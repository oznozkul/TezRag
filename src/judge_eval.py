"""Report section: do the conclusions hold under a second correctness criterion?

For every model whose answers are fully judged (src/judge.py), the systems are rebuilt with the
judge's verdict as `correct` (answer set `judge` in src/evaluate.py) and compared with the main
criterion (token-bounded accuracy, answer set `all`). Writes judge_compare.csv and
judge_disagreement.csv; adds the human-label agreement from src/annotation.py when labels exist.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.bootstrap import paired_mean_diff
from src.config import Config

SYSTEMS = ("llm_only", "always_rag", "oracle_optimistic", "oracle_realistic", "llm_decision_router")
DIFFS = (("always_rag", "llm_only"), ("llm_decision_router", "always_rag"),
         ("oracle_realistic", "always_rag"))


def missing_verdicts(cfg: Config, recs: dict, kept: dict, verdicts: dict, model: str) -> int:
    return sum(1 for s in cfg.judge.systems for qid in kept
               if recs[s][qid]["error"] is None and (model, s, qid) not in verdicts)


def compare_rows(cfg: Config, model: str, main: pd.DataFrame, judged: pd.DataFrame) -> list[dict]:
    rows = []
    B, ci, seed = cfg.eval.bootstrap_samples, cfg.eval.ci, cfg.seed
    for crit, df in (("accuracy", main), ("judge", judged)):
        w = {s: g.set_index("qid").sort_index() for s, g in df.groupby("system")}
        strata = w["llm_only"].dataset.to_numpy()
        # dollar saving; local models cost $0, so their saving is measured in billed tokens
        col = "total_usd" if float(w["always_rag"].total_usd.mean()) > 0 else "billed_tokens"
        for s in ("always_rag", "oracle_realistic"):
            w[s] = w[s].assign(billed_tokens=w[s].billed_input_tokens + w[s].billed_output_tokens)
        base = {"model": model, "criterion": crit, "n": len(w["llm_only"]),
                "both_fail_share": float((w["llm_only"].label == "both_fail").mean()),
                "oracle_realistic_saving": 1 - float(w["oracle_realistic"][col].mean())
                / float(w["always_rag"][col].mean()), "saving_unit": "usd" if col == "total_usd" else "tokens"}
        for s in SYSTEMS:
            rows.append({**base, "kind": "accuracy", "name": s, "value": float(w[s].correct.mean()),
                         "ci_lo": float("nan"), "ci_hi": float("nan")})
        for a, b in DIFFS:
            m, lo, hi = paired_mean_diff(w[a].correct.astype(float).to_numpy(),
                                         w[b].correct.astype(float).to_numpy(), strata, B, ci, seed)
            rows.append({**base, "kind": "diff", "name": f"{a} - {b}", "value": m, "ci_lo": lo, "ci_hi": hi})
    return rows


def disagreement_rows(model: str, main: pd.DataFrame, judged: pd.DataFrame) -> list[dict]:
    rows = []
    for s in ("llm_only", "always_rag"):
        a = main[main.system == s].set_index("qid").correct.astype(bool)
        j = judged[judged.system == s].set_index("qid").correct.astype(bool).reindex(a.index)
        rows.append({"model": model, "system": s, "n": len(a), "accuracy_rate": float(a.mean()),
                     "judge_rate": float(j.mean()), "agree": float((a == j).mean()),
                     "judge_only_correct": int((j & ~a).sum()), "accuracy_only_correct": int((a & ~j).sum())})
    return rows


def judge_section(cfg: Config, dry_run: bool, bundles: list, frames: dict, out: Path, shared: Path) -> str:
    from src import evaluate
    from src.annotation import agreement_markdown, all_agreement, annotation_dir
    from src.judge import load_verdicts
    from src.report import md_table

    if cfg.judge is None:
        return ""
    verdicts = load_verdicts(cfg, dry_run)
    evaluate.JUDGE_VERDICTS.clear()
    evaluate.JUDGE_VERDICTS.update(verdicts)

    compare, disagree, pending = [], [], []
    for model, recs, _excl, kept in bundles:
        miss = missing_verdicts(cfg, recs, kept, verdicts, model)
        if miss:
            pending.append(f"`{model}` ({miss} answers not judged)")
            continue
        judged = pd.DataFrame(evaluate.build_rows(cfg, kept, recs, evaluate.JUDGE_SET))
        compare += compare_rows(cfg, model, frames[model], judged)
        disagree += disagreement_rows(model, frames[model], judged)

    L = ["## Second correctness criterion: LLM judge", ""]
    if not compare:
        L += [f"No model is fully judged yet (`python -m src.judge`). Pending: {', '.join(pending) or 'all'}.", ""]
    else:
        cmp_df, dis_df = pd.DataFrame(compare), pd.DataFrame(disagree)
        for folder in {out, shared}:
            cmp_df.to_csv(folder / "judge_compare.csv", index=False)
            dis_df.to_csv(folder / "judge_disagreement.csv", index=False)
        L += [f"Judge `{cfg.judge.model}` reads the question, the gold answers and one prediction and replies "
              "CORRECT or INCORRECT. `judge only` = judge correct, accuracy wrong (what accuracy misses); "
              "`accuracy only` = the reverse.", "",
              md_table(dis_df, [("model", "model", None), ("system", "system", None), ("n", "n", None),
                                ("accuracy_rate", "accuracy", 3), ("judge_rate", "judge", 3),
                                ("agree", "agree", 3), ("judge_only_correct", "judge only", None),
                                ("accuracy_only_correct", "accuracy only", None)]), "",
              "Main comparisons under both criteria (paired 95% CI, stratified by dataset):", ""]
        d = cmp_df[cmp_df.kind == "diff"].copy()
        d["result"] = [f"{v:+.3f} [{lo:+.3f}, {hi:+.3f}]" for v, lo, hi in zip(d.value, d.ci_lo, d.ci_hi)]
        wide = d.pivot_table(index=["model", "criterion", "both_fail_share", "oracle_realistic_saving", "saving_unit"],
                             columns="name", values="result", aggfunc="first", sort=False).reset_index()
        cols = [("model", "model", None), ("criterion", "criterion", None),
                ("both_fail_share", "both_fail", 3), ("oracle_realistic_saving", "real. oracle saving", 3), ("saving_unit", "unit", None)]
        cols += [(f"{a} - {b}", f"{a} − {b}", None) for a, b in DIFFS]
        L += [md_table(wide, cols), ""]
        if pending:
            L += [f"Not fully judged yet: {', '.join(pending)}.", ""]

    sheet = annotation_dir(cfg, dry_run) / "sheet.csv"
    n_sheet = sum(1 for _ in open(sheet, encoding="utf-8-sig")) - 1 if sheet.exists() else 0
    agr = all_agreement(cfg, dry_run, verdicts)
    if not agr.empty:
        for folder in {out, shared}:
            agr.to_csv(folder / "annotation_agreement.csv", index=False)
    L += [agreement_markdown(agr, n_sheet)]
    return "\n".join(L)
