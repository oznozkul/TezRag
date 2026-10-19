"""Reasoning leakage: answers whose text contains deliberation or explanation instead of a short answer.

A record counts as leaked if any of:
  incomplete  the call stopped at max_output_tokens (status != completed)
  long        the answer has >= LONG_WORDS words (calibrated on the full run: answers of 8-16 words are
              verbose but genuine; from ~17 words most are deliberation or explanation)
  marker      the answer contains a deliberation marker (wait, hmm, let me, actually, so answer, ...)
The criteria are reported separately so the definition can be audited.
"""
from __future__ import annotations

import re

LONG_WORDS = 17
MARKERS = re.compile(
    r"\b(wait|hmm|let's|let me|i'll|i will|i think|maybe|actually|but instruction|so answer|"
    r"provide|answer:)", re.IGNORECASE)


def leak_flags(rec: dict) -> dict[str, bool]:
    text = rec.get("prediction") or ""
    flags = {
        "incomplete": rec.get("error_kind") == "incomplete" or (
            rec.get("status") not in (None, "completed") and rec.get("input_tokens") is not None),
        "long": len(text.split()) >= LONG_WORDS,
        "marker": bool(MARKERS.search(text)),
    }
    flags["leak"] = any(flags.values())
    return flags
