"""Anthropic Messages client. Same LLMResult fields as the OpenAI client.

    python -m src.llm --probe --config configs/claude.yaml

Claude Haiku 5.5 thinks unless the request sends thinking disabled. That is accepted
only at effort high or below. output_tokens already include thinking tokens, so
reasoning_tokens are not added again in cost.py. Cache reads use the cached-input price.
This run does not set a cache breakpoint, so cache writes stay 0.

The API key is read only from ANTHROPIC_API_KEY (.env or the environment).
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from datetime import datetime, timezone

from aiolimiter import AsyncLimiter

from src.config import Config
from src.llm import LLMResult

log = logging.getLogger("llm_anthropic")

PROBE_INPUT = "Reply with the single word OK."
_PARAM_KEYS = {"temperature", "max_output_tokens", "effort", "thinking"}


def request_kwargs(params: dict) -> dict:
    unknown = set(params) - _PARAM_KEYS
    if unknown:
        raise ValueError(f"unknown anthropic params: {sorted(unknown)}")
    kw: dict = {}
    if "max_output_tokens" in params:
        kw["max_tokens"] = params["max_output_tokens"]
    if "temperature" in params:
        kw["temperature"] = params["temperature"]
    if "effort" in params:
        kw["output_config"] = {"effort": params["effort"]}
    if "thinking" in params:
        kw["thinking"] = {"type": params["thinking"]}
    return kw


def parse_message(content: list, usage: dict | None, stop_reason: str | None) -> dict:
    """Map one Messages response onto LLMResult fields. A thinking block is an error."""
    texts = []
    for block in content or []:
        if block.get("type") == "thinking" or block.get("type") == "redacted_thinking":
            return {"error": "response included a thinking block", "error_kind": "thinking"}
        if block.get("type") == "text":
            texts.append(block.get("text") or "")
    if not usage or usage.get("input_tokens") is None or usage.get("output_tokens") is None:
        return {"error": "response has no usage", "error_kind": "no_usage"}
    fresh = int(usage.get("input_tokens") or 0)
    cache_read = int(usage.get("cache_read_input_tokens") or 0)
    cache_write = int(usage.get("cache_creation_input_tokens") or 0)
    details = usage.get("output_tokens_details") or {}
    reasoning = int(details.get("thinking_tokens") or 0)
    out = {
        "text": "".join(texts),
        "input_tokens": fresh + cache_read + cache_write,
        "cached_input_tokens": cache_read,
        "output_tokens": int(usage["output_tokens"]),
        "reasoning_tokens": reasoning,
        "error": None,
        "error_kind": None,
    }
    if reasoning:
        out["error"], out["error_kind"] = "response included thinking tokens", "thinking"
    elif stop_reason == "max_tokens":
        out["error"], out["error_kind"] = "stop_reason=max_tokens", "incomplete"
    elif stop_reason == "refusal":
        out["error"], out["error_kind"] = "stop_reason=refusal", "permanent"
    return out


MESSAGES_URL = "https://api.anthropic.com/v1/messages"
_RETRY_STATUS = {429, 500, 502, 503, 529}


def _headers(cfg: Config) -> dict:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY is not set (put it in .env)")
    return {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}


class AnthropicClient:
    def __init__(self, cfg: Config, sent_params: dict, concurrency: int | None = None):
        import httpx

        self.cfg = cfg
        self.model = cfg.llm.model
        self.sent_params = sent_params
        self.kwargs = request_kwargs(sent_params)
        self.headers = _headers(cfg)
        self.http = httpx.AsyncClient(timeout=cfg.llm.timeout_s)
        self.sem = asyncio.Semaphore(concurrency or cfg.runner.concurrency)
        # One slot per interval, so the first calls do not spend the whole minute at once.
        self.rpm = AsyncLimiter(1, 60 / cfg.runner.rpm)
        self.tpm = AsyncLimiter(cfg.runner.tpm, 60)

    async def aclose(self) -> None:
        await self.http.aclose()

    async def _post(self, body: dict) -> tuple[int, dict | str]:
        import httpx

        try:
            response = await self.http.post(MESSAGES_URL, headers=self.headers, json=body)
        except (httpx.TimeoutException, httpx.TransportError) as e:
            return 0, f"{type(e).__name__}: {e}"
        try:
            payload = response.json()
        except ValueError:
            payload = response.text
        return response.status_code, payload

    async def complete(self, prompt: str) -> LLMResult:
        rc = self.cfg.runner
        res = LLMResult()
        est_tokens = min(len(prompt) // 3 + int(self.sent_params.get("max_output_tokens", 256)), rc.tpm)
        body = {"model": self.model, "messages": [{"role": "user", "content": prompt}], **self.kwargs}
        async with self.sem:
            for attempt in range(1, rc.max_retries + 2):
                res.attempts = attempt
                await self.rpm.acquire()
                await self.tpm.acquire(est_tokens)
                t0 = time.perf_counter_ns()
                status, payload = await self._post(body)
                if status == 0 or status in _RETRY_STATUS:
                    if attempt > rc.max_retries:
                        res.error = payload if isinstance(payload, str) else _error_text(status, payload)
                        res.error_kind = "transient_exhausted"
                        return res
                    wait = min(rc.backoff_max_s, rc.backoff_base_s * 2 ** (attempt - 1))
                    wait *= random.uniform(0.5, 1.5)
                    log.warning("attempt %d: HTTP %s; retry in %.1fs", attempt, status or "transport", wait)
                    await asyncio.sleep(wait)
                    continue
                res.llm_ms = (time.perf_counter_ns() - t0) / 1e6
                break
        if status != 200 or not isinstance(payload, dict):
            res.error = _error_text(status, payload)
            res.error_kind = "permanent"
            return res
        res.response_id = payload.get("id")
        res.response_model = payload.get("model")
        res.status = payload.get("stop_reason")
        parsed = parse_message(payload.get("content") or [], payload.get("usage"), payload.get("stop_reason"))
        res.text = parsed.get("text")
        res.raw_usage = payload.get("usage") or {}
        if parsed.get("error_kind") == "thinking":
            res.error, res.error_kind = parsed["error"], "permanent"
            return res
        for name in ("input_tokens", "output_tokens", "reasoning_tokens", "cached_input_tokens"):
            if name in parsed:
                setattr(res, name, parsed[name])
        if parsed.get("error"):
            res.error, res.error_kind = parsed["error"], parsed["error_kind"]
        return res


def _error_text(status: int, payload) -> str:
    if isinstance(payload, dict):
        err = payload.get("error") or {}
        message = err.get("message") if isinstance(err, dict) else str(err)
        return f"HTTP {status}: {message}"
    return f"HTTP {status}: {payload}"


async def _try(cfg: Config, params: dict) -> tuple[bool, str | None, dict | None]:
    import httpx

    kw = request_kwargs(params)
    kw.setdefault("max_tokens", 16)
    body = {"model": cfg.llm.model, "messages": [{"role": "user", "content": PROBE_INPUT}], **kw}
    async with httpx.AsyncClient(timeout=cfg.llm.timeout_s) as http:
        try:
            response = await http.post(MESSAGES_URL, headers=_headers(cfg), json=body)
        except (httpx.TimeoutException, httpx.TransportError) as e:
            return False, f"{type(e).__name__}: {e}", None
    try:
        payload = response.json()
    except ValueError:
        return False, f"HTTP {response.status_code}: {response.text}", None
    if response.status_code == 400:
        return False, _error_text(400, payload), None
    if response.status_code != 200:
        return False, _error_text(response.status_code, payload), None
    return True, None, {"stop_reason": payload.get("stop_reason"), "usage": payload.get("usage"),
                        "content": payload.get("content"), "model": payload.get("model")}


async def probe(cfg: Config) -> dict:
    model = cfg.llm.model
    base = {}
    if cfg.llm.params.get("thinking") == "disabled":
        base["thinking"] = "disabled"
    if cfg.llm.params.get("effort"):
        base["effort"] = cfg.llm.params["effort"]
    out: dict = {"model": model, "provider": "anthropic",
                 "probed_at": datetime.now(timezone.utc).isoformat(), "params": {}}
    ok, err, info = await _try(cfg, base)
    if not ok:
        raise SystemExit(f"request to {model} failed: {err}")
    parsed = parse_message(info["content"], info["usage"], info["stop_reason"])
    if parsed.get("error_kind") == "thinking":
        raise SystemExit(f"{model} still returned a thinking block with {base}")
    out["bare_request"] = info
    for name, value in cfg.llm.params.items():
        ok, err, info = await _try(cfg, {**base, name: value})
        out["params"][name] = {"value": value, "accepted": ok, "error": err, "response": info}
        (log.info if ok else log.warning)("param %s=%r: %s", name, value,
                                          "accepted" if ok else f"REJECTED ({err})")
    if cfg.llm.params.get("thinking") == "disabled":
        rec = out["params"].get("thinking")
        if not rec or not rec["accepted"]:
            raise SystemExit("thinking=disabled was rejected; refusing to run with thinking on")
        out["lowest_reasoning_effort"] = "disabled"
    return out
