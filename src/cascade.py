"""Answer-first cascade: always answer without retrieval, retrieve only when that answer looks unreliable.

    python -m src.cascade [--dry-run] [--criterion judge]

This is the design of Dong et al. (2026) and TARG (Wang et al., 2026): the no-retrieval answer is the
decision signal, and when the cascade does not escalate, that answer is the final one, so the
decision is not pure overhead (unlike the separate YES/NO call of `llm_decision`). Everything is
composed from the logged llm_only and always_rag records; no API calls.

Cost per question = llm_only call + (escalated ? always_rag call : 0). Retrieval is local and free.
The cascade saves money against Always-RAG only when its escalation rate is below
1 - cost(llm_only) / cost(always_rag) (break-even escalation rate).

Policies:
  cascade_oracle   escalate iff the llm_only answer is wrong (upper bound; uses gold answers)
  cascade_abstain  escalate iff the answer abstains or hedges ("I don't know", "not sure", "?", ...)
                   or the call failed
  cascade_learned  logistic regression on TF-IDF of question + answer and simple answer features,
                   target `need` (retrieval_needed); fit on train, threshold on dev, report on test

Writes results/summary/cascade_test[_judge].csv.
"""
from __future__ import annotations

import argparse
import re

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from src.bootstrap import paired_mean_diff
from src.config import Config, load_config
from src.learned_routers import model_tables, target_label
from src.io_utils import setup_logging

ABSTAIN = re.compile(r"(don.?t know|do not know|not sure|unknown|unclear|cannot|can.?t|unable|"
                     r"no (?:information|data|answer)|not (?:specified|mentioned|provided|stated|available|enough)|"
                     r"insufficient|\?)", re.I)
BUDGETS = (0.8, 0.6, 0.4)


def abstains(answer: str, failed: bool) -> bool:
    return bool(failed or not (answer or "").strip() or ABSTAIN.search(answer or ""))


def answer_features(answers: pd.Series, failed: pd.Series) -> np.ndarray:
    a = answers.fillna("")
    return np.column_stack([
        [abstains(x, f) for x, f in zip(a, failed)],
        a.str.split().str.len().fillna(0),
        a.str.len(),
        a.str.contains(r"\d", regex=True),
        a.str.contains("\n"),
    ]).astype(float)


def learned_escalation(t: pd.DataFrame, train: np.ndarray) -> np.ndarray:
    """P(retrieval_needed | question, answer), fit on train rows."""
    y = target_label(t, "need").to_numpy()
    if y[train].min() == y[train].max():
        return np.full(len(t), float(y[train].mean()))
    vq = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True).fit(t.question[train])
    va = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True).fit(t.lo_pred[train])
    f = answer_features(t.lo_pred, t.lo_failed)
    sc = StandardScaler().fit(f[train])
    X = hstack([vq.transform(t.question), va.transform(t.lo_pred), csr_matrix(sc.transform(f))]).tocsr()
    m = LogisticRegression(C=1.0, max_iter=3000).fit(X[train], y[train])
    return m.predict_proba(X)[:, 1]


def cost_cols(t: pd.DataFrame) -> tuple[str, str, str]:
    """Dollar cost for priced models, billed tokens for local ones."""
    if float(t.usd_ar.mean()) > 0:
        return "usd_lo", "usd_ar", "usd"
    return "tok_lo", "tok_ar", "tokens"


def evaluate_policy(cfg: Config, model: str, name: str, t: pd.DataFrame, esc: np.ndarray, point: str) -> dict:
    lo, ar, unit = cost_cols(t)
    correct = np.where(esc, t.c_ar, t.c_lo)
    cost = t[lo].to_numpy() + np.where(esc, t[ar], 0.0)
    strata = t.dataset.to_numpy()
    B, ci, seed = cfg.eval.bootstrap_samples, cfg.eval.ci, cfg.seed
    da = paired_mean_diff(correct, t.c_ar.to_numpy(), strata, B, ci, seed)
    always = float(t[ar].mean())
    return {"model": model, "policy": name, "point": point, "n": len(t), "cost_unit": unit,
            "escalation_rate": float(esc.mean()), "accuracy": float(correct.mean()),
            "always_rag_accuracy": float(t.c_ar.mean()), "llm_only_accuracy": float(t.c_lo.mean()),
            "acc_diff": da[0], "acc_ci_lo": da[1], "acc_ci_hi": da[2],
            "relative_cost": float(cost.mean()) / always if always else float("nan"),
            "breakeven_escalation": 1 - float(t[lo].mean()) / always if always else float("nan")}


def esc_threshold_for_budget(p_dev: np.ndarray, budget: float) -> float:
    """Escalate the `budget` share of dev questions with the highest P(need)."""
    n = int(round(budget * len(p_dev)))
    if n <= 0:
        return float("inf")
    return float(np.sort(p_dev)[::-1][n - 1])


def no_loss_threshold(t_dev: pd.DataFrame, p_dev: np.ndarray) -> float:
    """Highest threshold (fewest escalations) whose dev accuracy is >= Always-RAG's dev accuracy."""
    target = float(t_dev.c_ar.mean())
    best = -np.inf
    for tau in np.unique(np.concatenate([p_dev, [-np.inf]])):
        acc = float(np.where(p_dev >= tau, t_dev.c_ar, t_dev.c_lo).mean())
        if acc >= target - 1e-12:
            best = max(best, tau)
    return best


def run(cfg: Config, dry_run: bool, criterion: str = "accuracy") -> pd.DataFrame:
    rows = []
    for model, t in model_tables(cfg, dry_run, criterion).items():
        train, dev, test = (t.split == s for s in ("train", "dev", "test"))
        train, dev, test = train.to_numpy(), dev.to_numpy(), test.to_numpy()
        tt = t[test].reset_index(drop=True)
        rows.append(evaluate_policy(cfg, model, "cascade_oracle", tt, (tt.c_lo == 0).to_numpy(), "oracle"))
        rows.append(evaluate_policy(cfg, model, "cascade_abstain", tt,
                                    np.array([abstains(a, f) for a, f in zip(tt.lo_pred, tt.lo_failed)]), "rule"))
        p = learned_escalation(t, train)
        points = [("no_loss", no_loss_threshold(t[dev], p[dev]))]
        points += [(f"escalate_{int(b * 100)}", esc_threshold_for_budget(p[dev], b)) for b in BUDGETS]
        for point, tau in points:
            rows.append(evaluate_policy(cfg, model, "cascade_learned", tt, p[test] >= tau, point))
    df = pd.DataFrame(rows)
    out = cfg.path("results", dry_run) / "summary"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / f"cascade_test{'' if criterion == 'accuracy' else '_' + criterion}.csv", index=False)
    return df


def cascade_markdown(summary_dir) -> str:
    from pathlib import Path

    from src.report import md_table

    parts = []
    for suffix, label in (("", "accuracy"), ("_judge", "LLM judge")):
        path = Path(summary_dir) / f"cascade_test{suffix}.csv"
        if not path.exists():
            continue
        d = pd.read_csv(path)
        d["result"] = [f"{a:+.3f} [{lo:+.3f}, {hi:+.3f}] · cost {c:.2f} · esc {e:.0%}"
                       for a, lo, hi, c, e in zip(d.acc_diff, d.acc_ci_lo, d.acc_ci_hi, d.relative_cost,
                                                  d.escalation_rate)]
        d["col"] = d.policy.str.replace("cascade_", "") + ":" + d.point
        wide = d.pivot_table(index=["model", "cost_unit", "breakeven_escalation"], columns="col",
                             values="result", aggfunc="first", sort=False).reset_index()
        order = ["oracle:oracle", "abstain:rule", "learned:no_loss", "learned:escalate_80",
                 "learned:escalate_60", "learned:escalate_40"]
        cols = [("model", "model", None), ("cost_unit", "unit", None),
                ("breakeven_escalation", "break-even esc.", 3)] + [(c, c, None) for c in order if c in wide.columns]
        parts += [f"Correct = {label}:", "", md_table(wide, cols), ""]
    if not parts:
        return ""
    return "\n".join([
        "## Answer-first cascade (no extra API calls)", "",
        "Every question is first answered without retrieval; it is escalated to Always-RAG only when that "
        "answer looks unreliable, and otherwise that answer is final (Dong et al. 2026; TARG). Cost = llm_only "
        "call + always_rag call when escalated, relative to Always-RAG (dollars for priced models, billed "
        "tokens for local ones); cost < 1 saves. `break-even esc.` = 1 − cost(llm_only)/cost(always_rag): "
        "escalating more than this share costs more than Always-RAG. Cells: test accuracy − Always-RAG "
        "[paired 95% CI] · relative cost · escalation rate. `learned` points: `no_loss` = dev-accuracy-matched "
        "threshold, `escalate_N` = escalate N% of dev questions.", "", *parts])


def main() -> None:
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--criterion", choices=["accuracy", "judge"], default="accuracy")
    args = ap.parse_args()
    df = run(load_config(args.config), args.dry_run, args.criterion)
    print(df[["model", "policy", "point", "escalation_rate", "acc_diff", "acc_ci_lo", "acc_ci_hi",
              "relative_cost", "breakeven_escalation"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
