"""Per-call cost, split into components (retrieval / generation / router).

Prices come from config `pricing` (per 1M tokens, with source URL and retrieval date).
output_tokens already include reasoning tokens (both billed at the output price), so reasoning is
not added again. Cached input tokens are billed at the cached-input price.
"""
from __future__ import annotations

from src.config import Config

COMPONENTS = ("retrieval_usd", "generation_usd", "router_usd")


def call_usd(cfg: Config, rec: dict | None) -> float:
    """Billed cost of one model call; 0 when the API returned no usage (e.g. a rejected prompt)."""
    if not rec or rec.get("input_tokens") is None:
        return 0.0
    p = cfg.pricing[rec["model"]]
    cached = rec.get("cached_input_tokens") or 0
    return ((rec["input_tokens"] - cached) * p["input_per_1m"] + cached * p["cached_input_per_1m"]
            + rec["output_tokens"] * p["output_per_1m"]) / 1e6


def retrieval_usd(cfg: Config, n_calls: int) -> float:
    return n_calls * float(cfg.pricing["retrieval_bm25"]["per_call_usd"])
