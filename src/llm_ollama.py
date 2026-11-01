"""Local Ollama chat client. Same LLMResult fields as the API clients.

    python -m src.llm --probe --config configs/qwen.yaml

The prompt is sent as a single user message. The thesis prompts are already the full
instruction, so no extra system text is added. `think: false` asks Qwen3.5 not to emit a
reasoning trace. A response that still contains one is an error. Token counts are Ollama's
`prompt_eval_count` and `eval_count`. The price in the config is 0: these weights run on
this machine.
"""
from __future__ import annotations

import asyncio
import logging
import random
import time
from datetime import datetime, timezone

import httpx
from aiolimiter import AsyncLimiter

from src.config import Config
from src.llm import LLMResult, PROBE_INPUT

log = logging.getLogger("llm_ollama")

HOST = "http://127.0.0.1:11434"
_OPTION_KEYS = {"temperature", "max_output_tokens", "seed"}
NUM_CTX = 8192


def request_body(tag: str, prompt: str, params: dict) -> dict:
    unknown = set(params) - _OPTION_KEYS - {"think"}
    if unknown:
        raise ValueError(f"unknown ollama params: {sorted(unknown)}")
    options = {"num_ctx": NUM_CTX}
    if "temperature" in params:
        options["temperature"] = params["temperature"]
    if "max_output_tokens" in params:
        options["num_predict"] = params["max_output_tokens"]
    if "seed" in params:
        options["seed"] = params["seed"]
    body = {
        "model": tag,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "keep_alive": "30m",
        "options": options,
    }
    if "think" in params:
        body["think"] = bool(params["think"])
    return body


def parse_chat(data: dict) -> tuple[str | None, dict | None, str | None]:
    """Return text, billed token fields, and an error kind.

    `length` keeps the tokens and is reported as incomplete. A thinking trace is refused.
    """
    message = data.get("message") or {}
    thinking = (message.get("thinking") or "").strip()
    if thinking:
        return message.get("content") or "", None, "thinking"
    if data.get("prompt_eval_count") is None or data.get("eval_count") is None:
        return message.get("content") or "", None, "no_usage"
    prompt = int(data["prompt_eval_count"])
    cached = int(data.get("prompt_eval_cached_count") or 0)
    if cached > prompt:
        cached = prompt
    usage = {
        "input_tokens": prompt,
        "cached_input_tokens": cached,
        "output_tokens": int(data["eval_count"]),
        "reasoning_tokens": 0,
    }
    if data.get("done_reason") == "length":
        return message.get("content") or "", usage, "incomplete"
    return message.get("content") or "", usage, None


class OllamaClient:
    def __init__(self, cfg: Config, sent_params: dict, concurrency: int | None = None):
        self.cfg = cfg
        self.model = cfg.llm.model
        self.tag = cfg.llm.ollama_tag or cfg.llm.model
        self.sent_params = sent_params
        self.sem = asyncio.Semaphore(concurrency or cfg.runner.concurrency)
        self.rpm = AsyncLimiter(cfg.runner.rpm, 60)
        self.tpm = AsyncLimiter(cfg.runner.tpm, 60)
        self.http = httpx.AsyncClient(timeout=cfg.llm.timeout_s)

    async def aclose(self) -> None:
        await self.http.aclose()

    async def complete(self, prompt: str) -> LLMResult:
        rc = self.cfg.runner
        res = LLMResult()
        est = min(len(prompt) // 3 + int(self.sent_params.get("max_output_tokens", 256)), rc.tpm)
        async with self.sem:
            for attempt in range(1, rc.max_retries + 2):
                res.attempts = attempt
                await self.rpm.acquire()
                await self.tpm.acquire(est)
                t0 = time.perf_counter_ns()
                try:
                    response = await self.http.post(
                        f"{HOST}/api/chat",
                        json=request_body(self.tag, prompt, self.sent_params),
                    )
                except (httpx.TimeoutException, httpx.TransportError) as e:
                    if attempt > rc.max_retries:
                        res.error, res.error_kind = f"{type(e).__name__}: {e}", "transient_exhausted"
                        return res
                    wait = min(rc.backoff_max_s, rc.backoff_base_s * 2 ** (attempt - 1))
                    wait *= random.uniform(0.5, 1.5)
                    log.warning("attempt %d: %s; retry in %.1fs", attempt, type(e).__name__, wait)
                    await asyncio.sleep(wait)
                    continue
                res.llm_ms = (time.perf_counter_ns() - t0) / 1e6
                if response.status_code >= 500 and attempt <= rc.max_retries:
                    wait = min(rc.backoff_max_s, rc.backoff_base_s * 2 ** (attempt - 1))
                    log.warning("attempt %d: HTTP %s; retry in %.1fs", attempt, response.status_code, wait)
                    await asyncio.sleep(wait)
                    continue
                if response.status_code != 200:
                    res.error = f"HTTP {response.status_code}: {response.text[:300]}"
                    res.error_kind = "permanent"
                    return res
                data = response.json()
                break
            else:
                res.error, res.error_kind = "retries exhausted", "transient_exhausted"
                return res

        res.response_model = data.get("model") or self.tag
        res.raw_usage = {k: data.get(k) for k in ("prompt_eval_count", "eval_count", "done_reason")}
        text, usage, kind = parse_chat(data)
        res.text = text
        res.status = data.get("done_reason")
        if usage:
            res.input_tokens = usage["input_tokens"]
            res.output_tokens = usage["output_tokens"]
            res.reasoning_tokens = usage["reasoning_tokens"]
            res.cached_input_tokens = usage["cached_input_tokens"]
        if kind == "thinking":
            res.error, res.error_kind = "thinking trace returned while think is off", "permanent"
        elif kind == "no_usage":
            res.error, res.error_kind = "response has no token counts", "no_usage"
        elif kind == "incomplete":
            res.error, res.error_kind = "done_reason=length", "incomplete"
        return res


async def _try(cfg: Config, params: dict, allow_thinking: bool = False) -> tuple[bool, str | None, dict | None]:
    tag = cfg.llm.ollama_tag or cfg.llm.model
    timeout = httpx.Timeout(cfg.llm.timeout_s)
    async with httpx.AsyncClient(timeout=timeout) as http:
        try:
            response = await http.post(f"{HOST}/api/chat", json=request_body(tag, PROBE_INPUT, params))
        except (httpx.TimeoutException, httpx.TransportError) as e:
            return False, f"{type(e).__name__}: {e}", None
    if response.status_code != 200:
        return False, f"HTTP {response.status_code}: {response.text[:300]}", None
    data = response.json()
    text, usage, kind = parse_chat(data)
    info = {"done_reason": data.get("done_reason"), "usage": usage, "output_text": text,
            "model": data.get("model")}
    if kind == "thinking" and allow_thinking:
        info["thinking"] = True
        return True, None, info
    if kind == "thinking":
        return False, "thinking trace returned while think is off", None
    if kind == "no_usage":
        return False, "response has no token counts", None
    return True, None, info


async def probe(cfg: Config) -> dict:
    out = {"model": cfg.llm.model, "ollama_tag": cfg.llm.ollama_tag,
           "probed_at": datetime.now(timezone.utc).isoformat(),
           "params": {}, "reasoning_effort_levels": {}}
    # Qwen3.5 thinks unless think is false, and a thinking reply is long. Every trial
    # therefore keeps think off when the config asks for it. The think trial checks
    # that the trace is actually absent.
    base = {"think": False} if cfg.llm.params.get("think") is False else {}
    ok, err, info = await _try(cfg, base)
    if not ok:
        raise SystemExit(f"bare request to {cfg.llm.ollama_tag} failed: {err}")
    out["bare_request"] = info
    for name, value in cfg.llm.params.items():
        ok, err, info = await _try(cfg, {**base, name: value})
        out["params"][name] = {"value": value, "accepted": ok, "error": err, "response": info}
        (log.info if ok else log.warning)("param %s=%r: %s", name, value,
                                          "accepted" if ok else f"REJECTED ({err})")
    think = out["params"].get("think")
    if cfg.llm.params.get("think") is False and not (think and think["accepted"]):
        raise SystemExit(f"think:false was not accepted ({think}); refusing to run with reasoning on")
    return out
