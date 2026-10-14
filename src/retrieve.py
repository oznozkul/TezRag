"""Stage 2: precompute BM25 retrieval for every question (fills the cache).

    python -m src.retrieve [--dry-run] [--datasets nq musique ...]

Writes results/retrieval/retrieval.jsonl (qid, dataset, split, corpus, retrieved_ids, scores,
retrieval_ms, cached, answer_in_topk) and results/meta/retrieval_summary.json (per-dataset latency
stats and answer recall@k: share of questions where a gold answer, under the accuracy alias policy,
occurs in the title or text of a retrieved passage — a diagnostic, not a thesis metric).
Before timing, each corpus gets `latency.warmup` throwaway queries so JVM/JIT warm-up does not
land on the first real question.
"""
from __future__ import annotations

import argparse
import logging
import statistics
from collections import defaultdict

from tqdm import tqdm

from src.config import Config, load_config
from src.data import load_questions
from src.io_utils import setup_logging, write_json, write_jsonl
from src.metrics import accuracy_golds, contains
from src.retrieval import BM25Retriever

log = logging.getLogger("retrieve")

WARMUP_QUERIES = ["who wrote the book", "capital city of the country", "when was the film released",
                  "largest river in the world", "president of the united states"]


def warmup(retriever: BM25Retriever, corpus: str, n: int) -> None:
    for q in (WARMUP_QUERIES * (n // len(WARMUP_QUERIES) + 1))[:n]:
        retriever.search(q, corpus, with_passages=True, use_cache=False)


def pct(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, round(p * (len(xs) - 1)))]


def run(cfg: Config, dry_run: bool, datasets: list[str] | None) -> None:
    questions = load_questions(cfg, dry_run)
    if datasets:
        questions = [q for q in questions if q["dataset"] in datasets]
    retriever = BM25Retriever(cfg, cache_path=cfg.path("cache", dry_run) / "retrieval.sqlite")

    rows = []
    for corpus in sorted({cfg.retrieval.corpus_for[q["dataset"]] for q in questions}):
        warmup(retriever, corpus, cfg.latency.warmup)
        qs = [q for q in questions if cfg.retrieval.corpus_for[q["dataset"]] == corpus]
        for q in tqdm(qs, desc=corpus):
            r = retriever.search(q["question"], corpus, with_passages=True)
            golds = accuracy_golds(q["answers"], q["answers_primary"],
                                   cfg.eval.accuracy_min_alias_chars)
            hit = any(contains(f"{p['title']} {p['text']}", g) for p in r.passages for g in golds)
            rows.append({"qid": q["qid"], "dataset": q["dataset"], "split": q["split"],
                         "corpus": corpus, "retrieved_ids": r.ids, "scores": r.scores,
                         "retrieval_ms": round(r.retrieval_ms, 3), "cached": r.cached,
                         "answer_in_topk": hit})

    out = cfg.path("results", dry_run)
    write_jsonl(out / "retrieval" / "retrieval.jsonl", rows)
    by_ds = defaultdict(list)
    for r in rows:
        by_ds[r["dataset"]].append(r)
    summary = {}
    for ds, rs in by_ds.items():
        ms = [r["retrieval_ms"] for r in rs]
        summary[ds] = {"n": len(rs), "corpus": rs[0]["corpus"],
                       "mean_ms": round(statistics.mean(ms), 2), "p50_ms": round(pct(ms, .5), 2),
                       "p95_ms": round(pct(ms, .95), 2),
                       "short_results": sum(len(r["retrieved_ids"]) < cfg.retrieval.top_k for r in rs),
                       f"answer_recall@{cfg.retrieval.top_k}":
                           round(sum(r["answer_in_topk"] for r in rs) / len(rs), 3),
                       "from_cache": sum(r["cached"] for r in rs)}
    write_json(out / "meta" / "retrieval_summary.json", summary)
    for ds, s in summary.items():
        print(f"{ds:16s} {s}")
    print("note: these timings come from the batch precompute; P50/P95 for the thesis come from "
          "the sequential latency run (run_baselines --latency).")


def main() -> None:
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--datasets", nargs="*", default=None)
    args = ap.parse_args()
    run(load_config(args.config), args.dry_run, args.datasets)


if __name__ == "__main__":
    main()
