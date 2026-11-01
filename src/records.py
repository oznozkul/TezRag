"""Final call record per question, and the error kind used by resume and evaluation."""
from __future__ import annotations

from collections import defaultdict

from src.io_utils import read_jsonl
from src.llm import is_flagged_message


def error_kind(r: dict) -> str | None:
    """Error kind of a record; records written before `flagged` existed are classified by message."""
    if r.get("error") is None:
        return None
    return "flagged" if is_flagged_message(r["error"]) else r.get("error_kind")


def final_records(path) -> tuple[dict, dict]:
    """qid -> final record, qid -> number of calls."""
    by_q = defaultdict(list)
    for r in read_jsonl(path):
        by_q[r["qid"]].append(r)
    final = {}
    for qid, rs in by_q.items():
        ok = [r for r in rs if r["error"] is None]
        final[qid] = ok[-1] if ok else rs[-1]
    return final, {q: len(v) for q, v in by_q.items()}
