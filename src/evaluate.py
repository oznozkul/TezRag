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
  summary.md            readable report

Final record per (qid, system): the last successful call, else the last call. A failed call counts as a
wrong answer (scores 0) but its billed tokens still count as cost. A qid whose final record is `flagged`
in any system is removed from every system (comparisons use the common question set).
"""
from __future__ import annotations

import argparse
import logging
from collections import defaultdict

import numpy as np
import pandas as pd

from src.bootstrap import paired_mean_diff, paired_stat_diff
from src.config import Config, load_config
from src.cost import call_usd, retrieval_usd
from src.data import load_questions
from src.io_utils import read_jsonl, setup_logging, write_jsonl, write_text
from src.leakage import leak_flags
from src.metrics import is_correct, score
from src.routers import oracle_route, outcome_label
from src.run_baselines import error_kind, out_path

log = logging.getLogger("evaluate")

BASE = ("llm_only", "always_rag")
DERIVED = ("oracle", "llm_decision_router")
SYSTEMS = BASE + DERIVED
LABELS = ("both_ok", "rag_hurts", "retrieval_needed", "both_fail")


# --- loading ---------------------------------------------------------------------------------

def final_records(path) -> tuple[dict, dict]:
    """qid -> final record, qid -> number of calls."""
    by_q = defaultdict(list)
    for r in read_jsonl(path):
        by_q[r["qid"]].append(r)
    final = {}
    for qid, rs in by_q.items():
        ok = [r for r in rs if r["error"] is None]
        final[qid] = ok[-1] if ok else rs[-1]
    return final, {q: len(v) for q, v in by_q.items()}


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


# --- aggregation -----------------------------------------------------------------------------

def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for split in ["all", "train", "dev", "test"]:
        d1 = df if split == "all" else df[df.split == split]
        for ds in sorted(d1.dataset.unique()) + ["ALL"]:
            d2 = d1 if ds == "ALL" else d1[d1.dataset == ds]
            for (aset, sysname), g in d2.groupby(["answer_set", "system"]):
                out.append({
                    "answer_set": aset, "split": split, "dataset": ds, "system": sysname, "n": len(g),
                    "em": g.em.mean(), "f1": g.f1.mean(), "accuracy": g.accuracy.mean(),
                    "correct": g.correct.mean(),
                    "mean_input_tokens": (g.input_tokens + g.router_input_tokens).mean(),
                    "mean_output_tokens": (g.output_tokens + g.router_output_tokens).mean(),
                    "mean_reasoning_tokens": (g.reasoning_tokens + g.router_reasoning_tokens).mean(),
                    "usd_per_q": g.total_usd.mean(), "generation_usd_per_q": g.generation_usd.mean(),
                    "router_usd_per_q": g.router_usd.mean(), "retrieval_usd_per_q": g.retrieval_usd.mean(),
                    "retrieval_calls": int(g.retrieval_calls.sum()),
                    "retrieval_rate": g.retrieval_calls.mean(), "failed_calls": int(g.failed.sum())})
    return pd.DataFrame(out)


def label_table(df: pd.DataFrame) -> pd.DataFrame:
    base = df[df.system == "llm_only"]
    out = []
    for split in ["all", "train", "dev", "test"]:
        d1 = base if split == "all" else base[base.split == split]
        for ds in sorted(d1.dataset.unique()) + ["ALL"]:
            d2 = d1 if ds == "ALL" else d1[d1.dataset == ds]
            for aset, g in d2.groupby("answer_set"):
                c = g.label.value_counts()
                row = {"answer_set": aset, "split": split, "dataset": ds, "n": len(g)}
                for lab in LABELS:
                    row[lab] = int(c.get(lab, 0))
                row["no_retrieval_ok"] = row["both_ok"] + row["rag_hurts"]
                out.append(row)
    return pd.DataFrame(out)


def decision_table(df: pd.DataFrame) -> pd.DataFrame:
    d = df[(df.system == "llm_decision_router")]
    out = []
    for ds in sorted(d.dataset.unique()) + ["ALL"]:
        for aset, g in (d if ds == "ALL" else d[d.dataset == ds]).groupby("answer_set"):
            lo_ok = g.label.isin(["both_ok", "rag_hurts"])
            decisive = g.label.isin(["rag_hurts", "retrieval_needed"])   # only here does the route matter
            dec_yes = g.decision == "yes"
            orc_lo = g.oracle_route == "llm_only"
            out.append({
                "answer_set": aset, "dataset": ds, "n": len(g),
                "yes": int((g.decision == "yes").sum()), "no": int((g.decision == "no").sum()),
                "invalid": int((g.decision == "invalid").sum()),
                "agree_with_oracle": float((g.decision_route == g.oracle_route).mean()),
                "n_decisive": int(decisive.sum()),
                "agree_on_decisive": float((g.decision_route == g.oracle_route)[decisive].mean())
                if decisive.any() else float("nan"),
                "yes_and_oracle_llm_only": int((dec_yes & orc_lo).sum()),
                "yes_but_oracle_rag": int((dec_yes & ~orc_lo).sum()),
                "no_but_oracle_llm_only": int((~dec_yes & orc_lo).sum()),
                "no_and_oracle_rag": int((~dec_yes & ~orc_lo).sum()),
                "self_knowledge_acc": float((dec_yes == lo_ok).mean()),
                "yes_precision": float(lo_ok[dec_yes].mean()) if dec_yes.any() else float("nan"),
                "llm_only_correct_rate": float(lo_ok.mean())})
    return pd.DataFrame(out)


def breakeven_table(df: pd.DataFrame) -> pd.DataFrame:
    """Decision cost vs. what skipping retrieval saves (context tokens and money). df: one answer set."""
    lo = df[df.system == "llm_only"].set_index("qid")
    ar = df[df.system == "always_rag"].set_index("qid")
    dr = df[df.system == "llm_decision_router"].set_index("qid")
    out = []
    for ds in sorted(df.dataset.unique()) + ["ALL"]:
        idx = dr.index if ds == "ALL" else dr.index[dr.dataset == ds]
        sub_dr, sub_lo, sub_ar = dr.loc[idx], lo.loc[idx], ar.loc[idx]
        skipped = sub_dr.decision == "yes"
        saving = sub_ar.generation_usd + sub_ar.retrieval_usd - sub_lo.generation_usd
        saved_ctx = (sub_ar.input_tokens - sub_lo.input_tokens)[skipped].sum()
        saved_usd = saving[skipped].sum()
        dec_usd = sub_dr.router_usd.sum()
        dec_tok = sub_dr.router_input_tokens.sum() + sub_dr.router_output_tokens.sum()
        out.append({
            "dataset": ds, "n": len(idx), "skipped_retrievals": int(skipped.sum()),
            "decision_usd_total": dec_usd, "saved_usd_total": float(saved_usd),
            "cost_to_saving_ratio_usd": dec_usd / saved_usd if saved_usd else float("inf"),
            "decision_tokens_total": int(dec_tok),
            "decision_input_tokens_total": int(sub_dr.router_input_tokens.sum()),
            "decision_output_tokens_total": int(sub_dr.router_output_tokens.sum()),
            "saved_context_tokens_total": int(saved_ctx),
            "token_ratio_decision_to_saved_context": dec_tok / saved_ctx if saved_ctx else float("inf"),
            "decision_usd_per_q": dec_usd / len(idx),
            "mean_saving_usd_if_skipped": float(saving.mean()),
            "breakeven_skip_rate": (dec_usd / len(idx)) / float(saving.mean()),
            "actual_skip_rate": float(skipped.mean())})
    return pd.DataFrame(out)


def leakage_table(cfg: Config, questions: dict, recs: dict) -> pd.DataFrame:
    out = []
    for s in cfg.systems:
        flags = [leak_flags(recs[s][q]) | {"dataset": questions[q]["dataset"]} for q in questions]
        f = pd.DataFrame(flags)
        for ds in sorted(f.dataset.unique()) + ["ALL"]:
            g = f if ds == "ALL" else f[f.dataset == ds]
            out.append({"system": s, "dataset": ds, "n": len(g), "leak": int(g.leak.sum()),
                        "leak_rate": float(g.leak.mean()), "incomplete": int(g.incomplete.sum()),
                        "long": int(g.long.sum()), "marker": int(g.marker.sum())})
    return pd.DataFrame(out)


def pct(xs, p):
    return float(np.percentile(xs, p)) if len(xs) else float("nan")


def latency_tables(cfg: Config, questions: dict, lat: dict, excluded: set) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    qids = [q for q in lat["llm_only"] if q in lat["always_rag"] and q in lat["llm_decision"]
            and q in questions and q not in excluded]
    bad = [q for q in qids if any(lat[s][q]["error"] is not None for s in cfg.systems)]
    qids = sorted(set(qids) - set(bad))
    lo = np.array([lat["llm_only"][q]["total_ms"] for q in qids])
    ar = np.array([lat["always_rag"][q]["total_ms"] for q in qids])
    dec = np.array([lat["llm_decision"][q]["total_ms"] for q in qids])
    route = [lat["llm_decision"][q]["router_route"] for q in qids]
    adaptive = dec + np.where(np.array(route) == "llm_only", lo, ar)
    ar_retr = np.array([lat["always_rag"][q]["retrieval_ms"] for q in qids])
    series = {"llm_only": lo, "always_rag": ar, "llm_decision_call_only": dec,
              "adaptive_llm_decision (decision + chosen path)": adaptive}
    rows = [{"system": k, "n": len(v), "mean_ms": float(v.mean()), "p50_ms": pct(v, 50),
             "p95_ms": pct(v, 95)} for k, v in series.items()]
    rows.append({"system": "always_rag: retrieval part only", "n": len(ar_retr),
                 "mean_ms": float(ar_retr.mean()), "p50_ms": pct(ar_retr, 50), "p95_ms": pct(ar_retr, 95)})
    B, ci, seed = cfg.eval.bootstrap_samples, cfg.eval.ci, cfg.seed
    diffs = []
    for name, a, b in (("adaptive - always_rag", adaptive, ar), ("adaptive - llm_only", adaptive, lo),
                       ("always_rag - llm_only", ar, lo)):
        m = paired_mean_diff(a, b, None, B, ci, seed)
        md = paired_stat_diff(a, b, np.median, B, ci, seed)
        diffs.append({"comparison": name, "n": len(a), "mean_diff_ms": m[0], "mean_ci_lo": m[1],
                      "mean_ci_hi": m[2], "median_diff_ms": md[0], "median_ci_lo": md[1],
                      "median_ci_hi": md[2]})
    info = {"n": len(qids), "dropped_errors": bad, "routed_to_llm_only": int(sum(r == "llm_only" for r in route))}
    return pd.DataFrame(rows), pd.DataFrame(diffs), info


def bootstrap_table(cfg: Config, df: pd.DataFrame) -> pd.DataFrame:
    pairs = [("always_rag", "llm_only"), ("oracle", "always_rag"), ("oracle", "llm_only"),
             ("llm_decision_router", "always_rag"), ("llm_decision_router", "llm_only"),
             ("llm_decision_router", "oracle")]
    out = []
    for aset in df.answer_set.unique():
        d = df[df.answer_set == aset]
        wide = {"correct": d.pivot(index="qid", columns="system", values="correct"),
                "usd_per_1k_q": d.pivot(index="qid", columns="system", values="total_usd") * 1000}
        ds_of = d.drop_duplicates("qid").set_index("qid").dataset
        for ds in sorted(d.dataset.unique()) + ["ALL"]:
            qids = ds_of.index if ds == "ALL" else ds_of[ds_of == ds].index
            strata = ds_of.loc[qids].values if ds == "ALL" else None
            for a, b in pairs:
                for metric, w in wide.items():
                    m, lo, hi = paired_mean_diff(w.loc[qids, a].astype(float), w.loc[qids, b].astype(float),
                                                 strata, cfg.eval.bootstrap_samples, cfg.eval.ci, cfg.seed)
                    out.append({"answer_set": aset, "dataset": ds, "comparison": f"{a} - {b}",
                                "metric": metric if metric != "correct" else cfg.eval.correct_metric,
                                "n": len(qids), "diff": m, "ci_lo": lo, "ci_hi": hi,
                                "significant": not (lo <= 0 <= hi)})
    return pd.DataFrame(out)


# --- report ----------------------------------------------------------------------------------

def fmt(x, nd=3):
    return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"


def md_table(df: pd.DataFrame, cols: list[tuple[str, str, int | None]]) -> str:
    head = "| " + " | ".join(c[1] for c in cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    lines = [head, sep]
    for _, r in df.iterrows():
        cells = []
        for key, _, nd in cols:
            v = r[key]
            cells.append(fmt(v, nd) if nd is not None and isinstance(v, (float, np.floating)) else str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def run(cfg: Config, dry_run: bool) -> None:
    all_q = {q["qid"]: q for q in load_questions(cfg, dry_run)}
    recs, calls = load_runs(cfg, dry_run, latency=False)
    lat, _ = load_runs(cfg, dry_run, latency=True)

    missing = {s: [q for q in all_q if q not in recs[s]] for s in cfg.systems}
    if any(missing.values()):
        raise SystemExit(f"missing records: { {s: len(v) for s, v in missing.items()} }")
    excluded = {q: [s for s in cfg.systems if error_kind(recs[s][q]) == "flagged"] for q in all_q}
    excluded = {q: v for q, v in excluded.items() if v}
    questions = {q: v for q, v in all_q.items() if q not in excluded}
    out = cfg.path("results", dry_run) / "summary"
    out.mkdir(parents=True, exist_ok=True)

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

    write_text(out / "summary.md", report(cfg, dry_run, all_q, questions, excl_df, metrics, labels, decision,
                                          breakeven, leakage, boot, lat_tab, lat_diff, lat_info, retry_rows,
                                          df, main_set))
    print((out / "summary.md").read_text())


def report(cfg, dry_run, all_q, questions, excl_df, metrics, labels, decision, breakeven, leakage, boot,
           lat_tab, lat_diff, lat_info, retry_rows, df, main_set) -> str:
    p = cfg.pricing[cfg.llm.model]
    cm = cfg.eval.correct_metric
    L = [f"# Results{' (dry run)' if dry_run else ''}", "",
         f"Model `{cfg.llm.model}`; prices ${p['input_per_1m']}/1M input, ${p['cached_input_per_1m']}/1M cached "
         f"input, ${p['output_per_1m']}/1M output (source: {p['source']}, retrieved {p['retrieved']}). "
         f"BM25 retrieval cost ${cfg.pricing['retrieval_bm25']['per_call_usd']}/call (local). "
         f"\"Correct\" = **{cm}**. Main answer set: `{main_set}` (accuracy ignores aliases of <= "
         f"{cfg.eval.accuracy_min_alias_chars - 1} normalized chars). Bootstrap: {cfg.eval.bootstrap_samples:,} "
         f"paired resamples, stratified by dataset for pooled rows, {cfg.eval.ci:.0%} percentile CI.", "",
         "## Question set", "",
         f"{len(all_q)} questions; **{len(questions)} in the common comparison set**; "
         f"{len(excl_df)} excluded because the prompt was rejected by OpenAI's filter twice "
         f"(first call + one `--retry-flagged`).", ""]
    if len(excl_df):
        L += [md_table(excl_df, [("qid", "qid", None), ("dataset", "dataset", None), ("split", "split", None),
                                 ("flagged_in", "flagged in", None), ("calls", "calls", None)]), "",
              "Excluded per dataset: " + ", ".join(f"{k} {v}" for k, v in
                                                     excl_df.dataset.value_counts().sort_index().items()), ""]
    L += ["Calls and retries:", "", md_table(pd.DataFrame(retry_rows), [
        ("system", "system", None), ("calls", "calls", None),
        ("qids_called_more_than_once", "qids retried", None), ("recovered", "recovered on retry", None)]), ""]

    def main_tab(split, aset):
        m = metrics[(metrics.split == split) & (metrics.answer_set == aset)].copy()
        m["system"] = pd.Categorical(m.system, SYSTEMS)
        return m.sort_values(["dataset", "system"])

    cols = [("dataset", "dataset", None), ("system", "system", None), ("n", "n", None), ("em", "EM", 3),
            ("f1", "F1", 3), ("accuracy", "Acc", 3), ("mean_input_tokens", "in tok", 1),
            ("mean_output_tokens", "out tok", 1), ("mean_reasoning_tokens", "reas tok", 2),
            ("usd_per_q", "$/q", 7), ("retrieval_calls", "retr calls", None), ("failed_calls", "failed", None)]
    L += ["## Main results (all splits)", "",
          "Tokens and cost include the router call for `llm_decision_router`. Failed calls count as wrong.", "",
          md_table(main_tab("all", main_set), cols), "",
          "## Test split only", "", md_table(main_tab("test", main_set)[lambda x: x.dataset == "ALL"], cols), ""]

    if "adaptive_rag" in cfg.eval.answer_sets:
        pc = [("dataset", "dataset", None), ("system", "system", None), ("em", "EM", 3), ("f1", "F1", 3),
              ("accuracy", "Acc", 3)]
        L += ["## Adaptive-RAG comparison: Adaptive-RAG's gold answers", "",
              "Gold = what Adaptive-RAG/IRCoT score against, without our short-alias filter: NQ/TriviaQA the "
              "full DPR answer list, HotpotQA/2Wiki/MuSiQue the single IRCoT answer, PopQA (not in "
              "Adaptive-RAG) all `possible_answers`. Accuracy is still token-bounded containment. "
              "Base systems only.", "",
              md_table(main_tab("all", "adaptive_rag")[lambda x: x.system.isin(BASE)], pc), ""]

    lab = labels[(labels.split == "all") & (labels.answer_set == main_set)]
    lab_cols = [("dataset", "dataset", None), ("n", "n", None), ("no_retrieval_ok", "no_retrieval_ok", None),
                ("both_ok", "both_ok", None), ("rag_hurts", "rag_hurts", None),
                ("retrieval_needed", "retrieval_needed", None), ("both_fail", "both_fail", None)]
    L += ["## Outcome labels", "",
          "`no_retrieval_ok` = llm_only correct (= both_ok + rag_hurts); `rag_hurts` = llm_only correct, "
          "always_rag wrong; `retrieval_needed` = llm_only wrong, always_rag correct; `both_fail` = both wrong.", "",
          md_table(lab, lab_cols), "",
          "### rag_hurts per dataset and split", "",
          md_table(labels[labels.answer_set == main_set]
                   .pivot(index="dataset", columns="split", values="rag_hurts")
                   .reindex(list(lab.dataset)).reset_index()[["dataset", "train", "dev", "test", "all"]],
                   [("dataset", "dataset", None), ("train", "train", None), ("dev", "dev", None),
                    ("test", "test", None), ("all", "all", None)]), ""]

    mo = metrics[(metrics.split == "all") & (metrics.answer_set == main_set) & (metrics.dataset == "ALL")] \
        .set_index("system")
    o, a = mo.loc["oracle"], mo.loc["always_rag"]
    L += ["## Oracle vs Always-RAG", "",
          f"Oracle {cm} {o.correct:.3f} vs Always-RAG {a.correct:.3f}; cost per question ${o.usd_per_q:.7f} vs "
          f"${a.usd_per_q:.7f} (**{1 - o.usd_per_q / a.usd_per_q:.1%} cheaper**); retrieval calls "
          f"{o.retrieval_calls} vs {a.retrieval_calls} ({1 - o.retrieval_calls / a.retrieval_calls:.1%} fewer).", ""]

    dsel = decision[decision.answer_set == main_set]
    L += ["## llm_decision router (the model's own YES/NO)", "",
          "Route: YES -> llm_only, NO/invalid -> always_rag. Decision cost is charged as router cost. "
          "`agree w/ oracle` is dominated by both_fail questions (the oracle sends them to llm_only by "
          "convention); `agree on decisive` uses only rag_hurts + retrieval_needed, where the route "
          "changes the outcome.", "",
          md_table(dsel, [("dataset", "dataset", None), ("n", "n", None), ("yes", "YES", None), ("no", "NO", None),
                          ("invalid", "invalid", None), ("agree_with_oracle", "agree w/ oracle", 3),
                          ("n_decisive", "decisive q", None), ("agree_on_decisive", "agree on decisive", 3),
                          ("self_knowledge_acc", "YES<->llm_only correct", 3),
                          ("yes_precision", "P(llm_only correct | YES)", 3),
                          ("llm_only_correct_rate", "llm_only correct rate", 3)]), "",
          "Confusion vs oracle route (all datasets):", ""]
    allr = dsel[dsel.dataset == "ALL"].iloc[0]
    L += ["| | oracle: llm_only | oracle: always_rag |", "|---|---|---|",
          f"| decision YES | {allr.yes_and_oracle_llm_only} | {allr.yes_but_oracle_rag} |",
          f"| decision NO/invalid | {allr.no_but_oracle_llm_only} | {allr.no_and_oracle_rag} |", ""]
    dr = mo.loc["llm_decision_router"]
    L += [f"Score and cost (incl. decision call): {cm} {dr.correct:.3f}, ${dr.usd_per_q:.7f}/q "
          f"(router ${dr.router_usd_per_q:.7f}, generation ${dr.generation_usd_per_q:.7f}); "
          f"retrieval rate {dr.retrieval_rate:.1%}.", "",
          "Decision call tokens (mean per question): input "
          f"{df[(df.system == 'llm_decision_router') & (df.answer_set == main_set)].router_input_tokens.mean():.1f}, "
          f"output {df[(df.system == 'llm_decision_router') & (df.answer_set == main_set)].router_output_tokens.mean():.1f}, "
          f"reasoning {df[(df.system == 'llm_decision_router') & (df.answer_set == main_set)].router_reasoning_tokens.mean():.2f}.", ""]

    L += ["## Break-even: decision cost vs. skipped context", "",
          "For questions the decision routes to llm_only (YES), skipping retrieval saves the context tokens "
          "(always_rag input − llm_only input) and the cost difference. Ratio < 1 means the decision call pays "
          "for itself. `breakeven_skip_rate` = decision cost per question / mean saving per skipped question; "
          "the router must skip at least this share of questions to break even on cost.", "",
          md_table(breakeven, [("dataset", "dataset", None), ("n", "n", None), ("skipped_retrievals", "skipped", None),
                               ("saved_context_tokens_total", "saved ctx tok", None),
                               ("decision_tokens_total", "decision tok (in+out)", None),
                               ("token_ratio_decision_to_saved_context", "tok ratio", 3),
                               ("decision_usd_total", "decision $", 5), ("saved_usd_total", "saved $", 5),
                               ("cost_to_saving_ratio_usd", "$ ratio", 3),
                               ("breakeven_skip_rate", "break-even skip rate", 3),
                               ("actual_skip_rate", "actual skip rate", 3)]), ""]

    if lat_tab is not None:
        L += ["## Latency (sequential run, test subset)", "",
              f"{lat_info['n']} test questions with valid records for all three calls "
              f"(dropped: {len(lat_info['dropped_errors'])}); concurrency 1, fresh retrieval. "
              f"Adaptive = decision call followed by the chosen path, run sequentially; "
              f"{lat_info['routed_to_llm_only']} of {lat_info['n']} routed to llm_only.", "",
              md_table(lat_tab, [("system", "system", None), ("n", "n", None), ("mean_ms", "mean ms", 0),
                                 ("p50_ms", "P50 ms", 0), ("p95_ms", "P95 ms", 0)]), "",
              md_table(lat_diff, [("comparison", "comparison", None), ("mean_diff_ms", "mean diff ms", 0),
                                  ("mean_ci_lo", "CI lo", 0), ("mean_ci_hi", "CI hi", 0),
                                  ("median_diff_ms", "median diff ms", 0), ("median_ci_lo", "CI lo", 0),
                                  ("median_ci_hi", "CI hi", 0)]), ""]

    b = boot[(boot.answer_set == main_set) & (boot.dataset == "ALL")]
    L += ["## Paired bootstrap differences (all datasets)", "",
          md_table(b, [("comparison", "comparison", None), ("metric", "metric", None), ("diff", "diff", 4),
                       ("ci_lo", "CI lo", 4), ("ci_hi", "CI hi", 4), ("significant", "CI excludes 0", None)]), "",
          "Per-dataset intervals: `bootstrap.csv`.", ""]

    lk = leakage[leakage.dataset == "ALL"]
    L += ["## Reasoning leakage", "",
          "Leak = `incomplete` (hit max_output_tokens) or >= 17 words or a deliberation marker "
          "(see `src/leakage.py`). Common question set; final record per question.", "",
          md_table(lk, [("system", "system", None), ("n", "n", None), ("leak", "leaked", None),
                        ("leak_rate", "rate", 3), ("incomplete", "incomplete", None), ("long", ">=17 words", None),
                        ("marker", "marker", None)]), "",
          "Per dataset: `leakage.csv`.", ""]
    return "\n".join(L) + "\n"


def main() -> None:
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    run(load_config(args.config), args.dry_run)


if __name__ == "__main__":
    main()

