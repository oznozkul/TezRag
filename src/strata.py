"""Accuracy and cost by a source attribute. Attributes are not one difficulty scale.

hop_type            every question; single vs multi
pop_tertile        PopQA only; thirds of log10(subject popularity). low = least popular
musique_hops       MuSiQue only; 2 / 3 / 4 from the question id
hotpot_type        HotpotQA only. level is hard for the whole sample, so the cut is bridge
                   vs comparison, which is not a difficulty ranking
wiki_type          2Wiki only; reasoning type, not a difficulty ranking
"""
from __future__ import annotations

import pandas as pd

from src.bootstrap import mean_ci, paired_mean_diff
from src.config import Config

SYSTEMS = ("llm_only", "always_rag", "oracle", "llm_decision_router")

SPECS = (
    {"name": "hop_type", "column": "hop_type", "dataset": None,
     "note": "single vs multi; the only cut defined for every question"},
    {"name": "pop_tertile", "column": "pop_tertile", "dataset": "popqa",
     "note": "thirds of log10(s_pop) on the frozen PopQA sample; low is least popular. "
             "Not a difficulty ranking."},
    {"name": "musique_hops", "column": "musique_hops", "dataset": "musique",
     "note": "hop count from the MuSiQue id; subtypes such as 3hop1 and 4hop2 collapse to 3 and 4"},
    {"name": "hotpot_type", "column": "hotpot_type", "dataset": "hotpotqa",
     "note": "HotpotQA level is hard for every question in this sample; type is not a difficulty rank"},
    {"name": "wiki_type", "column": "wiki_type", "dataset": "2wikimultihopqa",
     "note": "2Wiki reasoning type, not a difficulty rank"},
)

META_COLUMNS = ["qid", "hop_type", "hotpot_level", "hotpot_type", "musique_hops", "wiki_type",
                "s_pop", "pop_tertile"]


def with_meta(df: pd.DataFrame, meta: dict[str, dict]) -> pd.DataFrame:
    extra = pd.DataFrame([meta[q] for q in df["qid"].unique()])
    keep = [c for c in META_COLUMNS if c in extra.columns]
    out = df.merge(extra[keep], on="qid", how="left")
    missing = int(out["hop_type"].isna().sum())
    if missing:
        raise KeyError(f"{missing} rows have no question_meta entry")
    return out


def _subset(df: pd.DataFrame, spec: dict) -> pd.DataFrame:
    d = df if spec["dataset"] is None else df[df.dataset == spec["dataset"]]
    if d.empty:
        return d
    if d[spec["column"]].isna().any():
        raise ValueError(f"{spec['name']} has empty values")
    return d


def stratum_table(df: pd.DataFrame, model: str, cfg: Config) -> pd.DataFrame:
    """df: one answer set, already joined with question_meta, one row per question per system."""
    rows = []
    for spec in SPECS:
        d = _subset(df, spec)
        if d.empty:
            continue
        for value, g in d.groupby(spec["column"], sort=True):
            if spec["name"] == "musique_hops":
                value = int(value)
            for system in SYSTEMS:
                s = g[g.system == system]
                if s.empty:
                    continue
                acc, acc_lo, acc_hi = mean_ci(s.correct, cfg.eval.bootstrap_samples, cfg.eval.ci, cfg.seed)
                usd, usd_lo, usd_hi = mean_ci(s.total_usd, cfg.eval.bootstrap_samples, cfg.eval.ci, cfg.seed)
                rows.append({
                    "model": model, "stratum": spec["name"], "stratum_value": value,
                    "note": spec["note"], "system": system, "n": len(s),
                    "em": float(s.em.mean()), "f1": float(s.f1.mean()),
                    "accuracy": acc, "acc_ci_lo": acc_lo, "acc_ci_hi": acc_hi,
                    "usd_per_q": usd, "usd_ci_lo": usd_lo, "usd_ci_hi": usd_hi,
                })
    return pd.DataFrame(rows)


def _aligned(a: pd.DataFrame, b: pd.DataFrame, column: str, value, system: str):
    left = a[(a[column] == value) & (a.system == system)].set_index("qid")
    right = b[(b[column] == value) & (b.system == system)].set_index("qid")
    common = left.index.intersection(right.index)
    return left.loc[common], right.loc[common]


def compare_table(frames: dict[str, pd.DataFrame], cfg: Config) -> pd.DataFrame:
    """Paired differences on the qids present for both models. `frames` are meta-joined."""
    models = list(frames)
    rows = []
    if len(models) < 2:
        return pd.DataFrame(rows)
    for i, ma in enumerate(models):
        for mb in models[i + 1:]:
            a, b = frames[ma], frames[mb]
            for spec in SPECS:
                da, db = _subset(a, spec), _subset(b, spec)
                if da.empty or db.empty:
                    continue
                values = sorted(set(da[spec["column"]].unique()) & set(db[spec["column"]].unique()),
                                key=str)
                for value in values:
                    for system in SYSTEMS:
                        la, lb = _aligned(da, db, spec["column"], value, system)
                        if la.empty:
                            continue
                        strata = la["dataset"].to_numpy() if spec["dataset"] is None else None
                        acc = paired_mean_diff(la.correct, lb.correct, strata,
                                                cfg.eval.bootstrap_samples, cfg.eval.ci, cfg.seed)
                        usd = paired_mean_diff(la.total_usd, lb.total_usd, strata,
                                                cfg.eval.bootstrap_samples, cfg.eval.ci, cfg.seed)
                        rows.append({
                            "model_a": ma, "model_b": mb, "stratum": spec["name"],
                            "stratum_value": value, "note": spec["note"], "system": system,
                            "n": len(la),
                            "accuracy_a": float(la.correct.mean()), "accuracy_b": float(lb.correct.mean()),
                            "acc_diff": acc[0], "acc_ci_lo": acc[1], "acc_ci_hi": acc[2],
                            "usd_per_q_a": float(la.total_usd.mean()),
                            "usd_per_q_b": float(lb.total_usd.mean()),
                            "usd_diff": usd[0], "usd_ci_lo": usd[1], "usd_ci_hi": usd[2],
                        })
    return pd.DataFrame(rows)


def stratum_markdown(strata: pd.DataFrame, compare: pd.DataFrame) -> str:
    from src.report import fmt, md_table

    if strata.empty:
        return ""
    lines = ["## Accuracy and cost by source attribute", "",
             "Cuts are the attributes the source datasets define. They are not one difficulty scale, "
             "and they are not model outcomes. NQ and TriviaQA have no source difficulty field; they "
             "appear only under `hop_type`. Intervals are percentile bootstrap CIs of the mean. "
             "Full tables: `strata.csv`"
             + (", `model_compare.csv`." if not compare.empty else ".")]
    show = [("stratum_value", "value", None), ("system", "system", None), ("n", "n", None),
            ("accuracy", "Acc", 3), ("acc_ci_lo", "CI lo", 3), ("acc_ci_hi", "CI hi", 3),
            ("usd_per_q", "$/q", 7)]
    for model, g in strata.groupby("model", sort=True):
        lines += ["", f"### {model}", ""]
        for spec in SPECS:
            sub = g[g.stratum == spec["name"]]
            if sub.empty:
                continue
            lines += [f"**{spec['name']}.** {spec['note']}", "", md_table(sub, show), ""]
    if compare.empty:
        lines += ["One model is in the results directory, so there is no cross-model comparison.", ""]
    else:
        lines += ["### Paired model difference (A − B)", "",
                  "Same questions, same route. A positive accuracy difference means A is higher.", ""]
        cols = [("stratum", "stratum", None), ("stratum_value", "value", None), ("system", "system", None),
                ("n", "n", None), ("acc_diff", "acc A-B", 3), ("acc_ci_lo", "CI lo", 3),
                ("acc_ci_hi", "CI hi", 3), ("usd_diff", "$/q A-B", 7)]
        lines += [md_table(compare, cols), ""]
    return "\n".join(lines)
