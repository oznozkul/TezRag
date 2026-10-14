"""OpenAI Responses API client: parameter probing, retries, rate limiting, usage capture.

    python -m src.llm --probe     # paid: a handful of tiny calls; writes results/meta/param_probe.json

Probe: every configured parameter is tried on its own on top of a bare request; the server's answer
decides whether it is supported. Unsupported parameters are dropped with a WARNING and listed in every
output record (`dropped_params`), never silently. Reasoning effort levels are tried from lowest to
highest and the lowest accepted one is reported (the config must pin exactly that level).

Token counts come only from `response.usage` (input_tokens, output_tokens,
output_tokens_details.reasoning_tokens, input_tokens_details.cached_tokens). For reasoning models
output_tokens already includes reasoning_tokens; both are billed at the output price.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from aiolimiter import AsyncLimiter

from src.config import Config, load_config
from src.io_utils import setup_logging, write_json

log = logging.getLogger("llm")

EFFORT_ORDER = ["none", "minimal", "low", "medium", "high"]
PROBE_INPUT = "Reply with the single word OK."


def to_api_kwargs(params: dict) -> dict:
    """Map config param names to Responses API keyword arguments."""
    kw: dict = {}
    extra: dict = {}
    for k, v in params.items():
        if k == "reasoning_effort":
            kw["reasoning"] = {"effort": v}
        elif k == "verbosity":
            kw["text"] = {"verbosity": v}
        elif k == "seed":
            extra["seed"] = v
        else:
            kw[k] = v
    if extra:
        kw["extra_body"] = extra
    return kw


@dataclass
class LLMResult:
    text: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None
    cached_input_tokens: int | None = None
    llm_ms: float | None = None
    response_id: str | None = None
    response_model: str | None = None
    status: str | None = None
    error: str | None = None
    error_kind: str | None = None        # transient_exhausted | permanent | incomplete | no_usage
    attempts: int = 0
    raw_usage: dict = field(default_factory=dict)


def _client():
    from openai import AsyncOpenAI

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set (put it in .env)")
    return AsyncOpenAI(max_retries=0)  # retries are ours, so they are counted and logged


class LLMClient:
    def __init__(self, cfg: Config, sent_params: dict, concurrency: int | None = None):
        self.cfg = cfg
        self.model = cfg.llm.model
        self.sent_params = sent_params
        self.kwargs = to_api_kwargs(sent_params)
        self.client = _client()
        self.sem = asyncio.Semaphore(concurrency or cfg.runner.concurrency)
        self.rpm = AsyncLimiter(cfg.runner.rpm, 60)
        self.tpm = AsyncLimiter(cfg.runner.tpm, 60)

    async def aclose(self) -> None:
        await self.client.close()

    async def complete(self, prompt: str) -> LLMResult:
        import openai

        rc = self.cfg.runner
        res = LLMResult()
        est_tokens = min(len(prompt) // 3 + int(self.sent_params.get("max_output_tokens", 256)),
                         rc.tpm)
        async with self.sem:
            for attempt in range(1, rc.max_retries + 2):
                res.attempts = attempt
                await self.rpm.acquire()
                await self.tpm.acquire(est_tokens)
                t0 = time.perf_counter_ns()
                try:
                    r = await self.client.responses.create(
                        model=self.model, input=prompt, timeout=self.cfg.llm.timeout_s, **self.kwargs)
                except (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError,
                        openai.InternalServerError) as e:
                    if attempt > rc.max_retries:
                        res.error, res.error_kind = f"{type(e).__name__}: {e}", "transient_exhausted"
                        return res
                    wait = min(rc.backoff_max_s, rc.backoff_base_s * 2 ** (attempt - 1))
                    wait *= random.uniform(0.5, 1.5)  # jitter
                    log.warning("attempt %d: %s; retry in %.1fs", attempt, type(e).__name__, wait)
                    await asyncio.sleep(wait)
                    continue
                except openai.APIStatusError as e:
                    res.error, res.error_kind = f"{type(e).__name__} {e.status_code}: {e.message}", \
                        "permanent"
                    return res
                res.llm_ms = (time.perf_counter_ns() - t0) / 1e6
                break

        res.response_id, res.response_model, res.status = r.id, r.model, r.status
        res.text = r.output_text
        u = r.usage
        if u is None:
            res.error, res.error_kind = "response has no usage field", "no_usage"
            return res
        res.raw_usage = u.model_dump()
        res.input_tokens, res.output_tokens = u.input_tokens, u.output_tokens
        res.reasoning_tokens = u.output_tokens_details.reasoning_tokens
        res.cached_input_tokens = u.input_tokens_details.cached_tokens
        if r.status != "completed":
            reason = r.incomplete_details.reason if r.incomplete_details else "unknown"
            res.error, res.error_kind = f"status={r.status} ({reason})", "incomplete"
        return res


# --- probing ---------------------------------------------------------------------------------

async def _try(client, model: str, kwargs: dict) -> tuple[bool, str | None, dict | None]:
    import openai

    try:
        r = await client.responses.create(model=model, input=PROBE_INPUT, **kwargs)
        return True, None, {"status": r.status, "usage": r.usage.model_dump() if r.usage else None,
                            "output_text": r.output_text, "model": r.model}
    except openai.BadRequestError as e:
        return False, e.message, None


async def probe(cfg: Config) -> dict:
    client = _client()
    model = cfg.llm.model
    out: dict = {"model": model, "probed_at": datetime.now(timezone.utc).isoformat(),
                 "params": {}, "reasoning_effort_levels": {}}
    ok, err, info = await _try(client, model, {})
    if not ok:
        raise SystemExit(f"bare request to {model} failed: {err}")
    out["bare_request"] = info
    for name, value in cfg.llm.params.items():
        ok, err, info = await _try(client, model, to_api_kwargs({name: value}))
        out["params"][name] = {"value": value, "accepted": ok, "error": err, "response": info}
        (log.info if ok else log.warning)("param %s=%r: %s", name, value,
                                          "accepted" if ok else f"REJECTED ({err})")
    for level in EFFORT_ORDER:
        ok, err, info = await _try(client, model, {"reasoning": {"effort": level}})
        out["reasoning_effort_levels"][level] = {"accepted": ok, "error": err,
                                                 "usage": info and info["usage"]}
        if ok:
            out["lowest_reasoning_effort"] = level
            break
    return out


def probe_path(cfg: Config):
    return cfg.path("results") / "meta" / "param_probe.json"


def load_sent_params(cfg: Config) -> tuple[dict, dict]:
    """Split configured params into (sent, dropped) using the saved probe. Refuses to run without it."""
    p = probe_path(cfg)
    if not p.exists():
        raise SystemExit(f"{p} missing; run `python -m src.llm --probe` first")
    pr = json.loads(p.read_text())
    if pr["model"] != cfg.llm.model:
        raise SystemExit(f"probe was for {pr['model']}, config uses {cfg.llm.model}; re-probe")
    sent, dropped = {}, {}
    for k, v in cfg.llm.params.items():
        rec = pr["params"].get(k)
        if rec is None or rec["value"] != v:
            raise SystemExit(f"param {k}={v!r} not covered by the probe; re-run --probe")
        if rec["accepted"]:
            sent[k] = v
        else:
            dropped[k] = {"value": v, "reason": rec["error"]}
            log.warning("dropping unsupported param %s=%r (%s)", k, v, rec["error"])
    lowest = pr.get("lowest_reasoning_effort")
    if "reasoning_effort" in sent and sent["reasoning_effort"] != lowest:
        raise SystemExit(f"config reasoning_effort={sent['reasoning_effort']!r} but lowest supported "
                         f"is {lowest!r}; pin it in configs/default.yaml")
    return sent, dropped


def main() -> None:
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--probe", action="store_true", required=True)
    args = ap.parse_args()
    cfg = load_config(args.config)
    out = asyncio.run(probe(cfg))
    write_json(probe_path(cfg), out)
    print(json.dumps({k: v["accepted"] for k, v in out["params"].items()}, indent=1))
    print("lowest reasoning effort:", out.get("lowest_reasoning_effort"))


if __name__ == "__main__":
    main()

