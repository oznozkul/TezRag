"""Per-call cost, split into components (retrieval / generation / router).

Prices come from config `pricing` (per 1M tokens, with source URL and retrieval date).
output_tokens already include reasoning tokens (both billed at the output price), so reasoning is
not added again. Cached input tokens are billed at the cached-input price.

DeepSeek bills twice the listed off-peak rate during weekday peak hours (01:00-04:00 and
06:00-10:00 UTC). A pricing entry with `peak_multiplier` applies that factor from the call's
timestamp. Chinese public holidays are not excluded, so a holiday inside those hours is priced
as peak.
"""
from __future__ import annotations

from datetime import datetime, timezone

from src.config import Config

COMPONENTS = ("retrieval_usd", "generation_usd", "router_usd")


def is_peak_utc(timestamp: str | None) -> bool:
    """Weekday 01:00-04:00 or 06:00-10:00 UTC. Weekends are off-peak. Missing time is off-peak."""
    if not timestamp:
        return False
    t = datetime.fromisoformat(timestamp)
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    t = t.astimezone(timezone.utc)
    if t.weekday() >= 5:
        return False
    return t.hour in (1, 2, 3, 6, 7, 8, 9)


def call_usd(cfg: Config, rec: dict | None) -> float:
    """Billed cost of one model call; 0 when the API returned no usage (e.g. a rejected prompt)."""
    if not rec or rec.get("input_tokens") is None:
        return 0.0
    p = cfg.pricing[rec["model"]]
    cached = rec.get("cached_input_tokens") or 0
    amount = ((rec["input_tokens"] - cached) * p["input_per_1m"] + cached * p["cached_input_per_1m"]
              + rec["output_tokens"] * p["output_per_1m"]) / 1e6
    if p.get("peak_multiplier") and is_peak_utc(rec.get("timestamp")):
        amount *= float(p["peak_multiplier"])
    return amount


def retrieval_usd(cfg: Config, n_calls: int) -> float:
    return n_calls * float(cfg.pricing["retrieval_bm25"]["per_call_usd"])
