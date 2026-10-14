import asyncio

import pytest

from src import run_baselines
from src.config import load_config
from src.io_utils import read_jsonl
from src.llm import LLMResult, to_api_kwargs
from src.systems import build_prompt, parse_decision, route_for, template

CFG = load_config()


def test_templates_differ_only_by_context_block():
    rag, plain = template(CFG, "always_rag"), template(CFG, "llm_only")
    assert rag.replace("Context:\n{context}\n\n", "") == plain


def test_build_prompt_is_brace_safe():
    p = build_prompt(CFG, "always_rag", "what is {x}?",
                     [{"title": "T {a}", "text": "body {b}"}, {"title": "U", "text": "v"}])
    assert "what is {x}?" in p and "Wikipedia Title: T {a}\nbody {b}\n\nWikipedia Title: U\nv" in p
    assert "{context}" not in p and "{question}" not in p
    with pytest.raises(ValueError):
        build_prompt(CFG, "always_rag", "q")


@pytest.mark.parametrize("text,expected", [
    ("YES", "yes"), ("Yes.", "yes"), (" no ", "no"), ("NO!", "no"),
    ("", "invalid"), (None, "invalid"), ("Yes, I can.", "invalid"), ("yes or no", "invalid"),
    ("EVET", "invalid"),
])
def test_parse_decision(text, expected):
    assert parse_decision(text) == expected


def test_route_for_invalid_is_retrieve():
    assert route_for("yes") == "llm_only"
    assert route_for("no") == "always_rag"
    assert route_for("invalid") == "always_rag"


def test_api_kwargs_mapping():
    kw = to_api_kwargs({"reasoning_effort": "minimal", "verbosity": "low", "seed": 42,
                        "max_output_tokens": 10})
    assert kw == {"reasoning": {"effort": "minimal"}, "text": {"verbosity": "low"},
                  "max_output_tokens": 10, "extra_body": {"seed": 42}}


class FakeClient:
    calls = 0

    def __init__(self, cfg, sent, concurrency=None):
        pass

    async def aclose(self):
        pass

    async def complete(self, prompt):
        FakeClient.calls += 1
        if "FAIL" in prompt:
            return LLMResult(error="BadRequestError 400", error_kind="permanent", attempts=1)
        return LLMResult(text="YES", input_tokens=10, output_tokens=3, reasoning_tokens=0,
                         cached_input_tokens=0, llm_ms=1.0, status="completed", attempts=1)


def test_resume_skips_successes_and_retries_errors(tmp_path, monkeypatch):
    cfg = CFG.model_copy(update={"paths": CFG.paths.model_copy(update={"results": str(tmp_path)})})
    monkeypatch.setattr(run_baselines, "LLMClient", FakeClient)
    qs = [{"qid": f"q{i}", "dataset": "nq", "split": "test",
           "question": "FAIL?" if i == 0 else f"question {i}"} for i in range(4)]

    def go():
        asyncio.run(run_baselines.run_system(cfg, "llm_decision", qs, dry_run=False, latency=False,
                                             retriever=None, sent={}, dropped={}, run_id="t", yes=True))

    FakeClient.calls = 0
    go()
    assert FakeClient.calls == 4
    go()                                   # only the failed one is called again
    assert FakeClient.calls == 5
    rows = list(read_jsonl(tmp_path / "raw" / "llm_decision.jsonl"))
    assert len(rows) == 5
    ok = [r for r in rows if r["error"] is None]
    assert {r["router_decision"] for r in ok} == {"yes"} and {r["router_route"] for r in ok} == {"llm_only"}
    assert all(r["input_tokens"] == 10 and r["reasoning_tokens"] == 0 for r in ok)


def test_full_run_needs_yes(tmp_path, monkeypatch):
    cfg = CFG.model_copy(update={"paths": CFG.paths.model_copy(update={"results": str(tmp_path)})})
    monkeypatch.setattr(run_baselines, "LLMClient", FakeClient)
    qs = [{"qid": "q1", "dataset": "nq", "split": "test", "question": "q"}]
    with pytest.raises(SystemExit):
        asyncio.run(run_baselines.run_system(cfg, "llm_only", qs, dry_run=False, latency=False,
                                             retriever=None, sent={}, dropped={}, run_id="t", yes=False))
