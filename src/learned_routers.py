"""Routers that make no LLM call: trained on train, threshold chosen on dev, reported on test.

    python -m src.learned_routers [--dry-run] [--criterion judge]

`--criterion judge` uses the LLM judge's verdicts (src/judge.py) as "correct" for labels, training and
evaluation; outputs get a `_judge` suffix. Default: token-bounded accuracy.

For every model with a complete run, a router scores each question and skips retrieval when the
score >= tau. Two training targets:
  lo_correct  y = llm_only is correct (the realistic oracle's rule); score = P(y)
  need        y = retrieval_needed (llm_only wrong, always_rag right); score = 1 - P(y). Questions
              that both paths get wrong count as safe to skip, so a router trained on this target can
              learn to skip groups of questions retrieval does not rescue (as the optimistic oracle
              does per question, but only from patterns in the question). The routed system reuses the logged llm_only / always_rag records of
that question (no new API calls); the router itself costs $0 and its compute time is measured.

Routers (features in src/router_features.py):
  dataset_prior   train rate of "llm_only correct" per source dataset (uses source metadata on purpose)
  rules           logistic regression on question-text features
  bm25            logistic regression on BM25 retrieval scores and question/passage overlap
  rules+bm25      both
  tfidf           logistic regression on word 1-2 gram TF-IDF of the question
  embed           logistic regression on bge-small question embeddings
  knn             mean label of the 15 most similar train questions (cosine, embeddings; SKR-style)
  embed+bm25      embeddings + scaled BM25 features

Leakage rules: fit on split=train only; tau on split=dev only; split=test only for reporting.
The 5-fold cross-validation over all questions is a separate robustness check (budget curves, AUC).

Operating points chosen on dev:
  no_loss   the largest skip rate whose dev accuracy is >= Always-RAG's dev accuracy
  loss_1pt  the largest skip rate whose dev accuracy is >= Always-RAG's dev accuracy - 0.01
  budget_80 the score quantile that retrieves for 80% of dev questions (a fixed budget; more stable
            than accuracy-matched points on a 600-question dev set)
Random baseline = skipping the same share of questions at random (expected value, exact).

Router selection (fixed before reading test): 5-fold cross-validation over train + dev only (test
questions never enter), out-of-fold scores, accuracy at an 80% retrieval budget minus Always-RAG on
those same questions, averaged over the six models. The best (router, target) under the main
criterion (accuracy) is the primary router; its test rows are the reported result, under both
criteria. The other routers stay in the CSVs as secondary results. The older cross-validation over
all questions (routers_cv_budget.csv) includes test questions and is descriptive only.

Writes results/summary/routers_test.csv, routers_cv_budget.csv, routers_auc.csv, routers_dev_curve.csv,
routers_selection.csv.
"""
from __future__ import annotations

import argparse
import logging
import time

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.bootstrap import paired_mean_diff
from src.config import Config, load_config
from src.data import load_questions
from src.dispatch import discover_run_dirs, excluded_qids, load_run_dir, model_of
from src.evaluate import build_rows
from src.io_utils import setup_logging
from src.router_features import bm25_features, question_embeddings, rule_features

log = logging.getLogger("learned_routers")

TARGETS = ("lo_correct", "need")
ROUTERS = ("dataset_prior", "rules", "bm25", "rules+bm25", "tfidf", "embed", "knn", "embed+bm25")
EMBED_ROUTERS = {"embed", "knn", "embed+bm25"}
BUDGETS = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5)
SELECTION_BUDGET = 0.8
KNN_K = 15


# --- data ----------------------------------------------------------------------------------------

def model_tables(cfg: Config, dry_run: bool, criterion: str = "accuracy") -> dict[str, pd.DataFrame]:
    """model -> one row per question: split, dataset, label, both paths' correctness/cost/tokens,
    and the text/BM25 inputs for features. Only complete runs; flagged questions dropped per model."""
    questions = {q["qid"]: q for q in load_questions(cfg, dry_run)}
    answer_set = "all"
    if criterion == "judge":
        from src import evaluate
        from src.judge import load_verdicts
        evaluate.JUDGE_VERDICTS.clear()
        evaluate.JUDGE_VERDICTS.update(load_verdicts(cfg, dry_run))
        answer_set = evaluate.JUDGE_SET
    out = {}
    for directory in discover_run_dirs(cfg.path("results", dry_run)):
        recs, _ = load_run_dir(directory)
        model = model_of(recs)
        if model is None or any(qid not in recs[s] for s in recs for qid in questions):
            continue
        excl = excluded_qids(questions, recs)
        kept = {q: v for q, v in questions.items() if q not in excl}
        try:
            rows = pd.DataFrame(build_rows(cfg, kept, recs, answer_set))
        except KeyError:
            log.warning("%s: not fully judged, skipped", model)
            continue
        lo = rows[rows.system == "llm_only"].set_index("qid")
        ar = rows[rows.system == "always_rag"].set_index("qid")
        t = pd.DataFrame({
            "qid": lo.index, "split": lo.split.values, "dataset": lo.dataset.values,
            "y": lo.correct.astype(int).values,
            "c_lo": lo.correct.astype(float).values, "c_ar": ar.loc[lo.index].correct.astype(float).values,
            "usd_lo": lo.total_usd.values, "usd_ar": ar.loc[lo.index].total_usd.values,
            "tok_lo": (lo.billed_input_tokens + lo.billed_output_tokens).values,
            "tok_ar": (ar.loc[lo.index].billed_input_tokens + ar.loc[lo.index].billed_output_tokens).values,
        })
        t["question"] = [kept[q]["question"] for q in t.qid]
        t["lo_pred"] = [(recs["llm_only"][q].get("prediction") or "") if recs["llm_only"][q]["error"] is None
                        else "" for q in t.qid]
        t["lo_failed"] = [recs["llm_only"][q]["error"] is not None for q in t.qid]
        t["bm25_scores"] = [recs["always_rag"][q].get("retrieved_scores") or [] for q in t.qid]
        t["rag_prompt"] = [recs["always_rag"][q].get("prompt") or "" for q in t.qid]
        out[model] = t.reset_index(drop=True)
    return out


def feature_frames(t: pd.DataFrame) -> dict[str, pd.DataFrame]:
    rules = pd.DataFrame([rule_features(q) for q in t.question])
    bm25 = pd.DataFrame([bm25_features(q, s, p) for q, s, p in zip(t.question, t.bm25_scores, t.rag_prompt)])
    return {"rules": rules, "bm25": bm25}


# --- routers -------------------------------------------------------------------------------------

def _lr():
    return LogisticRegression(C=1.0, max_iter=2000)


def fit_predict(name: str, t: pd.DataFrame, feats: dict, emb: np.ndarray | None,
                train: np.ndarray, seed: int) -> np.ndarray:
    """p(llm_only correct) for every row of t, fitted on rows where train is True."""
    y = t.y.to_numpy()
    if y[train].min() == y[train].max():                 # one class only (tiny dry runs)
        return np.full(len(t), float(y[train].mean()))
    if name == "dataset_prior":
        rate = t[train].groupby("dataset").y.mean()
        return t.dataset.map(rate).fillna(float(y[train].mean())).to_numpy(dtype=float)
    if name == "tfidf":
        m = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True), _lr())
        m.fit(t.question[train], y[train])
        return m.predict_proba(t.question)[:, 1]
    if name == "knn":
        sim = emb @ emb[train].T
        k = min(KNN_K, int(train.sum()))
        idx = np.argpartition(-sim, k - 1, axis=1)[:, :k]
        ytr = y[train]
        p = ytr[idx].mean(axis=1)
        # a training row must not see its own label
        own = np.where(train)[0]
        sim_own = sim[own].copy()
        sim_own[np.arange(len(own)), np.arange(len(own))] = -np.inf
        idx_own = np.argpartition(-sim_own, k - 1, axis=1)[:, :k]
        p[own] = ytr[idx_own].mean(axis=1)
        return p
    if name == "rules":
        X = feats["rules"].to_numpy()
    elif name == "bm25":
        X = feats["bm25"].to_numpy()
    elif name == "rules+bm25":
        X = np.hstack([feats["rules"].to_numpy(), feats["bm25"].to_numpy()])
    elif name == "embed":
        X = emb
    elif name == "embed+bm25":
        X = np.hstack([emb, StandardScaler().fit(feats["bm25"][train]).transform(feats["bm25"])])
    else:
        raise ValueError(name)
    m = make_pipeline(StandardScaler(), _lr()) if name in {"rules", "bm25", "rules+bm25"} else _lr()
    m.fit(X[train], y[train])
    return m.predict_proba(X)[:, 1]


# --- evaluation ----------------------------------------------------------------------------------

def routed(t: pd.DataFrame, skip: np.ndarray) -> dict[str, np.ndarray]:
    return {"correct": np.where(skip, t.c_lo, t.c_ar), "usd": np.where(skip, t.usd_lo, t.usd_ar),
            "tok": np.where(skip, t.tok_lo, t.tok_ar)}


def sweep(t: pd.DataFrame, p: np.ndarray) -> pd.DataFrame:
    """Every distinct threshold on these rows (+ never skip): retrieval rate, accuracy, cost."""
    taus = np.unique(np.concatenate([p, [np.inf]]))
    rows = []
    for tau in taus:
        r = routed(t, p >= tau)
        rows.append({"tau": float(tau), "retrieval_rate": float(1 - (p >= tau).mean()),
                     "accuracy": float(r["correct"].mean()), "usd_per_q": float(r["usd"].mean()),
                     "tokens_per_q": float(r["tok"].mean())})
    return pd.DataFrame(rows)


def choose_tau(curve: pd.DataFrame, always_acc: float, slack: float) -> float:
    ok = curve[curve.accuracy >= always_acc - slack - 1e-12]
    return float(ok.sort_values(["retrieval_rate", "tau"]).iloc[0].tau)


def budget_tau(scores: np.ndarray, budget: float) -> float:
    """Threshold that skips the (1 - budget) share of these scores with the highest values."""
    n_skip = int(round((1 - budget) * len(scores)))
    if n_skip == 0:
        return float("inf")
    return float(np.sort(scores)[::-1][n_skip - 1])


def random_accuracy(t: pd.DataFrame, skip_rate: float) -> float:
    return float(t.c_ar.mean() + skip_rate * (t.c_lo - t.c_ar).mean())


def target_label(t: pd.DataFrame, target: str) -> pd.Series:
    if target == "lo_correct":
        return t.c_lo.astype(int)
    return ((t.c_ar == 1) & (t.c_lo == 0)).astype(int)


def skip_score(p: np.ndarray, target: str) -> np.ndarray:
    return p if target == "lo_correct" else 1 - p


def test_rows(cfg: Config, model: str, name: str, target: str, t: pd.DataFrame, p: np.ndarray,
              ms: float, label: pd.Series, prob: np.ndarray) -> list[dict]:
    dev, test = (t.split == "dev").to_numpy(), (t.split == "test").to_numpy()
    td, tt = t[dev], t[test]
    curve = sweep(td, p[dev])
    out = []
    points = [("no_loss", choose_tau(curve, float(td.c_ar.mean()), 0.0)),
              ("loss_1pt", choose_tau(curve, float(td.c_ar.mean()), 0.01)),
              ("budget_80", budget_tau(p[dev], 0.8))]
    for point, tau in points:
        skip = p[test] >= tau
        r = routed(tt, skip)
        strata = tt.dataset.to_numpy()
        B, ci, seed = cfg.eval.bootstrap_samples, cfg.eval.ci, cfg.seed
        da = paired_mean_diff(r["correct"], tt.c_ar.to_numpy(), strata, B, ci, seed)
        du = paired_mean_diff(r["usd"] * 1000, tt.usd_ar.to_numpy() * 1000, strata, B, ci, seed)
        skip_rate = float(skip.mean())
        out.append({
            "model": model, "router": name, "target": target, "point": point, "tau": tau, "n_test": len(tt),
            "retrieval_rate": 1 - skip_rate, "accuracy": float(r["correct"].mean()),
            "always_rag_accuracy": float(tt.c_ar.mean()),
            "acc_diff": da[0], "acc_ci_lo": da[1], "acc_ci_hi": da[2],
            "usd_per_1k_diff": du[0], "usd_ci_lo": du[1], "usd_ci_hi": du[2],
            "usd_saving": 1 - float(r["usd"].mean()) / float(tt.usd_ar.mean()) if tt.usd_ar.mean() else float("nan"),
            "token_saving": 1 - float(r["tok"].mean()) / float(tt.tok_ar.mean()),
            "acc_minus_random": float(r["correct"].mean()) - random_accuracy(tt, skip_rate),
            "test_auc": float(roc_auc_score(label[test], prob[test])) if label[test].nunique() == 2 else float("nan"),
            "router_ms_per_q": ms,
        })
    return out


def budget_rows(model: str, name: str, t: pd.DataFrame, p: np.ndarray, target: str = "lo_correct") -> list[dict]:
    """Out-of-fold predictions: skip the (1 - budget) share with the highest p."""
    order = np.argsort(-p, kind="stable")
    rows = []
    for b in BUDGETS:
        n_skip = int(round((1 - b) * len(t)))
        skip = np.zeros(len(t), bool)
        skip[order[:n_skip]] = True
        r = routed(t, skip)
        rows.append({"model": model, "router": name, "target": target, "retrieval_budget": b,
                     "accuracy": float(r["correct"].mean()), "random_accuracy": random_accuracy(t, 1 - b),
                     "always_rag_accuracy": float(t.c_ar.mean()),
                     "oracle_accuracy": float(np.maximum(t.c_lo, t.c_ar).mean()),
                     "token_saving": 1 - float(r["tok"].mean()) / float(t.tok_ar.mean())})
    return rows


def embed_ms_per_question(cfg: Config, texts: list[str]) -> float:
    """Wall time to embed questions from scratch (no cache), per question, on this machine."""
    import torch
    from transformers import AutoModel, AutoTokenizer

    from src.router_features import EMBED_MODEL
    hf = cfg.path("cache") / "hf"
    tok = AutoTokenizer.from_pretrained(EMBED_MODEL, cache_dir=hf, local_files_only=True)
    model = AutoModel.from_pretrained(EMBED_MODEL, cache_dir=hf, local_files_only=True).eval()
    sample = texts[:200]
    t0 = time.perf_counter()
    with torch.no_grad():
        for q in sample:                                  # one at a time, as a router would see them
            model(**tok([q], return_tensors="pt", truncation=True, max_length=128))
    return (time.perf_counter() - t0) * 1000 / len(sample)


def run(cfg: Config, dry_run: bool, criterion: str = "accuracy") -> dict[str, pd.DataFrame]:
    tables = model_tables(cfg, dry_run, criterion)
    if not tables:
        raise SystemExit("no complete model runs")
    all_q = {q["qid"]: q["question"] for q in load_questions(cfg, dry_run)}
    qids = sorted(all_q)
    emb_all = question_embeddings(cfg, dry_run, qids, [all_q[q] for q in qids])
    emb_index = {q: i for i, q in enumerate(qids)}
    embed_ms = embed_ms_per_question(cfg, [all_q[q] for q in qids])
    log.info("embedding cost: %.1f ms per question (CPU, batch 1)", embed_ms)

    tests, budgets, aucs, curves, selection = [], [], [], [], []
    for model, t in tables.items():
        feats = feature_frames(t)
        emb = emb_all[[emb_index[q] for q in t.qid]]
        train = (t.split == "train").to_numpy()
        folds = StratifiedKFold(5, shuffle=True, random_state=cfg.seed)
        for target in TARGETS:
            label = target_label(t, target)
            tt = t.assign(y=label.to_numpy())
            strat = t.dataset + "_" + label.astype(str)
            for name in ROUTERS:
                t0 = time.perf_counter()
                prob = fit_predict(name, tt, feats, emb, train, cfg.seed)
                ms = (time.perf_counter() - t0) * 1000 / len(t)      # fit + predict, an upper bound
                if name in EMBED_ROUTERS:
                    ms += embed_ms
                score = skip_score(prob, target)
                tests += test_rows(cfg, model, name, target, t, score, ms, label, prob)
                dev = (t.split == "dev").to_numpy()
                c = sweep(t[dev], score[dev])
                c.insert(0, "target", target)
                c.insert(0, "router", name)
                c.insert(0, "model", model)
                curves.append(c)
                oof = np.zeros(len(t))
                for tr_idx, te_idx in folds.split(t, strat):
                    mask = np.zeros(len(t), bool)
                    mask[tr_idx] = True
                    oof[te_idx] = fit_predict(name, tt, feats, emb, mask, cfg.seed)[te_idx]
                budgets += budget_rows(model, name, t, skip_score(oof, target), target)
                # selection CV: test questions excluded entirely
                nt = (t.split != "test").to_numpy()
                tn = t[nt].reset_index(drop=True)
                ttn = tt[nt].reset_index(drop=True)
                fn = {k: v[nt].reset_index(drop=True) for k, v in feats.items()}
                oof_n = np.zeros(len(tn))
                strat_n = tn.dataset + "_" + label[nt].astype(str).to_numpy()
                for tr_idx, te_idx in StratifiedKFold(5, shuffle=True, random_state=cfg.seed).split(tn, strat_n):
                    mask = np.zeros(len(tn), bool)
                    mask[tr_idx] = True
                    oof_n[te_idx] = fit_predict(name, ttn, fn, emb[nt], mask, cfg.seed)[te_idx]
                b = [r for r in budget_rows(model, name, tn, skip_score(oof_n, target), target)
                     if r["retrieval_budget"] == SELECTION_BUDGET][0]
                selection.append({"model": model, "router": name, "target": target,
                                  "acc_minus_always": b["accuracy"] - b["always_rag_accuracy"],
                                  "acc_minus_random": b["accuracy"] - b["random_accuracy"],
                                  "token_saving": b["token_saving"]})
                aucs.append({"model": model, "router": name, "target": target,
                             "cv_auc": float(roc_auc_score(label, oof)) if label.nunique() == 2 else float("nan"),
                             "base_rate": float(label.mean())})
        log.info("%s: done", model)

    sel = pd.DataFrame(selection)
    mean = sel.groupby(["router", "target"]).acc_minus_always.mean().rename("mean_acc_minus_always")
    sel = sel.merge(mean.reset_index(), on=["router", "target"])
    best = mean.idxmax()
    sel["primary"] = (sel.router == best[0]) & (sel.target == best[1])
    log.info("primary router (train+dev CV, %s): %s / %s (mean %+.4f)", criterion, best[0], best[1], mean.max())
    res = {"routers_test": pd.DataFrame(tests), "routers_cv_budget": pd.DataFrame(budgets),
           "routers_selection": sel,
           "routers_auc": pd.DataFrame(aucs), "routers_dev_curve": pd.concat(curves, ignore_index=True)}
    out = cfg.path("results", dry_run) / "summary"
    out.mkdir(parents=True, exist_ok=True)
    for name, df in res.items():
        df.to_csv(out / f"{name}{'' if criterion == 'accuracy' else '_' + criterion}.csv", index=False)
    return res


def main() -> None:
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--criterion", choices=["accuracy", "judge"], default="accuracy")
    args = ap.parse_args()
    res = run(load_config(args.config), args.dry_run, args.criterion)
    t = res["routers_test"]
    cols = ["model", "router", "target", "point", "retrieval_rate", "acc_diff", "acc_ci_lo", "acc_ci_hi",
            "token_saving", "acc_minus_random", "test_auc"]
    print(t[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()


def router_markdown(summary_dir) -> str:
    """Report section from the CSVs this module wrote; empty when they do not exist yet."""
    from pathlib import Path

    from src.report import md_table

    path = Path(summary_dir) / "routers_test.csv"
    if not path.exists():
        return ""
    t = pd.read_csv(path)
    a = pd.read_csv(Path(summary_dir) / "routers_auc.csv")
    def table(df: pd.DataFrame) -> pd.DataFrame:
        sel = df[(df.point == "budget_80") & (df.target == "need")].copy()
        sel["cell"] = [f"{d:+.3f} [{lo:+.3f}, {hi:+.3f}] · {s:.0%}"
                       for d, lo, hi, s in zip(sel.acc_diff, sel.acc_ci_lo, sel.acc_ci_hi, sel.token_saving)]
        return sel.pivot(index="model", columns="router", values="cell").reset_index()

    wide = table(t)
    cols = [("model", "model", None)] + [(r, r, None) for r in ROUTERS if r in wide.columns]
    judge_path = Path(summary_dir) / "routers_test_judge.csv"
    judge_part = []
    if judge_path.exists():
        judge_part = ["Same table with the LLM judge's verdicts as `correct` (labels, training and "
                      "evaluation; `routers_test_judge.csv`, `routers_cv_budget_judge.csv`):", "",
                      md_table(table(pd.read_csv(judge_path)), cols), ""]
    auc = a.pivot_table(index=["model", "target"], columns="router", values="cv_auc").reset_index()
    acols = [("model", "model", None), ("target", "target", None)] + [(r, r, 3) for r in ROUTERS if r in auc.columns]
    ms = t.groupby("router").router_ms_per_q.mean()
    primary_part = []
    sel_path = Path(summary_dir) / "routers_selection.csv"
    if sel_path.exists():
        sel = pd.read_csv(sel_path)
        pr = sel[sel.primary].iloc[0]
        rows = []
        for crit, f in (("accuracy", path), ("judge", judge_path)):
            if not Path(f).exists():
                continue
            d = pd.read_csv(f)
            d = d[(d.router == pr.router) & (d.target == pr.target) & (d.point == "budget_80")]
            for r in d.itertuples():
                rows.append({"model": r.model, "criterion": crit, "retrieval_rate": r.retrieval_rate,
                             "acc": f"{r.acc_diff:+.3f} [{r.acc_ci_lo:+.3f}, {r.acc_ci_hi:+.3f}]",
                             "token_saving": r.token_saving, "usd_saving": r.usd_saving,
                             "vs_random": r.acc_minus_random})
        prim = pd.DataFrame(rows).sort_values(["model", "criterion"])
        ranking = sel.groupby(["router", "target"]).mean_acc_minus_always.first().sort_values(ascending=False)
        primary_part = [
            f"**Primary router: `{pr.router}` / target `{pr.target}`**, chosen before reading test: 5-fold "
            "cross-validation over train + dev only, accuracy at an 80% retrieval budget minus Always-RAG, "
            f"averaged over models (`routers_selection.csv`; best {ranking.iloc[0]:+.4f}, next "
            f"`{ranking.index[1][0]}`/{ranking.index[1][1]} {ranking.iloc[1]:+.4f}). Test results "
            "(threshold = dev quantile for 80% retrieval):", "",
            md_table(prim, [("model", "model", None), ("criterion", "criterion", None),
                            ("retrieval_rate", "retrieval rate", 3), ("acc", "acc − Always-RAG [95% CI]", None),
                            ("token_saving", "token saving", 3), ("usd_saving", "$ saving", 3),
                            ("vs_random", "acc − random skip", 3)]), "",
            "Secondary: every router at the same point (read only as context; not the reported result):", ""]
    return "\n".join([
        "## Routers without an LLM call", "", *primary_part,
        "Trained on train, threshold on dev, reported on test (599 questions per model); no new API calls, "
        "router cost $0. Target `need` = retrieval_needed (skip score 1 − P); `lo_correct` = llm_only correct. "
        "Cells: test accuracy − Always-RAG [paired 95% CI] · share of tokens saved, at the `budget_80` point "
        "(threshold = the dev score quantile that retrieves for 80% of dev questions). All operating points, "
        "both targets and the random baseline: `routers_test.csv`; 5-fold budget curves: `routers_cv_budget.csv`.", "",
        md_table(wide, cols), "",
        *judge_part,
        "Router compute per question (ms, CPU; fit + predict over all questions, plus embedding at batch 1 "
        "for embedding routers): " + ", ".join(f"{r} {ms[r]:.1f}" for r in ROUTERS if r in ms.index) + ".", "",
        "5-fold cross-validated ROC-AUC of the router's probability for its target:", "",
        md_table(auc, acols), "",
        "Caveat: several routers are compared on the same test set; choose the router on dev or cross-"
        "validation before reading its test row, and treat single significant rows with care.", ""])
