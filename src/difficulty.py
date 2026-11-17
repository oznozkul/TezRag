"""Question difficulty from how many *other* models answer it without retrieval.

For model m and question q, difficulty = share of the other models whose llm_only answer to q is
correct (leave-one-model-out). Using m's own answer would be circular: on "easy" questions m's
llm_only accuracy would be high by construction, and the retrieval gain there would look negative
because of selection, not because retrieval hurts.

  very_hard  no other model is correct
  hard       0 < share <= 0.5
  medium     0.5 < share < 1
  easy       every other model is correct

The tier uses gold answers and other models' outputs, so it is an analysis variable, not a router
feature. A router has to predict it from the question text.

Outputs (results/summary/):
  difficulty.csv             model x tier x system: n, accuracy, cost, retrieval rate; YES rate of the
                             llm_decision call; paired retrieval gain (always_rag - llm_only) with CI
  difficulty_by_dataset.csv  questions per dataset by how many models answer them without retrieval
  difficulty_questions.csv   per (model, qid): other models correct, other models, tier
"""
from __future__ import annotations

import pandas as pd

from src.bootstrap import paired_mean_diff
from src.config import Config

TIERS = ("very_hard", "hard", "medium", "easy")
SYSTEMS = ("llm_only", "always_rag", "oracle_optimistic", "oracle_realistic", "llm_decision_router")
MIN_OTHER_MODELS = 2


def tier_of(others_correct: int, n_others: int) -> str:
    if n_others <= 0:
        raise ValueError("difficulty needs at least one other model")
    share = others_correct / n_others
    if share == 0:
        return "very_hard"
    if share <= 0.5:
        return "hard"
    if share < 1:
        return "medium"
    return "easy"


def llm_only_correct(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """qid x model -> llm_only correct (NaN where the model has no record for that question)."""
    cols = {m: f[f.system == "llm_only"].set_index("qid").correct.astype(float) for m, f in frames.items()}
    return pd.DataFrame(cols)


def question_tiers(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Leave-one-model-out tier per (model, qid). Empty when fewer than MIN_OTHER_MODELS others exist."""
    wide = llm_only_correct(frames)
    rows = []
    for m in wide.columns:
        others = wide.drop(columns=m)
        n_others = others.notna().sum(axis=1)
        k = others.sum(axis=1)
        ok = wide[m].notna() & (n_others >= MIN_OTHER_MODELS)
        for qid in wide.index[ok]:
            rows.append({"model": m, "qid": qid, "others_correct": int(k[qid]),
                         "n_other_models": int(n_others[qid]),
                         "tier": tier_of(int(k[qid]), int(n_others[qid]))})
    return pd.DataFrame(rows, columns=["model", "qid", "others_correct", "n_other_models", "tier"])


def difficulty_table(frames: dict[str, pd.DataFrame], tiers: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    if tiers.empty:
        return pd.DataFrame()
    parts = []
    for m, f in frames.items():
        t = tiers[tiers.model == m][["qid", "tier"]]
        parts.append(f.merge(t, on="qid").assign(model=m))
    df = pd.concat(parts, ignore_index=True)
    B, ci, seed = cfg.eval.bootstrap_samples, cfg.eval.ci, cfg.seed
    out = []
    for model in list(frames) + ["ALL"]:
        dm = df if model == "ALL" else df[df.model == model]
        for tier in TIERS:
            d = dm[dm.tier == tier]
            if d.empty:
                continue
            lo = d[d.system == "llm_only"].set_index(["model", "qid"]).sort_index()
            ar = d[d.system == "always_rag"].set_index(["model", "qid"]).sort_index()
            dec = d[d.system == "llm_decision_router"]
            strata = lo.index.get_level_values("model").to_numpy() if model == "ALL" else None
            gain = paired_mean_diff(ar.correct.astype(float).to_numpy(), lo.correct.astype(float).to_numpy(),
                                    strata, B, ci, seed)
            base = {"model": model, "tier": tier, "n": len(lo),
                    "decision_yes_rate": float((dec.decision == "yes").mean()),
                    "retrieval_gain": gain[0], "gain_ci_lo": gain[1], "gain_ci_hi": gain[2]}
            for s in SYSTEMS:
                g = d[d.system == s]
                out.append({**base, "system": s, "accuracy": float(g.correct.mean()),
                            "usd_per_q": float(g.total_usd.mean()),
                            "input_tokens": float(g.billed_input_tokens.mean()),
                            "retrieval_rate": float(g.retrieval_calls.mean())})
    return pd.DataFrame(out)


def dataset_counts(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Questions answered by every model: how many models answer each one without retrieval."""
    wide = llm_only_correct(frames).dropna()
    if wide.shape[1] < MIN_OTHER_MODELS + 1:
        return pd.DataFrame()
    ds = pd.concat([f[f.system == "llm_only"].set_index("qid").dataset for f in frames.values()])
    ds = ds[~ds.index.duplicated()]
    k = wide.sum(axis=1).astype(int).rename("models_correct")
    t = pd.crosstab(ds.loc[k.index], k)
    t.loc["ALL"] = t.sum()
    t.columns = [f"{c}/{wide.shape[1]}" for c in t.columns]
    return t.reset_index(names="dataset")


def difficulty_markdown(table: pd.DataFrame, counts: pd.DataFrame) -> str:
    from src.report import md_table

    if table.empty:
        return ("## Difficulty (cross-model)\n\nNeeds full runs of at least "
                f"{MIN_OTHER_MODELS + 1} models; not available here.\n")
    L = ["## Difficulty (cross-model)", "",
         "Tier of a question for model m = share of the *other* models whose llm_only answer is correct "
         "(very_hard 0, hard <= 0.5, medium < 1, easy = all). m's own answer is left out, otherwise the "
         "tiers would be circular. `gain` = always_rag − llm_only accuracy, paired 95% CI (pooled rows "
         "stratified by model). `YES rate` = share of llm_decision calls that say no retrieval is needed. "
         "Tiers use gold answers: analysis only, not a router feature.", ""]
    w = table.pivot_table(index=["model", "tier", "n", "retrieval_gain", "gain_ci_lo", "gain_ci_hi",
                                 "decision_yes_rate"], columns="system", values="accuracy",
                          sort=False).reset_index()
    w["tier"] = pd.Categorical(w.tier, TIERS)
    order = {m: i for i, m in enumerate(dict.fromkeys(table.model))}
    w = w.sort_values(["model", "tier"], key=lambda c: c.map(order) if c.name == "model" else c)
    cols = [("model", "model", None), ("tier", "tier", None), ("n", "n", None),
            ("llm_only", "llm_only", 3), ("always_rag", "always_rag", 3), ("oracle_realistic", "oracle", 3),
            ("llm_decision_router", "llm_decision", 3), ("retrieval_gain", "gain", 3),
            ("gain_ci_lo", "CI lo", 3), ("gain_ci_hi", "CI hi", 3), ("decision_yes_rate", "YES rate", 3)]
    L += [md_table(w, cols), ""]
    if not counts.empty:
        L += ["Questions per dataset by how many models answer them without retrieval "
              "(questions in every model's comparison set):", "",
              md_table(counts, [(c, c, None) for c in counts.columns]), ""]
    return "\n".join(L)
