"""Read the prepared questions joined with their split (used by every later stage)."""
from __future__ import annotations

from src.config import Config
from src.io_utils import read_jsonl


def load_questions(cfg: Config, dry_run: bool = False) -> list[dict]:
    q_path = cfg.path("processed", dry_run) / "questions.jsonl"
    s_path = cfg.path("splits", dry_run) / "split.jsonl"
    if not q_path.exists() or not s_path.exists():
        hint = " --dry-run" if dry_run else ""
        raise FileNotFoundError(f"{q_path} / {s_path} missing; run `python -m src.prepare_data{hint}`")
    split = {r["qid"]: r["split"] for r in read_jsonl(s_path)}
    rows = []
    for q in read_jsonl(q_path):
        if q["qid"] not in split:
            raise KeyError(f"{q['qid']} has no split assignment")
        rows.append({**q, "split": split[q["qid"]]})
    if len(rows) != len(split):
        raise ValueError("questions.jsonl and split.jsonl disagree on the question set")
    return rows
