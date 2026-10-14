"""The three call types. Each turns a question (+ retrieval for always_rag) into one prompt.

  llm_only      question -> model
  always_rag    question + BM25 top-k passages -> model   (template differs only by the context block)
  llm_decision  "can you answer without external sources? YES/NO" -> model; the answer is a routing
                decision (yes -> llm_only, no/invalid -> always_rag), combined later in evaluation.

Templates are filled with str.replace, not str.format, so braces in questions/passages are safe.
"""
from __future__ import annotations

import re
from functools import cache

from src.config import PROJECT_ROOT, Config

SYSTEMS = ("llm_only", "always_rag", "llm_decision")
USES_RETRIEVAL = {"llm_only": False, "always_rag": True, "llm_decision": False}


@cache
def _read(path: str) -> str:
    return (PROJECT_ROOT / path).read_text()


def template(cfg: Config, system: str) -> str:
    return _read(getattr(cfg.prompts, system))


def format_context(cfg: Config, passages: list[dict]) -> str:
    tpl = _read(cfg.prompts.passage)
    return cfg.prompts.passage_separator.join(
        tpl.replace("{title}", p["title"]).replace("{text}", p["text"]) for p in passages)


def build_prompt(cfg: Config, system: str, question: str, passages: list[dict] | None = None) -> str:
    prompt = template(cfg, system).replace("{question}", question)
    if USES_RETRIEVAL[system]:
        if passages is None:
            raise ValueError("always_rag needs passages")
        prompt = prompt.replace("{context}", format_context(cfg, passages))
    return prompt


_WORD = re.compile(r"[a-z]+")


def parse_decision(text: str | None) -> str:
    """'yes' / 'no' only when the reply is exactly that word (case/punctuation ignored); else 'invalid'."""
    words = _WORD.findall((text or "").lower())
    if words == ["yes"]:
        return "yes"
    if words == ["no"]:
        return "no"
    return "invalid"


def route_for(decision: str) -> str:
    """Invalid replies are treated as NO (retrieve) — the safe default — and reported separately."""
    return "llm_only" if decision == "yes" else "always_rag"
