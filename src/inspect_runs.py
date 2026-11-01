"""Inspect raw run records: token/latency averages per system and example records.

    python -m src.inspect_runs --dry-run [--n 3]

Writes <results>/summary/inspection.md. Examples use the same n questions for every system
(chosen with random.Random(f"{seed}:examples") from questions present in all systems, from
different datasets where possible).
"""
from __future__ import annotations

import argparse
import random
import statistics
from collections import Counter

from src.config import load_config
from src.data import load_questions
from src.io_utils import read_jsonl, write_text
from src.metrics import score
from src.paths import out_path


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.mean(xs), 1) if xs else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--n", type=int, default=3)
    args = ap.parse_args()
    cfg = load_config(args.config)
    qs = {q["qid"]: q for q in load_questions(cfg, args.dry_run)}

    recs = {}
    for s in cfg.systems:
        p = out_path(cfg, s, args.dry_run, latency=False)
        rows = [r for r in read_jsonl(p) if r["error"] is None] if p.exists() else []
        recs[s] = {r["qid"]: r for r in rows}       # last successful record per qid

    lines = ["# Run inspection" + (" (dry run)" if args.dry_run else ""), "",
             "| system | calls ok | errors | mean input tok | mean output tok | mean reasoning tok | "
             "mean llm ms | accuracy |", "|---|---|---|---|---|---|---|---|"]
    for s, by_q in recs.items():
        p = out_path(cfg, s, args.dry_run, latency=False)
        n_err = sum(r["error"] is not None for r in read_jsonl(p)) if p.exists() else 0
        rs = list(by_q.values())
        acc = None
        if s != "llm_decision" and rs:
            acc = round(statistics.mean(
                score(r["prediction"], qs[r["qid"]]["answers"], qs[r["qid"]]["answers_primary"],
                      cfg.eval.accuracy_min_alias_chars)["accuracy"] for r in rs), 3)
        lines.append(f"| {s} | {len(rs)} | {n_err} | {_mean(r['input_tokens'] for r in rs)} | "
                     f"{_mean(r['output_tokens'] for r in rs)} | "
                     f"{_mean(r['reasoning_tokens'] for r in rs)} | {_mean(r['llm_ms'] for r in rs)} | "
                     f"{acc if acc is not None else '—'} |")

    if recs.get("llm_decision"):
        c = Counter(r["router_decision"] for r in recs["llm_decision"].values())
        lines += ["", f"llm_decision replies: yes={c['yes']}, no={c['no']}, invalid={c['invalid']}"]
        raw = Counter((r["prediction"] or "").strip() for r in recs["llm_decision"].values())
        lines.append("raw reply strings: " + ", ".join(f"`{k}`×{v}" for k, v in raw.most_common()))

    common = sorted(set.intersection(*(set(v) for v in recs.values()))) if recs else []
    rng = random.Random(f"{cfg.seed}:examples")
    rng.shuffle(common)
    picked, seen_ds = [], set()
    for qid in common:                      # prefer distinct datasets
        if qs[qid]["dataset"] not in seen_ds:
            picked.append(qid)
            seen_ds.add(qs[qid]["dataset"])
        if len(picked) == args.n:
            break

    for s, by_q in recs.items():
        lines += ["", f"## {s}"]
        for qid in picked:
            r, q = by_q[qid], qs[qid]
            sc = score(r["prediction"], q["answers"], q["answers_primary"],
                       cfg.eval.accuracy_min_alias_chars)
            lines += ["", f"### {qid} ({q['dataset']}, {q['split']})", "",
                      f"- prediction: `{r['prediction']!r}`"
                      + (f" → decision **{r['router_decision']}** → route {r['router_route']}"
                         if s == "llm_decision" else
                         f" — EM {sc['em']:.0f}, F1 {sc['f1']:.2f}, acc {sc['accuracy']:.0f}"),
                      f"- gold: {q['answers'][:6]}" + (" …" if len(q["answers"]) > 6 else ""),
                      f"- tokens: input {r['input_tokens']}, output {r['output_tokens']} "
                      f"(reasoning {r['reasoning_tokens']}), cached input {r['cached_input_tokens']}",
                      f"- ms: retrieval {r['retrieval_ms']} (cached={r['retrieval_cached']}), "
                      f"llm {r['llm_ms']}, total {r['total_ms']}",
                      f"- retrieved_ids: {r['retrieved_ids']}" if r["retrieved_ids"] else "- retrieved_ids: []",
                      f"- prompt_hash {r['prompt_hash']}, status {r['status']}, "
                      f"model {r['response_model']}",
                      "", "```text", r["prompt"], "```"]
    md = "\n".join(lines) + "\n"
    write_text(cfg.path("results", args.dry_run) / "summary" / "inspection.md", md)
    print(md)


if __name__ == "__main__":
    main()
