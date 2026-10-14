"""SQuAD-style answer metrics. With several gold answers, the max over golds is taken.

accuracy: a normalized gold answer occurs in the normalized prediction. We match on whole
tokens (" gold " in " pred "), not raw substrings, so short aliases such as "ca" (2Wiki, for
Canada) cannot match inside unrelated words. Adaptive-RAG uses plain substring containment;
this is a deliberate, documented difference (see README).

Alias policy for accuracy (default): aliases whose normalized form is shorter than
`min_alias_chars` (3, i.e. <= 2 characters such as "in" for India, "no" for Norwegian) are
ignored, because containment would match them inside ordinary words of a prediction.
The primary answer is always kept. EM and F1 use every alias.
"""
from __future__ import annotations

import re
import string
from collections import Counter

_ARTICLES = re.compile(r"\b(a|an|the)\b", re.UNICODE)
_PUNCT = set(string.punctuation)


def normalize_answer(s: str | None) -> str:
    """Lowercase, drop punctuation, drop articles a/an/the, collapse whitespace (SQuAD v1.1)."""
    if not s:
        return ""
    s = s.lower()
    s = "".join(ch for ch in s if ch not in _PUNCT)
    s = _ARTICLES.sub(" ", s)
    return " ".join(s.split())


def exact_match(pred: str | None, gold: str) -> float:
    return float(normalize_answer(pred) == normalize_answer(gold))


def f1(pred: str | None, gold: str) -> float:
    p, g = normalize_answer(pred).split(), normalize_answer(gold).split()
    if not p or not g:
        return float(p == g)
    common = Counter(p) & Counter(g)
    same = sum(common.values())
    if same == 0:
        return 0.0
    precision, recall = same / len(p), same / len(g)
    return 2 * precision * recall / (precision + recall)


def contains(pred: str | None, gold: str) -> float:
    g = normalize_answer(gold)
    if not g:
        return 0.0
    return float(f" {g} " in f" {normalize_answer(pred)} ")


def _best(fn, pred: str | None, golds: list[str]) -> float:
    golds = [g for g in golds if normalize_answer(g)]
    if not golds:
        raise ValueError("no non-empty gold answer")
    return max(fn(pred, g) for g in golds)


def accuracy_golds(golds: list[str], primary: list[str] | None, min_alias_chars: int) -> list[str]:
    """Golds used for accuracy: primary answer(s) + aliases with >= min_alias_chars normalized chars."""
    keep = list(primary or [])
    keep += [g for g in golds if len(normalize_answer(g)) >= min_alias_chars and g not in keep]
    return keep or golds


def score(pred: str | None, golds: list[str], primary: list[str] | None = None,
          min_alias_chars: int = 0) -> dict[str, float]:
    return {
        "em": _best(exact_match, pred, golds),
        "f1": _best(f1, pred, golds),
        "accuracy": _best(contains, pred, accuracy_golds(golds, primary, min_alias_chars)),
    }


def is_correct(scores: dict[str, float], metric: str, f1_threshold: float = 0.5) -> bool:
    if metric == "f1":
        return scores["f1"] >= f1_threshold
    return scores[metric] == 1.0
