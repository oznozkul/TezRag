"""Hand-labelled sample that validates the automatic correctness criteria.

    python -m src.annotation            # write the sheet once (refuses to overwrite)
    python -m src.annotation --report   # after labelling: agreement of accuracy and judge with humans
    python -m src.annotation --review claude-opus-5-5   # review sheet pre-filled with a model's labels

Sample: 200 (answer model, system, question) items from the complete runs, stratified by dataset
(6) x token-bounded accuracy (correct / wrong), about 17 per cell, seed 42. Stratifying on accuracy
gives enough of both outcomes to estimate how often accuracy misses a correct answer and how often
it accepts a wrong one. Rates are reweighted to the population with the cell sizes in the key file.

Files (results/annotation/):
  sheet.csv   what the annotator sees: item id, dataset, question, gold answers, model answer, and
              empty `human_label` / `note` columns. The model, the system and the automatic
              verdicts are hidden so they cannot anchor the label. Semicolon-separated, UTF-8 with
              BOM, so it opens directly in Excel with a Turkish locale.
  key.csv     item id -> answer model, system, qid, accuracy verdict, cell size (write-once)

Labels: 1 = correct, 0 = wrong, ? = unsure (left out of agreement). Grade against the gold answers;
if the gold answer is outdated, label against the gold and write `outdated` in the note.

Labellers: `human` is the `human_label` column of sheet.csv. A model can label the same items into
labels_<name>.csv (columns item_id;label;note); it is reported under its own name and never as a
human label. When both exist, the model labeller's agreement with the human labels is reported too.

Review (LLM pre-annotation + author verification): review.csv shows each item with a model's
suggested label. The author writes `ok` (accept), `1` / `0` (override) or `?` in `verdict`; empty
rows are not reviewed. Reviewed rows are reported as the labeller `author_verified`, never as `human`:
the author saw the suggestion, so these labels are not independent of it. Items whose suggestion
disagrees with accuracy or the judge, or is `?`, are listed first (`check_first` = 1).
"""
from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

import pandas as pd

from src.config import Config, load_config
from src.data import load_questions
from src.dispatch import discover_run_dirs, load_run_dir, model_of
from src.evaluate import scored
from src.records import error_kind

N_ITEMS = 200
SYSTEMS = ("llm_only", "always_rag")
VERIFIED = "author_verified"
REVIEW_COLUMNS = ["item_id", "check_first", "dataset", "question", "gold_answers", "model_answer",
                  "suggested_label", "suggested_note", "verdict", "note"]
SHEET_COLUMNS = ["item_id", "dataset", "question", "gold_answers", "model_answer", "human_label", "note"]


def annotation_dir(cfg: Config, dry_run: bool) -> Path:
    return cfg.path("results", dry_run) / "annotation"


def population(cfg: Config, dry_run: bool) -> list[dict]:
    """Every successful final answer of every complete run, with its accuracy verdict."""
    questions = {q["qid"]: q for q in load_questions(cfg, dry_run)}
    rows = []
    for directory in discover_run_dirs(cfg.path("results", dry_run)):
        recs, _ = load_run_dir(directory)
        model = model_of(recs)
        if model is None or any(qid not in recs[s] for s in recs for qid in questions):
            continue
        for system in SYSTEMS:
            for qid, rec in sorted(recs[system].items()):
                if qid not in questions or error_kind(rec) is not None:
                    continue
                q = questions[qid]
                rows.append({"answer_model": model, "system": system, "qid": qid, "dataset": q["dataset"],
                             "question": q["question"], "golds": q["answers"],
                             "primary": q.get("answers_primary") or [],
                             "prediction": " / ".join((rec["prediction"] or "").split("\n")).strip(" /"),
                             "accuracy_correct": bool(scored(cfg, q, rec, "all")["correct"])})
    return rows


def stratified_sample(rows: list[dict], n: int, seed: int) -> list[dict]:
    """About n/cells items per (dataset, accuracy verdict) cell; each item carries its cell size."""
    cells = defaultdict(list)
    for r in rows:
        cells[(r["dataset"], r["accuracy_correct"])].append(r)
    keys = sorted(cells, key=str)
    base, extra = divmod(n, len(keys))
    rng = random.Random(f"{seed}:annotation")
    out = []
    for i, key in enumerate(keys):
        take = min(len(cells[key]), base + (1 if i < extra else 0))
        for r in rng.sample(cells[key], take):
            out.append({**r, "cell_size": len(cells[key]), "cell_sampled": take})
    rng.shuffle(out)
    for i, r in enumerate(out, 1):
        r["item_id"] = f"A{i:03d}"
    return out


def gold_text(r: dict) -> str:
    seen = []
    for g in list(r["primary"]) + list(r["golds"]):
        if g not in seen:
            seen.append(g)
    return " | ".join(seen[:10])


def write_sheet(cfg: Config, dry_run: bool) -> Path:
    out = annotation_dir(cfg, dry_run)
    sheet, key = out / "sheet.csv", out / "key.csv"
    if sheet.exists() or key.exists():
        raise SystemExit(f"{out} already has a sheet; it is write-once (labels may be in it)")
    sample = stratified_sample(population(cfg, dry_run), N_ITEMS, cfg.seed)
    out.mkdir(parents=True, exist_ok=True)
    with open(sheet, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(SHEET_COLUMNS)
        for r in sample:
            w.writerow([r["item_id"], r["dataset"], r["question"], gold_text(r), r["prediction"], "", ""])
    pd.DataFrame([{k: r[k] for k in ("item_id", "answer_model", "system", "qid", "dataset",
                                     "accuracy_correct", "cell_size", "cell_sampled")} for r in sample]
                 ).to_csv(key, index=False)
    return sheet


def labellers(cfg: Config, dry_run: bool) -> list[str]:
    """`human` first (if the sheet exists), `author_verified` (if review.csv exists), then every
    labels_<name>.csv."""
    out = annotation_dir(cfg, dry_run)
    names = ["human"] if (out / "sheet.csv").exists() else []
    names += [VERIFIED] if (out / "review.csv").exists() else []
    return names + sorted(p.stem[len("labels_"):] for p in out.glob("labels_*.csv"))


def write_review(cfg: Config, dry_run: bool, source: str, verdicts: dict) -> Path:
    """review.csv: sheet items with `source`'s suggested label; disagreements with accuracy or the
    judge first. Write-once, like the sheet."""
    out = annotation_dir(cfg, dry_run)
    path = out / "review.csv"
    if path.exists():
        raise SystemExit(f"{path} exists; it is write-once (verdicts may be in it)")
    sheet = pd.read_csv(out / "sheet.csv", sep=";", encoding="utf-8-sig", dtype=str).fillna("")
    sug = pd.read_csv(out / f"labels_{source}.csv", sep=";", encoding="utf-8-sig", dtype=str).fillna("")
    key = pd.read_csv(out / "key.csv")
    d = sheet.merge(sug.rename(columns={"label": "suggested_label", "note": "suggested_note"}),
                    on="item_id", how="left").merge(key[["item_id", "answer_model", "system", "qid",
                                                         "accuracy_correct"]], on="item_id")
    d["suggested_label"] = d.suggested_label.fillna("").str.strip()
    if (d.suggested_label == "").any():
        raise SystemExit(f"labels_{source}.csv does not cover every sheet item")
    judge = [verdicts.get((m, s, q)) for m, s, q in zip(d.answer_model, d.system, d.qid)]
    sugg_ok = d.suggested_label == "1"
    acc_ok = d.accuracy_correct.astype(bool)
    judge_dis = pd.Series([j in ("correct", "incorrect") and (j == "correct") != g
                           for j, g in zip(judge, sugg_ok)], index=d.index)
    d["check_first"] = ((d.suggested_label == "?") | (sugg_ok != acc_ok) | judge_dis).astype(int)
    d["verdict"], d["note"] = "", ""
    d = d.sort_values(["check_first", "item_id"], ascending=[False, True])
    d[REVIEW_COLUMNS].to_csv(path, sep=";", index=False, encoding="utf-8-sig")
    return path


def review_labels(path: Path) -> pd.DataFrame:
    """item_id, label (0/1/?) and note from review.csv; `ok` takes the suggestion (an accepted `?`
    stays `?`), empty verdicts are left out."""
    r = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str).fillna("")
    v = r.verdict.str.strip().str.lower()
    bad = r[~v.isin(["", "ok", "0", "1", "?"])]
    if len(bad):
        raise ValueError(f"unknown verdicts in {path}: {sorted(set(bad.verdict))[:5]}; use ok, 1, 0 or ?")
    label = v.where(v != "ok", r.suggested_label.str.strip())
    out = pd.DataFrame({"item_id": r.item_id, "label": label, "note": r.note,
                        "changed": (v != "ok") & (v != "")})
    return out[v != ""]


def review_summary(cfg: Config, dry_run: bool) -> dict | None:
    path = annotation_dir(cfg, dry_run) / "review.csv"
    if not path.exists():
        return None
    r = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str).fillna("")
    lab = review_labels(path)
    return {"items": len(r), "reviewed": len(lab), "changed": int(lab.changed.sum()),
            "check_first": int((r.check_first == "1").sum()),
            "check_first_reviewed": int(r.loc[r.item_id.isin(lab.item_id), "check_first"].eq("1").sum())}


def read_labels(cfg: Config, dry_run: bool, labeller: str = "human") -> pd.DataFrame:
    """Items labelled 1 or 0 by `labeller`, joined with the key; `ref_correct` is the label.
    Empty when the labeller has no 1/0 labels yet."""
    out = annotation_dir(cfg, dry_run)
    key = out / "key.csv"
    path = out / {"human": "sheet.csv", VERIFIED: "review.csv"}.get(labeller, f"labels_{labeller}.csv")
    col = "human_label" if labeller == "human" else "label"
    if not path.exists() or not key.exists():
        return pd.DataFrame()
    s = (review_labels(path) if labeller == VERIFIED
         else pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str).fillna(""))
    s[col] = s[col].str.strip()
    bad = s[~s[col].isin(["", "0", "1", "?"])]
    if len(bad):
        raise ValueError(f"unknown labels in {path}: {sorted(set(bad[col]))[:5]}; use 1, 0 or ?")
    s = s[s[col].isin(["0", "1"])]
    if s.empty:
        return pd.DataFrame()
    d = s[["item_id", col, "note"]].merge(pd.read_csv(key), on="item_id")
    d["ref_correct"] = d[col] == "1"
    d["labeller"] = labeller
    return d


def agreement(labels: pd.DataFrame, verdicts: dict, judge_model: str | None = None,
              other_labels: dict[str, dict[str, bool]] | None = None) -> pd.DataFrame:
    """Accuracy, judge and (optionally) other labellers against one labeller's labels, raw and
    reweighted to the population. other_labels: name -> {item_id: correct}."""
    if labels.empty:
        return pd.DataFrame()
    d = labels.copy()
    d["weight"] = d.cell_size / d.cell_sampled
    d["judge_verdict"] = [verdicts.get((m, s, q)) for m, s, q in zip(d.answer_model, d.system, d.qid)]
    rows = []
    criteria = [("accuracy", d.accuracy_correct.astype(bool))]
    judged = d.judge_verdict.isin(["correct", "incorrect"])
    masks = {"accuracy": pd.Series(True, index=d.index)}
    if judged.any():
        criteria.append(("judge", d.judge_verdict == "correct"))
        masks["judge"] = judged
        if judge_model:
            # the judge may grade its own model's answers more leniently
            own = d.answer_model == judge_model
            for name, m in (("judge: own model's answers", judged & own),
                            ("judge: other models' answers", judged & ~own)):
                if m.any():
                    criteria.append((name, d.judge_verdict == "correct"))
                    masks[name] = m
    for name, lab in (other_labels or {}).items():
        has = d.item_id.isin(list(lab))
        if has.any():
            criteria.append((f"labels: {name}", d.item_id.map(lab).fillna(False).astype(bool)))
            masks[f"labels: {name}"] = has
    for name, pred in criteria:
        m = masks[name]
        h, p, w = d.ref_correct[m], pred[m], d.weight[m]
        agree = (h == p)
        fn = h & ~p        # human says correct, criterion says wrong
        fp = ~h & p        # human says wrong, criterion says correct
        po = float(agree.mean())
        pe = float(h.mean() * p.mean() + (1 - h.mean()) * (1 - p.mean()))
        rows.append({
            "reference": d.labeller.iloc[0], "criterion": name, "n_labelled": int(m.sum()),
            "agreement": po, "cohen_kappa": (po - pe) / (1 - pe) if pe < 1 else float("nan"),
            "missed_correct": int(fn.sum()), "accepted_wrong": int(fp.sum()),
            "weighted_agreement": float((agree * w).sum() / w.sum()),
            "weighted_missed_correct_rate": float((fn * w).sum() / (h * w).sum()) if h.any() else float("nan"),
            "weighted_accepted_wrong_rate": float((fp * w).sum() / (~h * w).sum()) if (~h).any() else float("nan"),
            "reference_correct_rate_weighted": float((h * w).sum() / w.sum()),
            "criterion_correct_rate_weighted": float((p * w).sum() / w.sum()),
        })
    return pd.DataFrame(rows)


def all_agreement(cfg: Config, dry_run: bool, verdicts: dict) -> pd.DataFrame:
    """Agreement tables for every labeller; model labellers are also compared with the human labels."""
    labs = {name: read_labels(cfg, dry_run, name) for name in labellers(cfg, dry_run)}
    labs = {k: v for k, v in labs.items() if not v.empty}
    parts = []
    for name, d in labs.items():
        others = ({o: dict(zip(v.item_id, v.ref_correct)) for o, v in labs.items() if o != name}
                  if name in ("human", VERIFIED) else None)
        parts.append(agreement(d, verdicts, cfg.judge.model if cfg.judge else None, others))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def agreement_markdown(table: pd.DataFrame, n_sheet: int) -> str:
    from src.report import md_table

    if table.empty:
        return ("## Correctness criteria vs. reference labels\n\nNo labelled items yet "
                "(`results/annotation/sheet.csv`).\n")
    cols = [("reference", "reference labels", None), ("criterion", "criterion", None), ("n_labelled", "n", None), ("agreement", "agreement", 3),
            ("cohen_kappa", "kappa", 3), ("missed_correct", "missed correct", None),
            ("accepted_wrong", "accepted wrong", None),
            ("weighted_missed_correct_rate", "missed-correct rate (w)", 3),
            ("weighted_accepted_wrong_rate", "accepted-wrong rate (w)", 3),
            ("reference_correct_rate_weighted", "reference correct (w)", 3),
            ("criterion_correct_rate_weighted", "criterion correct (w)", 3)]
    return "\n".join([
        "## Correctness criteria vs. reference labels", "",
        f"Sheet of {n_sheet} items; items labelled `?` are left out. `human` = hand labels made without "
        "any suggestion; `author_verified` = a model's suggested labels checked one by one by the author, "
        "who saw the suggestion (so its agreement with that model is not independent); any other "
        "reference is a model that labelled the same items and is not a human check. The sample is "
        "stratified by dataset x accuracy verdict; (w) columns reweight each cell to its share of all "
        "answers. `missed correct` = reference correct, criterion wrong; `accepted wrong` = the reverse.", "",
        md_table(table, cols), ""])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--review", metavar="LABELLER", help="write review.csv pre-filled with labels_<LABELLER>.csv")
    args = ap.parse_args()
    cfg = load_config(args.config)
    if args.review:
        from src.judge import load_verdicts
        print(f"wrote {write_review(cfg, args.dry_run, args.review, load_verdicts(cfg, args.dry_run))}")
        return
    if args.report:
        from src.judge import load_verdicts
        t = all_agreement(cfg, args.dry_run, load_verdicts(cfg, args.dry_run))
        print(t.to_string(index=False) if not t.empty else "no labelled items yet")
        return
    print(f"wrote {write_sheet(cfg, args.dry_run)}")


if __name__ == "__main__":
    main()
