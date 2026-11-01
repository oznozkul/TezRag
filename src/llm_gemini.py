"""Gemini generateContent client. Same LLMResult fields as the OpenAI client.

    python -m src.llm --probe --config configs/gemini.yaml

Token rule (Google token guide, checked 2026-10-24): `candidates_token_count` does not
include thinking tokens, and the output price includes them. Billed output is therefore
candidates + thoughts. cost.py bills `output_tokens` once and does not add `reasoning_tokens`
again. A response whose `total_token_count` shows thoughts already inside candidates is not
added twice. With thinking_budget 0 the two formulas match, because thoughts are 0.

The API key is read only from GEMINI_API_KEY (.env or the environment).
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from datetime import datetime, timezone

import httpx
from aiolimiter import AsyncLimiter
from google import genai
from google.genai import errors, types

from src.config import Config
from src.llm import LLMResult

log = logging.getLogger("llm_gemini")

PROBE_INPUT = "Reply with the single word OK."
SAFETY_FINISH = {"SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "IMAGE_SAFETY"}
_PARAM_KEYS = {"temperature", "top_p", "max_output_tokens", "seed", "thinking_budget"}


def tokens_from_gemini_usage(usage: dict | None) -> dict | None:
    """Map usage_metadata to the fields cost.py bills. None when the response has no usage."""
    if not usage:
        return None
    prompt = int(usage.get("prompt_token_count") or 0)
    cached = int(usage.get("cached_content_token_count") or 0)
    candidates = int(usage.get("candidates_token_count") or 0)
    thoughts = int(usage.get("thoughts_token_count") or 0)
    total = usage.get("total_token_count")
    billed = candidates + thoughts
    if total is not None and thoughts:
        total = int(total)
        if total == prompt + candidates:
            billed = candidates  # thoughts already included in candidates
        elif total != prompt + candidates + thoughts:
            raise ValueError(f"gemini usage does not add up: {usage}")
    if cached > prompt:
        cached = prompt
    return {"input_tokens": prompt, "cached_input_tokens": cached,
            "output_tokens": billed, "reasoning_tokens": thoughts}


def config_for(params: dict) -> types.GenerateContentConfig | None:
    unknown = set(params) - _PARAM_KEYS
    if unknown:
        raise ValueError(f"unknown gemini params: {sorted(unknown)}")
    kw: dict = {}
    for name in ("temperature", "top_p", "max_output_tokens", "seed"):
        if name in params:
            kw[name] = params[name]
    if "thinking_budget" in params:
        kw["thinking_config"] = types.ThinkingConfig(thinking_budget=params["thinking_budget"])
    return types.GenerateContentConfig(**kw) if kw else None


def _client(cfg: Config) -> genai.Client:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set (put it in .env)")
    return genai.Client(api_key=key,
                        http_options=types.HttpOptions(timeout=int(cfg.llm.timeout_s * 1000)))


def _finish_reason(response) -> str | None:
    candidates = response.candidates or []
    if not candidates or candidates[0].finish_reason is None:
        return None
    reason = candidates[0].finish_reason
    return getattr(reason, "value", None) or str(reason)


def _block_reason(response) -> str | None:
    feedback = response.prompt_feedback
    if feedback is None or not feedback.block_reason:
        return None
    reason = feedback.block_reason
    value = getattr(reason, "value", None) or str(reason)
    if value in {"", "BLOCK_REASON_UNSPECIFIED"}:
        return None
    return value


def _text(response) -> str | None:
    try:
        return response.text
    except ValueError:
        return None


def _usage_dict(response) -> dict | None:
    usage = response.usage_metadata
    if usage is None:
        return None
    return usage.model_dump()


class GeminiClient:
    def __init__(self, cfg: Config, sent_params: dict, concurrency: int | None = None):
        self.cfg = cfg
        self.model = cfg.llm.model
        self.sent_params = sent_params
        self.config = config_for(sent_params)
        self.client = _client(cfg)
        self.sem = asyncio.Semaphore(concurrency or cfg.runner.concurrency)
        self.rpm = AsyncLimiter(cfg.runner.rpm, 60)
        self.tpm = AsyncLimiter(cfg.runner.tpm, 60)

    async def aclose(self) -> None:
        return None

    async def complete(self, prompt: str) -> LLMResult:
        rc = self.cfg.runner
        res = LLMResult()
        est_tokens = min(len(prompt) // 3 + int(self.sent_params.get("max_output_tokens", 256)), rc.tpm)
        async with self.sem:
            for attempt in range(1, rc.max_retries + 2):
                res.attempts = attempt
                await self.rpm.acquire()
                await self.tpm.acquire(est_tokens)
                t0 = time.perf_counter_ns()
                try:
                    response = await self.client.aio.models.generate_content(
                        model=self.model, contents=prompt, config=self.config)
                except (errors.ServerError, httpx.TimeoutException, httpx.TransportError) as e:
                    if attempt > rc.max_retries:
                        res.error, res.error_kind = f"{type(e).__name__}: {e}", "transient_exhausted"
                        return res
                    wait = min(rc.backoff_max_s, rc.backoff_base_s * 2 ** (attempt - 1))
                    wait *= random.uniform(0.5, 1.5)
                    log.warning("attempt %d: %s; retry in %.1fs", attempt, type(e).__name__, wait)
                    await asyncio.sleep(wait)
                    continue
                except errors.ClientError as e:
                    if e.code == 429 and attempt <= rc.max_retries:
                        wait = min(rc.backoff_max_s, rc.backoff_base_s * 2 ** (attempt - 1))
                        wait *= random.uniform(0.5, 1.5)
                        log.warning("attempt %d: 429; retry in %.1fs", attempt, wait)
                        await asyncio.sleep(wait)
                        continue
                    res.error = f"ClientError {e.code}: {e.message}"
                    res.error_kind = "transient_exhausted" if e.code == 429 else "permanent"
                    return res
                res.llm_ms = (time.perf_counter_ns() - t0) / 1e6
                break

        res.response_id = response.response_id
        res.response_model = response.model_version
        res.text = _text(response)
        res.raw_usage = _usage_dict(response) or {}
        block = _block_reason(response)
        finish = _finish_reason(response)
        try:
            mapped = tokens_from_gemini_usage(res.raw_usage or None)
        except ValueError as e:
            res.error, res.error_kind = str(e), "no_usage"
            return res
        if mapped:
            res.input_tokens = mapped["input_tokens"]
            res.output_tokens = mapped["output_tokens"]
            res.reasoning_tokens = mapped["reasoning_tokens"]
            res.cached_input_tokens = mapped["cached_input_tokens"]
        if block or finish in SAFETY_FINISH:
            res.status = finish or block
            res.error = f"blocked: {block or finish}"
            res.error_kind = "flagged"
            return res
        if mapped is None:
            res.error, res.error_kind = "response has no usage", "no_usage"
            return res
        res.status = finish or "STOP"
        if finish == "MAX_TOKENS":
            res.error, res.error_kind = "finish_reason=MAX_TOKENS", "incomplete"
        return res


async def _try(client: genai.Client, model: str, params: dict) -> tuple[bool, str | None, dict | None]:
    try:
        response = await client.aio.models.generate_content(
            model=model, contents=PROBE_INPUT, config=config_for(params))
    except errors.ClientError as e:
        return False, f"{e.code} {e.message}", None
    usage = _usage_dict(response)
    return True, None, {"finish_reason": _finish_reason(response), "usage": usage,
                        "text": _text(response), "model": response.model_version}


async def probe(cfg: Config) -> dict:
    client = _client(cfg)
    model = cfg.llm.model
    out: dict = {"model": model, "provider": "gemini",
                 "probed_at": datetime.now(timezone.utc).isoformat(), "params": {}}
    ok, err, info = await _try(client, model, {})
    if not ok:
        raise SystemExit(f"bare request to {model} failed: {err}")
    out["bare_request"] = info
    for name, value in cfg.llm.params.items():
        ok, err, info = await _try(client, model, {name: value})
        out["params"][name] = {"value": value, "accepted": ok, "error": err, "response": info}
        (log.info if ok else log.warning)("param %s=%r: %s", name, value,
                                          "accepted" if ok else f"REJECTED ({err})")
        if name == "thinking_budget" and value == 0 and ok:
            thoughts = ((info or {}).get("usage") or {}).get("thoughts_token_count") or 0
            if thoughts:
                raise SystemExit(f"thinking_budget=0 still reported {thoughts} thinking tokens")
    return out
