"""Per-question record of whether a model call exists, and how the decision router sent it.

"Sent" means a call was logged. Both the no-retrieval path and the retrieval path call the model;
the flag that varies is `route` (llm_only or always_rag), not whether a model was called.
A question rejected by the provider filter twice is sent, and `in_comparison` is false.
"""
from __future__ import annotations

from pathlib import Path

from src.records import error_kind, final_records
from src.systems import SYSTEMS

META_FIELDS = ("hop_type", "hotpot_level", "hotpot_type", "musique_hops", "wiki_type",
               "s_pop", "pop_tertile")


def load_run_dir(directory: Path) -> tuple[dict, dict]:
    """system -> {qid: final record}, system -> {qid: call count}. Missing files are empty."""
    recs, calls = {}, {}
    for system in SYSTEMS:
        path = directory / f"{system}.jsonl"
        recs[system], calls[system] = final_records(path) if path.exists() else ({}, {})
    return recs, calls


def discover_run_dirs(root: Path) -> list[Path]:
    """Directories that hold `<system>.jsonl`. Legacy OpenAI logs stay in `<root>/raw`."""
    found = []
    legacy = root / "raw"
    if (legacy / "llm_only.jsonl").exists():
        found.append(legacy)
    models = root / "models"
    if models.is_dir():
        for d in sorted(p for p in models.iterdir() if p.is_dir()):
            raw = d / "raw"
            if (raw / "llm_only.jsonl").exists():
                found.append(raw)
    return found


def model_of(recs: dict) -> str | None:
    for system in SYSTEMS:
        for rec in recs[system].values():
            return rec["model"]
    return None


def excluded_qids(questions: dict, recs: dict) -> dict[str, list[str]]:
    """qid -> systems whose final record was rejected by the provider filter."""
    out = {}
    for qid in questions:
        flagged = [s for s in SYSTEMS if qid in recs[s] and error_kind(recs[s][qid]) == "flagged"]
        if flagged:
            out[qid] = flagged
    return out


def _status(rec: dict | None) -> str:
    if rec is None:
        return "not_sent"
    kind = error_kind(rec)
    return "ok" if kind is None else kind


def _route(system: str, rec: dict | None) -> str:
    if rec is None:
        return ""
    if system == "llm_decision":
        return rec.get("router_route") or ""
    return system


def dispatch_rows(questions: dict, recs: dict, meta: dict[str, dict], model: str,
                  excluded: set[str]) -> list[dict]:
    rows = []
    for qid in sorted(questions):
        q = questions[qid]
        m = meta[qid]
        complete = all(qid in recs[s] for s in SYSTEMS)
        for system in SYSTEMS:
            rec = recs[system].get(qid)
            rows.append({
                "qid": qid, "dataset": q["dataset"], "split": q["split"],
                **{k: m.get(k) for k in META_FIELDS},
                "model": model, "system": system,
                "sent": rec is not None, "status": _status(rec), "route": _route(system, rec),
                "in_comparison": complete and qid not in excluded,
            })
    return rows
