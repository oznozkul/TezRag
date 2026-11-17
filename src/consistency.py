"""How stable are the per-question outcomes when the same prompt is sent again?

    python -m src.consistency [--dry-run]       (after src.repeat_runs; evaluate also calls it)

For every model with repeats (src/repeat_runs.py), each question has R runs of llm_only and of
always_rag: the original final record plus the repeats. Run r of the label pairs llm_only run r with
always_rag run r. Reported, on the repeated split:

  per system   share of questions whose correctness is the same in every run; Fleiss' kappa over runs
  labels       share whose outcome label (both_ok, rag_hurts, retrieval_needed, both_fail) is the same in
               every run; how often each original label recurs in the repeats
  aggregates   accuracy, Always-RAG gain, realistic-oracle accuracy and saving per run (do the headline
               numbers move?)
  router       the primary router's test accuracy minus Always-RAG, computed with each run's answers
               (the router's decisions do not change; only the answers it routes to do)

Correctness = token-bounded accuracy (answer set `all`). Writes consistency_*.csv.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import Config, load_config
from src.data import load_questions
from src.dispatch import discover_run_dirs, load_run_dir, model_of
from src.evaluate import scored
from src.records import error_kind, final_records
from src.routers import outcome_label

SYSTEMS = ("llm_only", "always_rag")


def fleiss_kappa(matrix: np.ndarray) -> float:
    """matrix: items x runs, binary. Fleiss' kappa for two categories."""
    n_runs = matrix.shape[1]
    ones = matrix.sum(axis=1)
    counts = np.stack([n_runs - ones, ones], axis=1).astype(float)
    p_j = counts.sum(axis=0) / counts.sum()
    p_i = ((counts ** 2).sum(axis=1) - n_runs) / (n_runs * (n_runs - 1))
    p_bar, p_e = p_i.mean(), (p_j ** 2).sum()
    return float((p_bar - p_e) / (1 - p_e)) if p_e < 1 else float("nan")


def run_matrix(cfg: Config, dry_run: bool) -> dict[str, dict]:
    """model -> {"qids", "dataset", "correct": {system: items x runs (original first)}, "n_runs"}."""
    questions = {q["qid"]: q for q in load_questions(cfg, dry_run)}
    out = {}
    for directory in discover_run_dirs(cfg.path("results", dry_run)):
        recs, _ = load_run_dir(directory)
        model = model_of(recs)
        rep_root = directory.parent / "repeats"
        reps = sorted(rep_root.glob("rep*")) if rep_root.exists() else []
        if model is None or not reps:
            continue
        rep_recs = {s: [final_records(r / f"{s}.jsonl")[0] if (r / f"{s}.jsonl").exists() else {}
                        for r in reps] for s in SYSTEMS}
        qids = sorted(q for q in questions
                      if all(q in rr for s in SYSTEMS for rr in rep_recs[s])
                      and all(error_kind(run.get(q, {"error": "missing"})) != "flagged"
                              for s in SYSTEMS for run in [recs[s]] + rep_recs[s]))
        if not qids:
            continue
        correct = {}
        for s in SYSTEMS:
            runs = [recs[s]] + rep_recs[s]
            correct[s] = np.array([[bool(scored(cfg, questions[q], run[q], "all")["correct"]) for run in runs]
                                   for q in qids])
        out[model] = {"qids": qids, "dataset": [questions[q]["dataset"] for q in qids],
                      "correct": correct, "n_runs": 1 + len(reps)}
    return out


def tables(cfg: Config, dry_run: bool) -> dict[str, pd.DataFrame]:
    mats = run_matrix(cfg, dry_run)
    sys_rows, label_rows, agg_rows, rec_rows = [], [], [], []
    for model, m in mats.items():
        lo, ar = m["correct"]["llm_only"], m["correct"]["always_rag"]
        for s, mat in (("llm_only", lo), ("always_rag", ar)):
            sys_rows.append({"model": model, "system": s, "n": len(mat), "runs": mat.shape[1],
                             "same_in_all_runs": float((mat.all(1) | (~mat).all(1)).mean()),
                             "fleiss_kappa": fleiss_kappa(mat.astype(int)),
                             "accuracy_min": float(mat.mean(0).min()), "accuracy_max": float(mat.mean(0).max())})
        labels = np.array([[outcome_label(lo[i, r], ar[i, r]) for r in range(lo.shape[1])] for i in range(len(lo))])
        same = (labels == labels[:, [0]]).all(1)
        label_rows.append({"model": model, "label": "ALL", "n_original": len(labels),
                           "same_in_all_runs": float(same.mean()), "recurs_in_repeats": float("nan")})
        for lab in ("both_ok", "rag_hurts", "retrieval_needed", "both_fail"):
            orig = labels[:, 0] == lab
            if orig.any():
                label_rows.append({"model": model, "label": lab, "n_original": int(orig.sum()),
                                   "same_in_all_runs": float(same[orig].mean()),
                                   "recurs_in_repeats": float((labels[orig, 1:] == lab).mean())})
        for r in range(lo.shape[1]):
            oracle = lo[:, r] | ar[:, r]
            agg_rows.append({"model": model, "run": "original" if r == 0 else f"rep{r}",
                             "llm_only": float(lo[:, r].mean()), "always_rag": float(ar[:, r].mean()),
                             "rag_gain": float(ar[:, r].mean() - lo[:, r].mean()),
                             "oracle_realistic": float(oracle.mean()),
                             "skip_share_realistic": float(lo[:, r].mean()),
                             "rag_hurts_share": float((lo[:, r] & ~ar[:, r]).mean()),
                             "both_fail_share": float((~lo[:, r] & ~ar[:, r]).mean())})
        rec_rows += router_rows(cfg, dry_run, model, m)
    return {"consistency_systems": pd.DataFrame(sys_rows), "consistency_labels": pd.DataFrame(label_rows),
            "consistency_aggregates": pd.DataFrame(agg_rows), "consistency_router": pd.DataFrame(rec_rows)}


def router_rows(cfg: Config, dry_run: bool, model: str, m: dict) -> list[dict]:
    """Primary router's test decisions applied to each run's answers."""
    sel_path = cfg.path("results", dry_run) / "summary" / "routers_selection.csv"
    if not sel_path.exists():
        return []
    from src.learned_routers import (budget_tau, feature_frames, fit_predict, model_tables, skip_score,
                                     target_label)
    from src.router_features import question_embeddings
    sel = pd.read_csv(sel_path)
    pr = sel[sel.primary].iloc[0]
    t = model_tables(cfg, dry_run).get(model)
    if t is None:
        return []
    qids_all = sorted(t.qid)
    texts = dict(zip(t.qid, t.question))
    emb_all = question_embeddings(cfg, dry_run, qids_all, [texts[q] for q in qids_all])
    idx = {q: i for i, q in enumerate(qids_all)}
    emb = emb_all[[idx[q] for q in t.qid]]
    label = target_label(t, pr.target)
    prob = fit_predict(pr.router, t.assign(y=label.to_numpy()), feature_frames(t), emb,
                       (t.split == "train").to_numpy(), cfg.seed)
    score = skip_score(prob, pr.target)
    dev = (t.split == "dev").to_numpy()
    tau = budget_tau(score[dev], 0.8)
    skip = dict(zip(t.qid, score >= tau))
    keep = [i for i, q in enumerate(m["qids"]) if q in skip]
    sk = np.array([skip[m["qids"][i]] for i in keep])
    lo, ar = m["correct"]["llm_only"][keep], m["correct"]["always_rag"][keep]
    rows = []
    for r in range(lo.shape[1]):
        routed = np.where(sk, lo[:, r], ar[:, r])
        rows.append({"model": model, "router": f"{pr.router}/{pr.target}", "run": "original" if r == 0 else f"rep{r}",
                     "n": len(keep), "retrieval_rate": float(1 - sk.mean()),
                     "acc_minus_always": float(routed.mean() - ar[:, r].mean())})
    return rows


def consistency_markdown(cfg: Config, dry_run: bool, out: Path) -> str:
    from src.report import md_table

    t = tables(cfg, dry_run)
    if t["consistency_systems"].empty:
        return ""
    for name, df in t.items():
        df.to_csv(out / f"{name}.csv", index=False)
    s, lab, agg, rr = (t[k] for k in ("consistency_systems", "consistency_labels",
                                      "consistency_aggregates", "consistency_router"))
    L = ["## Label consistency (repeated runs)", "",
         f"Same prompts sent again ({int(s.runs.max())} runs per question incl. the original, split as repeated). "
         "Differences come from the model's own sampling; retrieval is identical (cached passages, checked).", "",
         md_table(s, [("model", "model", None), ("system", "system", None), ("n", "n", None), ("runs", "runs", None),
                      ("same_in_all_runs", "same correctness in all runs", 3), ("fleiss_kappa", "Fleiss κ", 3),
                      ("accuracy_min", "acc min", 3), ("accuracy_max", "acc max", 3)]), "",
         "Outcome labels: share identical in every run, and how often an original label recurs in the repeats:", "",
         md_table(lab, [("model", "model", None), ("label", "original label", None), ("n_original", "n", None),
                        ("same_in_all_runs", "same in all runs", 3), ("recurs_in_repeats", "recurs in repeats", 3)]), "",
         "Headline numbers per run:", "",
         md_table(agg, [("model", "model", None), ("run", "run", None), ("llm_only", "llm_only", 3),
                        ("always_rag", "always_rag", 3), ("rag_gain", "RAG gain", 3),
                        ("oracle_realistic", "oracle", 3), ("rag_hurts_share", "rag_hurts", 3),
                        ("both_fail_share", "both_fail", 3)]), ""]
    if not rr.empty:
        L += ["Primary router (decisions fixed) applied to each run's answers:", "",
              md_table(rr, [("model", "model", None), ("router", "router", None), ("run", "run", None),
                            ("n", "n", None), ("retrieval_rate", "retrieval rate", 3),
                            ("acc_minus_always", "acc − Always-RAG", 3)]), ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    cfg = load_config(args.config)
    out = cfg.path("results", args.dry_run) / "summary"
    out.mkdir(parents=True, exist_ok=True)
    print(consistency_markdown(cfg, args.dry_run, out) or "no repeats yet")


if __name__ == "__main__":
    main()
