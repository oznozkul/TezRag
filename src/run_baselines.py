"""Stage 3: run llm_only / always_rag / llm_decision and log every call.

    python -m src.run_baselines --dry-run                       # 8 q/dataset, all systems
    python -m src.run_baselines --system llm_only --yes         # full run (paid; prints estimate first)
    python -m src.run_baselines --latency --yes                 # sequential latency run on the test subset

Records go to results/raw/<system>.jsonl (latency: results/latency/<system>.jsonl), one line per call,
appended and fsynced as they arrive; failed records are never removed.

Resume rule, per (qid, system, model, prompt_hash):
  - success, `incomplete`, `permanent` or `no_usage`  -> never called again
  - `transient_exhausted` (429/5xx/timeouts after all retries) -> called again on the next run
  - `flagged` (OpenAI prompt filter)  -> called again only with --retry-flagged, and only once
    (a key with two flagged records is final; evaluation then drops that qid for all systems)

Normal runs take retrieval from the cache built by `src.retrieve` (retrieval_ms is the originally
measured value, retrieval_cached=true) and run calls concurrently. The latency run is sequential
(concurrency 1): fresh retrieval (cache bypassed) immediately followed by the model call.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.config import Config, load_config
from src.data import load_questions
from src.io_utils import append_jsonl, read_jsonl, setup_logging, sha256_text
from src.llm import LLMClient, LLMResult, load_sent_params
from src.paths import out_path
from src.records import error_kind
from src.retrieval import BM25Retriever
from src.retrieve import warmup
from src.systems import SYSTEMS, USES_RETRIEVAL, build_prompt, parse_decision, route_for

log = logging.getLogger("run_baselines")

EST_OUTPUT_TOKENS = 80   # per call, for the pre-run cost estimate only


def prompt_hash(model: str, prompt: str, sent_params: dict) -> str:
    return sha256_text(json.dumps({"model": model, "prompt": prompt, "params": sent_params},
                                  sort_keys=True, ensure_ascii=False))[:16]


def open_client(cfg: Config, sent: dict, concurrency: int | None = None):
    if cfg.llm.provider == "gemini":
        from src.llm_gemini import GeminiClient
        return GeminiClient(cfg, sent, concurrency)
    if cfg.llm.provider == "ollama":
        from src.llm_ollama import OllamaClient
        return OllamaClient(cfg, sent, concurrency)
    if cfg.llm.provider == "anthropic":
        from src.llm_anthropic import AnthropicClient
        return AnthropicClient(cfg, sent, concurrency)
    return LLMClient(cfg, sent, concurrency)


FINAL_ERROR_KINDS = {"incomplete", "permanent", "no_usage"}
MAX_FLAGGED_ATTEMPTS = 2   # first call + one --retry-flagged


def done_keys(path: Path, retry_flagged: bool = False) -> set[tuple]:
    """Keys that must not be called again under the resume rule above."""
    if not path.exists():
        return set()
    done, flagged = set(), Counter()
    for r in read_jsonl(path):
        key = (r["qid"], r["system"], r["model"], r["prompt_hash"])
        kind = error_kind(r)
        if kind is None or kind in FINAL_ERROR_KINDS:
            done.add(key)
        elif kind == "flagged":
            flagged[key] += 1
    for key, n in flagged.items():
        if not retry_flagged or n >= MAX_FLAGGED_ATTEMPTS:
            done.add(key)
    return done


def latency_subset(cfg: Config, questions: list[dict], dry_run: bool) -> list[dict]:
    pool = sorted((q for q in questions if q["split"] == cfg.latency.split), key=lambda q: q["qid"])
    n = min(len(pool), cfg.latency.n if not dry_run else len(pool))
    return random.Random(f"{cfg.seed}:latency").sample(pool, n)


def make_record(cfg: Config, q: dict, system: str, prompt: str, phash: str, sent: dict,
                dropped: dict, retrieval, res: LLMResult, run_id: str, mode: str) -> dict:
    retrieval_ms = retrieval.retrieval_ms if retrieval else 0.0
    rec = {
        "qid": q["qid"], "dataset": q["dataset"], "split": q["split"], "system": system,
        "model": cfg.llm.model, "prompt_hash": phash,
        "input_tokens": res.input_tokens, "output_tokens": res.output_tokens,
        "reasoning_tokens": res.reasoning_tokens, "cached_input_tokens": res.cached_input_tokens,
        "retrieval_ms": round(retrieval_ms, 3),
        "llm_ms": round(res.llm_ms, 3) if res.llm_ms is not None else None,
        "total_ms": round(retrieval_ms + res.llm_ms, 3) if res.llm_ms is not None else None,
        "retrieved_ids": retrieval.ids if retrieval else [],
        "retrieved_scores": retrieval.scores if retrieval else [],
        "retrieval_cached": retrieval.cached if retrieval else None,
        "prediction": res.text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error": res.error, "error_kind": res.error_kind,
        # provenance
        "run_id": run_id, "mode": mode, "config_hash": cfg.hash(),
        "response_model": res.response_model, "response_id": res.response_id, "status": res.status,
        "attempts": res.attempts, "request_params": sent, "dropped_params": dropped,
        "prompt": prompt,
        # router fields (only llm_decision fills them for now; learned routers later)
        "router_name": None, "router_decision": None, "router_route": None,
        "router_ms": None, "router_input_tokens": None, "router_output_tokens": None,
    }
    if system == "llm_decision":
        decision = parse_decision(res.text) if res.error is None else None
        rec.update({"router_name": "llm_decision", "router_decision": decision,
                    "router_route": route_for(decision) if decision else None,
                    "router_ms": rec["llm_ms"], "router_input_tokens": res.input_tokens,
                    "router_output_tokens": res.output_tokens})
    return rec


def estimate_cost(cfg: Config, prompts: list[str]) -> float:
    price = cfg.pricing[cfg.llm.model]
    inp = sum(len(p) / 4 for p in prompts)
    out = EST_OUTPUT_TOKENS * len(prompts)
    return inp / 1e6 * price["input_per_1m"] + out / 1e6 * price["output_per_1m"]


async def run_system(cfg: Config, system: str, questions: list[dict], *, dry_run: bool,
                     latency: bool, retriever: BM25Retriever | None, sent: dict, dropped: dict,
                     run_id: str, yes: bool, retry_flagged: bool = False) -> None:
    path = out_path(cfg, system, dry_run, latency)
    path.parent.mkdir(parents=True, exist_ok=True)
    done = done_keys(path, retry_flagged)
    mode = "latency" if latency else ("dry_run" if dry_run else "full")
    if retry_flagged:
        mode += "_retry_flagged"

    if latency:
        if USES_RETRIEVAL[system]:
            for corpus in sorted({cfg.retrieval.corpus_for[q["dataset"]] for q in questions}):
                warmup(retriever, corpus, cfg.latency.warmup)
        client = open_client(cfg, sent, concurrency=cfg.latency.concurrency)
        # prompt hash needs the passages, so pending is decided per question, sequentially
        n_new = 0
        try:
            with open(path, "a") as f:
                for q in questions:
                    r = (retriever.search(q["question"], cfg.retrieval.corpus_for[q["dataset"]],
                                          use_cache=False) if USES_RETRIEVAL[system] else None)
                    prompt = build_prompt(cfg, system, q["question"], r.passages if r else None)
                    ph = prompt_hash(cfg.llm.model, prompt, sent)
                    if (q["qid"], system, cfg.llm.model, ph) in done:
                        continue
                    res = await client.complete(prompt)
                    append_jsonl(f, make_record(cfg, q, system, prompt, ph, sent, dropped, r, res,
                                                run_id, mode))
                    n_new += 1
        finally:
            await client.aclose()
        log.info("%s latency: %d new calls -> %s", system, n_new, path)
        return

    pending = []
    for q in questions:
        r = (retriever.search(q["question"], cfg.retrieval.corpus_for[q["dataset"]])
             if USES_RETRIEVAL[system] else None)
        prompt = build_prompt(cfg, system, q["question"], r.passages if r else None)
        ph = prompt_hash(cfg.llm.model, prompt, sent)
        if (q["qid"], system, cfg.llm.model, ph) not in done:
            pending.append((q, r, prompt, ph))
    est = estimate_cost(cfg, [p for _, _, p, _ in pending])
    print(f"{system}: {len(questions) - len(pending)} done, {len(pending)} to call, "
          f"estimated cost ${est:.3f}")
    if not pending:
        return
    if not dry_run and not yes:
        raise SystemExit("paid full run: re-run with --yes after checking the estimate")

    client = open_client(cfg, sent)
    with open(path, "a") as f:
        async def one(item):
            q, r, prompt, ph = item
            res = await client.complete(prompt)
            append_jsonl(f, make_record(cfg, q, system, prompt, ph, sent, dropped, r, res,
                                        run_id, mode))
            return res

        try:
            results = await asyncio.gather(*(one(it) for it in pending))
        finally:
            await client.aclose()
    errors = sum(r.error is not None for r in results)
    log.info("%s: %d calls, %d errors -> %s", system, len(results), errors, path)


def main() -> None:
    setup_logging()
    logging.getLogger("httpx").setLevel(logging.WARNING)
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--system", nargs="+", choices=SYSTEMS, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--latency", action="store_true")
    ap.add_argument("--yes", action="store_true", help="confirm a paid full/latency run")
    ap.add_argument("--retry-flagged", action="store_true",
                    help="call again (once) the prompts rejected by OpenAI's prompt filter")
    args = ap.parse_args()

    cfg = load_config(args.config)
    systems = args.system or cfg.systems
    questions = load_questions(cfg, args.dry_run)
    if args.latency:
        if not args.dry_run and not args.yes:
            raise SystemExit("paid latency run: re-run with --yes")
        questions = latency_subset(cfg, questions, args.dry_run)
    sent, dropped = load_sent_params(cfg)
    retriever = None
    if any(USES_RETRIEVAL[s] for s in systems):
        retriever = BM25Retriever(cfg, cache_path=cfg.path("cache", args.dry_run) / "retrieval.sqlite")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    log.info("run %s: systems=%s questions=%d sent=%s dropped=%s", run_id, systems,
             len(questions), sent, list(dropped))

    async def run_all():
        for s in systems:
            await run_system(cfg, s, questions, dry_run=args.dry_run, latency=args.latency,
                             retriever=retriever, sent=sent, dropped=dropped, run_id=run_id,
                             yes=args.yes, retry_flagged=args.retry_flagged)

    asyncio.run(run_all())


if __name__ == "__main__":
    main()

