"""Repeat llm_only / always_rag on one split to measure how stable the outcome labels are.

    python -m src.repeat_runs --estimate               # pending calls and cost; no calls
    python -m src.repeat_runs --dry-run                # all dry-run questions (paid, a fraction of a cent)
    python -m src.repeat_runs --yes                    # test split, 2 repeats (paid)
    python -m src.repeat_runs --config configs/deepseek.yaml --yes   # another model

Each repeat sends exactly the prompt of the original final record: the same question and, for
always_rag, the same cached BM25 passages. Every record stores `same_prompt_as_original`; a mismatch
stops the run before any call. So a different outcome comes from the model's own sampling (the API
rejected temperature and seed), not from retrieval.

Logs: <results root>/repeats/rep<k>/<system>.jsonl (OpenAI: results/repeats/...), append-only and
resumable like the main runs. results/raw is only read.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.config import Config, load_config
from src.data import load_questions
from src.io_utils import append_jsonl, setup_logging
from src.llm import load_sent_params
from src.paths import out_path, results_root
from src.records import final_records
from src.retrieval import BM25Retriever
from src.run_baselines import done_keys, estimate_cost, make_record, open_client, prompt_hash
from src.systems import USES_RETRIEVAL, build_prompt

log = logging.getLogger("repeat_runs")
SYSTEMS = ("llm_only", "always_rag")


def repeat_path(cfg: Config, dry_run: bool, k: int, system: str) -> Path:
    return results_root(cfg, dry_run) / "repeats" / f"rep{k}" / f"{system}.jsonl"


def pending(cfg: Config, dry_run: bool, split: str, repeats: int, sent: dict,
            retriever: BM25Retriever | None) -> list[dict]:
    questions = [q for q in load_questions(cfg, dry_run) if split == "all" or q["split"] == split]
    items = []
    done = {}
    for system in SYSTEMS:
        orig, _ = final_records(out_path(cfg, system, dry_run, False))
        for q in questions:
            o = orig.get(q["qid"])
            if o is None:
                raise SystemExit(f"{q['qid']}: no original {system} record")
            r = (retriever.search(q["question"], cfg.retrieval.corpus_for[q["dataset"]])
                 if USES_RETRIEVAL[system] else None)
            prompt = build_prompt(cfg, system, q["question"], r.passages if r else None)
            same = prompt == o.get("prompt")
            if not same:
                raise SystemExit(f"{q['qid']} {system}: rebuilt prompt differs from the original; "
                                 "retrieval cache or prompt template changed")
            ph = prompt_hash(cfg.llm.model, prompt, sent)
            for k in range(1, repeats + 1):
                path = repeat_path(cfg, dry_run, k, system)
                if path not in done:
                    done[path] = done_keys(path)
                if (q["qid"], system, cfg.llm.model, ph) in done[path]:
                    continue
                items.append({"q": q, "system": system, "k": k, "prompt": prompt, "ph": ph,
                              "retrieval": r, "path": path})
    return items


async def call_all(cfg: Config, items: list[dict], sent: dict, dropped: dict, mode: str) -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    client = open_client(cfg, sent)
    handles = {}
    try:
        for p in sorted({str(it["path"]) for it in items}):
            Path(p).parent.mkdir(parents=True, exist_ok=True)
            handles[p] = open(p, "a")

        async def one(it):
            res = await client.complete(it["prompt"])
            rec = make_record(cfg, it["q"], it["system"], it["prompt"], it["ph"], sent, dropped,
                              it["retrieval"], res, run_id, f"{mode}_rep{it['k']}")
            rec["repeat"] = it["k"]
            rec["same_prompt_as_original"] = True
            append_jsonl(handles[str(it["path"])], rec)
            return res

        results = await asyncio.gather(*(one(it) for it in items))
    finally:
        await client.aclose()
        for f in handles.values():
            f.close()
    log.info("%d calls, %d errors", len(results), sum(r.error is not None for r in results))


def main() -> None:
    setup_logging()
    logging.getLogger("httpx").setLevel(logging.WARNING)
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--split", default="test")
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--estimate", action="store_true")
    ap.add_argument("--yes", action="store_true")
    args = ap.parse_args()
    cfg = load_config(args.config)
    sent, dropped = load_sent_params(cfg)
    retriever = BM25Retriever(cfg, cache_path=cfg.path("cache", args.dry_run) / "retrieval.sqlite")
    items = pending(cfg, args.dry_run, "all" if args.dry_run else args.split,
                    args.repeats, sent, retriever)
    by = {}
    for it in items:
        by[(it["system"], it["k"])] = by.get((it["system"], it["k"]), 0) + 1
    for (s, k), n in sorted(by.items()):
        print(f"  {cfg.llm.model:28s} {s:11s} rep{k} {n:5d} to call")
    print(f"{cfg.llm.model}: {len(items)} calls pending, estimated cost "
          f"${estimate_cost(cfg, [it['prompt'] for it in items]):.3f}")
    if args.estimate or not items:
        return
    if not args.dry_run and not args.yes:
        raise SystemExit("paid run: re-run with --yes after checking the estimate")
    asyncio.run(call_all(cfg, items, sent, dropped, "dry_run" if args.dry_run else "full"))


if __name__ == "__main__":
    main()
