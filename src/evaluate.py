"""Stage 4: evaluation, outcome labels, oracle, llm_decision router, cost, latency, bootstrap.

    python -m src.evaluate [--dry-run]

Reads results/raw/*.jsonl and results/latency/*.jsonl; writes results/summary/:
  metrics.csv           system x dataset x split x answer_set: EM, F1, accuracy, tokens, cost, retrieval calls
  question_labels.jsonl per-question outcome labels and routes (input for future routers)
  labels.csv            label distribution per dataset x split
  decision.csv          llm_decision router: decisions, agreement with oracle, confusion
  breakeven.csv         decision cost vs. context tokens saved
  latency.csv           sequential latency per system incl. adaptive (decision + chosen path)
  bootstrap.csv         paired 95% CIs for system differences
  leakage.csv           reasoning leakage per system and criterion
  excluded_qids.csv     questions removed from all comparisons (prompt flagged twice)
  dispatch.csv          per question: sent to the model, call status, decision route, source attributes
  strata.csv            accuracy and cost by source attribute (hop, popularity, hops, type)
  model_compare.csv     paired accuracy and cost difference when a second model has a full run
  summary.md            readable report

Final record per (qid, system): the last successful call, else the last call. A failed call counts as a
wrong answer (scores 0) but its billed tokens still count as cost. A qid whose final record is `flagged`
in any system is removed from every system (comparisons use the common question set).
"""
from __future__ import annotations

import argparse
import logging

import pandas as pd

from src.config import Config, load_config
from src.cost import call_usd, retrieval_usd
from src.data import load_questions
from src.dispatch import discover_run_dirs, dispatch_rows, excluded_qids, load_run_dir, model_of
from src.io_utils import setup_logging, write_jsonl, write_text
from src.metrics import is_correct, score
from src.paths import out_path, results_root
from src.question_meta import load_meta
from src.records import final_records
from src.report import _dispatch_markdown, report
from src.routers import oracle_route, outcome_label
from src.strata import compare_table, stratum_markdown, stratum_table, with_meta
from src.tables import (aggregate, bootstrap_table, breakeven_table, decision_table, label_table,
                        latency_tables, leakage_table)

log = logging.getLogger("evaluate")

BASE = ("llm_only", "always_rag")
DERIVED = ("oracle", "llm_decision_router")
SYSTEMS = BASE + DERIVED


def load_runs(cfg: Config, dry_run: bool, latency: bool) -> tuple[dict, dict]:
    recs, calls = {}, {}
    for s in cfg.systems:
        p = out_path(cfg, s, dry_run, latency)
        recs[s], calls[s] = final_records(p) if p.exists() else ({}, {})
    return recs, calls


# --- per-question rows -----------------------------------------------------------------------

FULL_LIST_IN_ADAPTIVE_RAG = {"nq", "triviaqa", "popqa"}


def golds_for(cfg: Config, q: dict, answer_set: str) -> tuple[list, list | None, int]:
    """(golds, primary, min_alias_chars) for an answer set.

    all          every variant; accuracy ignores aliases shorter than accuracy_min_alias_chars
                 (the primary answer is always kept)
    adaptive_rag the gold set Adaptive-RAG/IRCoT score against, no alias filtering:
                 NQ/TriviaQA the full DPR answer list (process_{nq,trivia}.py store all answers as
                 spans); HotpotQA/2Wiki/MuSiQue the single IRCoT span; PopQA (not in Adaptive-RAG)
                 all possible_answers, as in its original evaluation
    """
    if answer_set == "adaptive_rag":
        if q["dataset"] in FULL_LIST_IN_ADAPTIVE_RAG:
            return q["answers"], None, 0
        return q["answers_primary"], None, 0
    return q["answers"], q["answers_primary"], cfg.eval.accuracy_min_alias_chars


def scored(cfg: Config, q: dict, rec: dict, answer_set: str) -> dict:
    golds, primary, k = golds_for(cfg, q, answer_set)
    if rec["error"] is not None:
        sc = {"em": 0.0, "f1": 0.0, "accuracy": 0.0}
    else:
        sc = score(rec["prediction"], golds, primary, k)
    sc["correct"] = is_correct(sc, cfg.eval.correct_metric, cfg.eval.f1_threshold)
    return sc


def path_row(cfg: Config, rec: dict, sc: dict, uses_retrieval: bool) -> dict:
    return {**{k: sc[k] for k in ("em", "f1", "accuracy", "correct")},
            "input_tokens": rec.get("input_tokens") or 0, "output_tokens": rec.get("output_tokens") or 0,
            "reasoning_tokens": rec.get("reasoning_tokens") or 0,
            "generation_usd": call_usd(cfg, rec), "retrieval_calls": int(uses_retrieval),
            "retrieval_usd": retrieval_usd(cfg, int(uses_retrieval)),
            "router_usd": 0.0, "router_input_tokens": 0, "router_output_tokens": 0,
            "router_reasoning_tokens": 0, "failed": rec["error"] is not None}


def build_rows(cfg: Config, questions: dict, recs: dict, answer_set: str) -> list[dict]:
    rows = []
    for qid, q in questions.items():
        lo, ar, dec = recs["llm_only"][qid], recs["always_rag"][qid], recs["llm_decision"][qid]
        lo_s, ar_s = scored(cfg, q, lo, answer_set), scored(cfg, q, ar, answer_set)
        paths = {"llm_only": path_row(cfg, lo, lo_s, False), "always_rag": path_row(cfg, ar, ar_s, True)}
        o_route = oracle_route(lo_s["correct"], ar_s["correct"])
        decision = dec["router_decision"] if dec["error"] is None else "invalid"
        d_route = "llm_only" if decision == "yes" else "always_rag"
        router = {"router_usd": call_usd(cfg, dec), "router_input_tokens": dec.get("input_tokens") or 0,
                  "router_output_tokens": dec.get("output_tokens") or 0,
                  "router_reasoning_tokens": dec.get("reasoning_tokens") or 0}
        meta = {"qid": qid, "dataset": q["dataset"], "split": q["split"], "answer_set": answer_set,
                "label": outcome_label(lo_s["correct"], ar_s["correct"]),
                "oracle_route": o_route, "decision": decision, "decision_route": d_route}
        for s, base in (("llm_only", paths["llm_only"]), ("always_rag", paths["always_rag"]),
                        ("oracle", paths[o_route]), ("llm_decision_router", {**paths[d_route], **router})):
            rows.append({**meta, "system": s, "route": {"oracle": o_route,
                         "llm_decision_router": d_route}.get(s, s), **base})
    for r in rows:
        r["total_usd"] = r["generation_usd"] + r["retrieval_usd"] + r["router_usd"]
    return rows


def run(cfg: Config, dry_run: bool) -> None:
    all_q = {q["qid"]: q for q in load_questions(cfg, dry_run)}
    recs, calls = load_runs(cfg, dry_run, latency=False)
    lat, _ = load_runs(cfg, dry_run, latency=True)

    missing = {s: [q for q in all_q if q not in recs[s]] for s in cfg.systems}
    if any(missing.values()):
        raise SystemExit(f"missing records: { {s: len(v) for s, v in missing.items()} }")
    excluded = excluded_qids(all_q, recs)
    questions = {q: v for q, v in all_q.items() if q not in excluded}
    shared = cfg.path("results", dry_run) / "summary"
    out = results_root(cfg, dry_run) / "summary"
    out.mkdir(parents=True, exist_ok=True)
    shared.mkdir(parents=True, exist_ok=True)

    excl_df = pd.DataFrame([{"qid": q, "dataset": all_q[q]["dataset"], "split": all_q[q]["split"],
                             "flagged_in": ",".join(v),
                             "calls": ";".join(f"{s}:{calls[s].get(q, 0)}" for s in v)}
                            for q, v in sorted(excluded.items())],
                           columns=["qid", "dataset", "split", "flagged_in", "calls"])
    excl_df.to_csv(out / "excluded_qids.csv", index=False)

    rows = []
    for aset in cfg.eval.answer_sets:
        rows += build_rows(cfg, questions, recs, aset)
    df = pd.DataFrame(rows)
    main_set = cfg.eval.answer_sets[0]
    write_jsonl(out / "question_labels.jsonl",
                df[(df.system == "llm_only")][["qid", "dataset", "split", "answer_set", "label", "oracle_route",
                                               "decision", "decision_route"]].to_dict("records"))

    metrics = aggregate(df)
    metrics.to_csv(out / "metrics.csv", index=False)
    labels = label_table(df)
    labels.to_csv(out / "labels.csv", index=False)
    decision = decision_table(df)
    decision.to_csv(out / "decision.csv", index=False)
    breakeven = breakeven_table(df[df.answer_set == main_set])
    breakeven.to_csv(out / "breakeven.csv", index=False)
    leakage = leakage_table(cfg, questions, recs)
    leakage.to_csv(out / "leakage.csv", index=False)
    boot = bootstrap_table(cfg, df)
    boot.to_csv(out / "bootstrap.csv", index=False)
    lat_tab, lat_diff, lat_info = (latency_tables(cfg, questions, lat, set(excluded))
                                   if all(lat[s] for s in cfg.systems) else (None, None, None))
    if lat_tab is not None:
        lat_tab.to_csv(out / "latency.csv", index=False)
        lat_diff.to_csv(out / "latency_diffs.csv", index=False)

    # retry statistics
    retry_rows = []
    for s in cfg.systems:
        multi = {q: n for q, n in calls[s].items() if n > 1}
        retry_rows.append({"system": s, "calls": sum(calls[s].values()), "qids_called_more_than_once": len(multi),
                           "recovered": sum(recs[s][q]["error"] is None for q in multi)})

    meta = load_meta(cfg)
    missing_meta = [q for q in all_q if q not in meta]
    if missing_meta:
        raise SystemExit(f"question_meta is missing {len(missing_meta)} questions")
    bundles = [(model_of(recs), recs, set(excluded), questions)]
    primary_dir = out_path(cfg, "llm_only", dry_run, False).parent.resolve()
    for directory in discover_run_dirs(cfg.path("results", dry_run)):
        if directory.resolve() == primary_dir:
            continue
        orecs, _ocalls = load_run_dir(directory)
        missing = [q for q in all_q if any(q not in orecs[s] for s in cfg.systems)]
        if missing:
            log.warning("skipping %s: %d questions have no record for every system", directory, len(missing))
            continue
        omodel = model_of(orecs)
        if omodel not in cfg.pricing:
            raise SystemExit(f"no price for {omodel}; add it under pricing in the config")
        oexcl = excluded_qids(all_q, orecs)
        okept = {q: v for q, v in all_q.items() if q not in oexcl}
        bundles.append((omodel, orecs, set(oexcl), okept))

    dispatch_list, frames, stratum_parts = [], {}, []
    for model, mrecs, mexcl, mkept in bundles:
        dispatch_list += dispatch_rows(all_q, mrecs, meta, model, mexcl)
        frame = with_meta(pd.DataFrame(build_rows(cfg, mkept, mrecs, main_set)), meta)
        frames[model] = frame
        stratum_parts.append(stratum_table(frame, model, cfg))
    dispatch_df = pd.DataFrame(dispatch_list)
    strata = pd.concat(stratum_parts, ignore_index=True) if stratum_parts else pd.DataFrame()
    compare = compare_table(frames, cfg)
    for folder in {out, shared}:
        dispatch_df.to_csv(folder / "dispatch.csv", index=False)
        strata.to_csv(folder / "strata.csv", index=False)
        if not compare.empty:
            compare.to_csv(folder / "model_compare.csv", index=False)

    extra = _dispatch_markdown(dispatch_df) + "\n" + stratum_markdown(strata, compare)
    write_text(out / "summary.md", report(cfg, dry_run, all_q, questions, excl_df, metrics, labels, decision,
                                          breakeven, leakage, boot, lat_tab, lat_diff, lat_info, retry_rows,
                                          df, main_set, extra))
    print((out / "summary.md").read_text())


def main() -> None:
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    run(load_config(args.config), args.dry_run)


if __name__ == "__main__":
    main()
