"""LLM judge: a second correctness criterion next to token-bounded accuracy.

    python -m src.judge --estimate [--dry-run]   # count pending calls and estimate cost; no calls
    python -m src.judge --dry-run                # judge the dry-run logs (paid, a few cents at most)
    python -m src.judge --yes                    # judge every full run (paid)

For every model with logs and every system in `judge.systems` (llm_only, always_rag), the judge model
reads the question, the gold answers, and the final logged prediction, and replies CORRECT or
INCORRECT (prompts/judge.txt). A failed answer call is not judged: it stays wrong, as in evaluate.

Logs: results/judge/<judge model>/<answer model>/<system>.jsonl (dry run: runs/dryrun/results/...).
Append-only and resumable: a key (qid, system, answer model, judge model, prompt hash) with a final
record is never called again. Raw answer logs are only read.

The judge sees the gold answers, so its verdict is a grading decision, not the judge's own knowledge.
It is validated against a hand-labelled sample (src/annotation.py) before its numbers are used.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.config import PROJECT_ROOT, Config, load_config
from src.data import load_questions
from src.dispatch import discover_run_dirs, load_run_dir, model_of
from src.io_utils import append_jsonl, read_jsonl, setup_logging
from src.llm import LLMClient, LLMResult, load_sent_params
from src.run_baselines import FINAL_ERROR_KINDS, prompt_hash
from src.records import error_kind

log = logging.getLogger("judge")

EST_OUTPUT_TOKENS = 20     # per call, for the estimate only (minimal reasoning, one word)
VERDICTS = ("correct", "incorrect")
_VERDICT_RE = re.compile(r"\b(INCORRECT|CORRECT)\b", re.IGNORECASE)


def judge_cfg(cfg: Config):
    if cfg.judge is None:
        raise SystemExit("no `judge:` section in the config")
    return cfg.judge


def gold_list(q: dict, max_golds: int) -> list[str]:
    """Primary answers first, then the other variants, without duplicates."""
    out = []
    for g in list(q.get("answers_primary") or []) + list(q["answers"]):
        if g and g not in out:
            out.append(g)
    return out[:max_golds]


def build_judge_prompt(cfg: Config, q: dict, prediction: str) -> str:
    j = judge_cfg(cfg)
    template = (PROJECT_ROOT / j.prompt).read_text()
    golds = " | ".join(gold_list(q, j.max_golds))
    return template.format(question=q["question"], golds=golds, prediction=(prediction or "").strip())


def parse_verdict(text: str | None) -> str:
    """'correct' | 'incorrect' | 'invalid'. INCORRECT wins if the reply contains both words."""
    if not text:
        return "invalid"
    found = {m.upper() for m in _VERDICT_RE.findall(text)}
    if "INCORRECT" in found:
        return "incorrect"
    if "CORRECT" in found:
        return "correct"
    return "invalid"


def judge_root(cfg: Config, dry_run: bool) -> Path:
    return cfg.path("results", dry_run) / "judge" / judge_cfg(cfg).model


def judge_path(cfg: Config, dry_run: bool, answer_model: str, system: str) -> Path:
    return judge_root(cfg, dry_run) / answer_model / f"{system}.jsonl"


def done_keys(path: Path) -> set[tuple]:
    if not path.exists():
        return set()
    done = set()
    for r in read_jsonl(path):
        kind = r.get("error_kind")
        if r.get("error") is None or kind in FINAL_ERROR_KINDS or kind == "flagged":
            done.add((r["qid"], r["system"], r["answer_model"], r["judge_model"], r["prompt_hash"]))
    return done


def pending_items(cfg: Config, dry_run: bool, sent: dict) -> list[dict]:
    """Every (answer model, system, qid) whose final answer succeeded and has no final verdict."""
    j = judge_cfg(cfg)
    questions = {q["qid"]: q for q in load_questions(cfg, dry_run)}
    items = []
    for directory in discover_run_dirs(cfg.path("results", dry_run)):
        recs, _ = load_run_dir(directory)
        model = model_of(recs)
        if model is None or any(qid not in recs[s] for s in recs for qid in questions):
            log.warning("skipping %s: not every question has a record for every system", directory)
            continue
        for system in j.systems:
            path = judge_path(cfg, dry_run, model, system)
            done = done_keys(path)
            for qid, rec in sorted(recs[system].items()):
                if qid not in questions or error_kind(rec) is not None:
                    continue
                prompt = build_judge_prompt(cfg, questions[qid], rec["prediction"])
                ph = prompt_hash(j.model, prompt, sent)
                if (qid, system, model, j.model, ph) in done:
                    continue
                items.append({"q": questions[qid], "system": system, "answer_model": model,
                              "prediction": rec["prediction"], "prompt": prompt, "prompt_hash": ph,
                              "path": path})
    return items


def estimate_usd(cfg: Config, prompts: list[str]) -> float:
    p = cfg.pricing[judge_cfg(cfg).model]
    inp = sum(len(x) / 4 for x in prompts)
    return (inp * p["input_per_1m"] + EST_OUTPUT_TOKENS * len(prompts) * p["output_per_1m"]) / 1e6


def make_record(cfg: Config, item: dict, res: LLMResult, sent: dict, run_id: str, mode: str) -> dict:
    q = item["q"]
    return {
        "qid": q["qid"], "dataset": q["dataset"], "split": q["split"], "system": item["system"],
        "answer_model": item["answer_model"], "judge_model": judge_cfg(cfg).model,
        "prompt_hash": item["prompt_hash"], "prediction": item["prediction"],
        "verdict": parse_verdict(res.text) if res.error is None else None, "judge_text": res.text,
        "input_tokens": res.input_tokens, "output_tokens": res.output_tokens,
        "reasoning_tokens": res.reasoning_tokens, "cached_input_tokens": res.cached_input_tokens,
        "llm_ms": res.llm_ms, "error": res.error, "error_kind": res.error_kind,
        "attempts": res.attempts, "request_params": sent, "run_id": run_id, "mode": mode,
        "config_hash": cfg.hash(), "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt": item["prompt"],
    }


def load_verdicts(cfg: Config, dry_run: bool) -> dict[tuple[str, str, str], str]:
    """(answer model, system, qid) -> final verdict ('correct' | 'incorrect' | 'invalid').

    Last successful record per key wins. Missing keys mean not judged yet."""
    out: dict[tuple[str, str, str], str] = {}
    root = judge_root(cfg, dry_run) if cfg.judge else None
    if root is None or not root.exists():
        return out
    for path in sorted(root.glob("*/*.jsonl")):
        for r in read_jsonl(path):
            if r.get("error") is None and r.get("verdict"):
                out[(r["answer_model"], r["system"], r["qid"])] = r["verdict"]
    return out


async def run(cfg: Config, items: list[dict], sent: dict, mode: str) -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    jcfg = cfg.model_copy(update={"llm": cfg.llm.model_copy(update={"model": judge_cfg(cfg).model})})
    client = LLMClient(jcfg, sent)
    handles = {}
    try:
        for p in sorted({str(it["path"]) for it in items}):
            Path(p).parent.mkdir(parents=True, exist_ok=True)
            handles[p] = open(p, "a")

        async def one(item):
            res = await client.complete(item["prompt"])
            append_jsonl(handles[str(item["path"])], make_record(cfg, item, res, sent, run_id, mode))
            return res

        results = await asyncio.gather(*(one(it) for it in items))
    finally:
        await client.aclose()
        for f in handles.values():
            f.close()
    errors = sum(r.error is not None for r in results)
    invalid = sum(r.error is None and parse_verdict(r.text) == "invalid" for r in results)
    log.info("judge: %d calls, %d errors, %d invalid replies", len(results), errors, invalid)


def main() -> None:
    setup_logging()
    logging.getLogger("httpx").setLevel(logging.WARNING)
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--estimate", action="store_true", help="count pending calls and cost; no calls")
    ap.add_argument("--yes", action="store_true", help="confirm a paid full run")
    args = ap.parse_args()

    cfg = load_config(args.config)
    j = judge_cfg(cfg)
    if j.model != cfg.llm.model or cfg.llm.provider != "openai":
        raise SystemExit("the judge reuses the OpenAI parameter probe of the default model; "
                         "set judge.model to llm.model or probe the judge model first")
    sent, _dropped = load_sent_params(cfg)
    items = pending_items(cfg, args.dry_run, sent)
    by = {}
    for it in items:
        by[(it["answer_model"], it["system"])] = by.get((it["answer_model"], it["system"]), 0) + 1
    for (m, s), n in sorted(by.items()):
        print(f"  {m:28s} {s:11s} {n:5d} to judge")
    est = estimate_usd(cfg, [it["prompt"] for it in items])
    print(f"judge {j.model}: {len(items)} calls pending, estimated cost ${est:.3f}")
    if args.estimate or not items:
        return
    if not args.dry_run and not args.yes:
        raise SystemExit("paid full run: re-run with --yes after checking the estimate")
    asyncio.run(run(cfg, items, sent, "dry_run" if args.dry_run else "full"))


if __name__ == "__main__":
    main()
