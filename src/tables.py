"""Pandas summaries for Stage 4. Formulas are the evaluation; this module only aggregates rows."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.bootstrap import paired_mean_diff, paired_stat_diff
from src.config import Config
from src.leakage import leak_flags

LABELS = ("both_ok", "rag_hurts", "retrieval_needed", "both_fail")


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
