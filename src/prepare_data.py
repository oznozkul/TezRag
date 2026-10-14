"""Stage 1: sample questions and create the (write-once) train/dev/test split.

    python -m src.prepare_data            # writes data/processed + data/splits (fails if they exist)
    python -m src.prepare_data --dry-run  # dry_run_n per dataset -> runs/dryrun/, real split untouched

Procedure (all randomness from cfg.seed):
  1. Load each source pool; sort by source_id so file order does not matter.
  2. Drop questions with no answer that survives SQuAD normalization (unscorable, e.g. NQ "#"),
     and questions whose normalized text occurs more than once in the pool (PopQA has many
     template questions about different entities with the same surface form; their gold answers
     differ, and a duplicated text could land in train and test).
  3. Sample n_per_dataset with random.Random(f"{seed}:{dataset}") (independent of dataset order).
  4. Shuffle the sample with the same RNG and cut 60/20/20 within each dataset.
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import statistics
from collections import Counter
from datetime import datetime, timezone

from src.config import Config, load_config
from src.datasets.loaders import ALIAS_FILES, LOADERS
from src.io_utils import (WriteOnceError, setup_logging, sha256_file, write_json, write_jsonl,
                          write_once_json, write_once_jsonl, write_text)
from src.metrics import normalize_answer

log = logging.getLogger("prepare_data")

SPLITS = ("train", "dev", "test")


def split_sizes(n: int, ratios: dict[str, float]) -> dict[str, int]:
    n_train = round(n * ratios["train"])
    n_dev = round(n * ratios["dev"])
    return {"train": n_train, "dev": n_dev, "test": n - n_train - n_dev}


def drop_unscorable(pool: list[dict]) -> tuple[list[dict], int]:
    kept = [q for q in pool if q["answers"]]
    return kept, len(pool) - len(kept)


def drop_ambiguous(pool: list[dict]) -> tuple[list[dict], int]:
    counts = Counter(normalize_answer(q["question"]) for q in pool)
    kept = [q for q in pool if counts[normalize_answer(q["question"])] == 1]
    return kept, len(pool) - len(kept)


def sample_and_split(cfg: Config, dataset: str, pool: list[dict]) -> list[dict]:
    rng = random.Random(f"{cfg.seed}:{dataset}")
    pool = sorted(pool, key=lambda q: q["source_id"])
    n = cfg.data.n_per_dataset
    if n > len(pool):
        raise ValueError(f"{dataset}: requested {n} but pool has {len(pool)}")
    sample = rng.sample(pool, n)
    rng.shuffle(sample)
    sizes = split_sizes(n, cfg.data.split_ratios)
    out, i = [], 0
    for split in SPLITS:
        for q in sample[i:i + sizes[split]]:
            out.append({**q, "split": split})
        i += sizes[split]
    return out


def dry_run_subset(cfg: Config, rows: list[dict]) -> list[dict]:
    """First k questions of each split per dataset, k proportional to the split ratio."""
    sizes = split_sizes(cfg.data.dry_run_n, cfg.data.split_ratios)
    out = []
    for ds in cfg.data.datasets:
        for split in SPLITS:
            out += [r for r in rows if r["dataset"] == ds and r["split"] == split][:sizes[split]]
    return out


def check_no_leakage(rows: list[dict]) -> None:
    qid_split: dict[str, str] = {}
    text_split: dict[str, str] = {}
    for r in rows:
        if r["qid"] in qid_split:
            raise AssertionError(f"duplicate qid {r['qid']}")
        qid_split[r["qid"]] = r["split"]
        t = normalize_answer(r["question"])
        if t in text_split and text_split[t] != r["split"]:
            raise AssertionError(f"question text crosses splits: {r['question']!r}")
        text_split[t] = r["split"]


def build_summary(cfg: Config, rows: list[dict], pool_stats: dict) -> dict:
    per_ds = {}
    for ds in cfg.data.datasets:
        rs = [r for r in rows if r["dataset"] == ds]
        if not rs:
            continue
        per_ds[ds] = {
            "hop_type": rs[0]["hop_type"],
            **pool_stats[ds],
            "sampled": len(rs),
            "splits": {s: sum(r["split"] == s for r in rs) for s in SPLITS},
            "mean_question_words": round(statistics.mean(len(r["question"].split()) for r in rs), 2),
            "mean_answers_per_question": round(statistics.mean(len(r["answers"]) for r in rs), 2),
            "frac_multi_answer": round(sum(len(r["answers"]) > 1 for r in rs) / len(rs), 3),
        }
    totals = {s: sum(r["split"] == s for r in rows) for s in SPLITS}
    return {"per_dataset": per_ds, "total": {"questions": len(rows), "splits": totals}}


def short_alias_counts(cfg: Config, rows: list[dict]) -> dict:
    """Questions with at least one non-primary alias that accuracy ignores (normalized < min chars)."""
    k = cfg.eval.accuracy_min_alias_chars
    out = {}
    for ds in cfg.data.datasets:
        out[ds] = {}
        for split in SPLITS:
            rs = [r for r in rows if r["dataset"] == ds and r["split"] == split]
            out[ds][split] = sum(
                any(len(normalize_answer(a)) < k for a in r["answers"] if a not in r["answers_primary"])
                for r in rs)
        out[ds]["total"] = sum(out[ds][s] for s in SPLITS)
    return out


def summary_markdown(summary: dict, header: str) -> str:
    lines = [f"# {header}", "",
             "| dataset | hop | pool | unscorable dropped | ambiguous dropped | sampled | train | dev | "
             "test | words/q | answers/q | multi-answer |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for ds, s in summary["per_dataset"].items():
        sp = s["splits"]
        lines.append(f"| {ds} | {s['hop_type']} | {s['pool_size']} | {s['unscorable_dropped']} | {s['ambiguous_dropped']} | "
                     f"{s['sampled']} | {sp['train']} | {sp['dev']} | {sp['test']} | "
                     f"{s['mean_question_words']} | {s['mean_answers_per_question']} | "
                     f"{s['frac_multi_answer']:.1%} |")
    t = summary["total"]
    lines.append(f"| **total** | | | | | {t['questions']} | {t['splits']['train']} | "
                 f"{t['splits']['dev']} | {t['splits']['test']} | | | |")
    if "short_alias_questions" in summary:
        sa = summary["short_alias_questions"]
        lines += ["", f"Questions with an alias ignored by accuracy (normalized length < "
                      f"{summary['accuracy_min_alias_chars']}):", "",
                  "| dataset | train | dev | test | total |", "|---|---|---|---|---|"]
        for ds, c in sa.items():
            lines.append(f"| {ds} | {c['train']} | {c['dev']} | {c['test']} | {c['total']} |")
        lines.append(f"| **total** | {sum(c['train'] for c in sa.values())} | "
                     f"{sum(c['dev'] for c in sa.values())} | {sum(c['test'] for c in sa.values())} | "
                     f"{sum(c['total'] for c in sa.values())} |")
    return "\n".join(lines) + "\n"


def write_summary(cfg: Config, summary: dict, rows: list[dict], dry_run: bool) -> str:
    summary["accuracy_min_alias_chars"] = cfg.eval.accuracy_min_alias_chars
    summary["short_alias_questions"] = short_alias_counts(cfg, rows)
    processed = cfg.path("processed", dry_run)
    write_json(processed / "summary.json", summary)
    md = summary_markdown(summary, "Sample and split summary" + (" (dry run)" if dry_run else ""))
    write_text(processed / "summary.md", md)
    return md


def resummarize(cfg: Config, dry_run: bool) -> None:
    """Recompute summary files from the existing questions/split (write-once files untouched)."""
    from src.data import load_questions

    summary = json.loads((cfg.path("processed", dry_run) / "summary.json").read_text())
    print(write_summary(cfg, summary, load_questions(cfg, dry_run), dry_run))


def run(cfg: Config, dry_run: bool) -> None:
    processed, splits_dir = cfg.path("processed", dry_run), cfg.path("splits", dry_run)
    q_path, s_path, m_path = (processed / "questions.jsonl", splits_dir / "split.jsonl",
                              splits_dir / "manifest.json")
    if not dry_run:
        existing = [p for p in (q_path, s_path, m_path) if p.exists()]
        if existing:
            raise WriteOnceError(f"write-once outputs already exist: {existing}. "
                                 "Delete them by hand to regenerate the split.")

    raw = cfg.path("raw")
    rows, pool_stats = [], {}
    for ds in cfg.data.datasets:
        pool = LOADERS[ds](raw)
        kept, unscorable = drop_unscorable(pool)
        kept, ambiguous = drop_ambiguous(kept)
        pool_stats[ds] = {"pool_size": len(pool), "unscorable_dropped": unscorable,
                          "ambiguous_dropped": ambiguous}
        log.info("%s: pool %d, dropped %d unscorable, %d ambiguous", ds, len(pool), unscorable, ambiguous)
        rows += sample_and_split(cfg, ds, kept)

    check_no_leakage(rows)
    if dry_run:
        rows = dry_run_subset(cfg, rows)

    questions = [{k: v for k, v in r.items() if k != "split"} for r in rows]
    split_rows = [{"qid": r["qid"], "dataset": r["dataset"], "split": r["split"]} for r in rows]
    summary = build_summary(cfg, rows, pool_stats)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": cfg.seed,
        "config_hash": cfg.hash(),
        "n_per_dataset": cfg.data.n_per_dataset,
        "split_ratios": cfg.data.split_ratios,
        "dry_run": dry_run,
        "raw_sources_sha256": {f: sha256_file(raw / f)
                               for f in sorted({r["source_file"] for r in rows} | ALIAS_FILES)},
        "counts": summary["total"],
    }

    if dry_run:  # dry-run outputs are scratch and may be overwritten
        write_jsonl(q_path, questions)
        write_jsonl(s_path, split_rows)
        write_json(m_path, manifest)
    else:
        write_once_jsonl(q_path, questions)
        write_once_jsonl(s_path, split_rows)
        write_once_json(m_path, manifest)
    print(write_summary(cfg, summary, rows, dry_run))
    print(f"questions -> {q_path}\nsplit     -> {s_path}")


def main() -> None:
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resummarize", action="store_true",
                    help="only rebuild summary.{json,md} from the existing questions and split")
    args = ap.parse_args()
    cfg = load_config(args.config)
    if args.resummarize:
        resummarize(cfg, args.dry_run)
    else:
        run(cfg, args.dry_run)


if __name__ == "__main__":
    main()
