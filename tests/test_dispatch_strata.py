import asyncio

import pandas as pd
import pytest

from src.config import load_config
from src.dispatch import dispatch_rows
from src.llm_gemini import tokens_from_gemini_usage
from src.llm_ollama import parse_chat, request_body
from src.paths import out_path
from src.run_baselines import run_system
from src.strata import compare_table, stratum_table, with_meta
from tests.test_systems import FakeClient

CFG = load_config()
NANO = "gpt-5-nano-2025-08-07"


def _cfg_small():
    return CFG.model_copy(update={"eval": CFG.eval.model_copy(update={"bootstrap_samples": 40})})


def test_tokens_add_thoughts_when_total_says_they_are_separate():
    usage = {"prompt_token_count": 10, "candidates_token_count": 4, "thoughts_token_count": 6,
             "cached_content_token_count": 0, "total_token_count": 20}
    got = tokens_from_gemini_usage(usage)
    assert got["output_tokens"] == 10 and got["reasoning_tokens"] == 6
    assert got["input_tokens"] == 10


def test_tokens_do_not_add_thoughts_already_inside_candidates():
    usage = {"prompt_token_count": 10, "candidates_token_count": 10, "thoughts_token_count": 6,
             "total_token_count": 20}
    assert tokens_from_gemini_usage(usage)["output_tokens"] == 10


def test_tokens_with_no_thoughts_match_either_rule():
    usage = {"prompt_token_count": 10, "candidates_token_count": 3, "thoughts_token_count": 0,
             "total_token_count": 13}
    assert tokens_from_gemini_usage(usage)["output_tokens"] == 3
    assert tokens_from_gemini_usage(None) is None
    with pytest.raises(ValueError):
        tokens_from_gemini_usage({"prompt_token_count": 10, "candidates_token_count": 3,
                                  "thoughts_token_count": 5, "total_token_count": 99})


def test_gemini_overlay_replaces_params_and_keeps_datasets():
    cfg = load_config("configs/gemini.yaml")
    assert cfg.llm.provider == "gemini"
    assert cfg.llm.model == "gemini-2.5-flash-lite"
    assert cfg.llm.api == "generate_content"
    assert "reasoning_effort" not in cfg.llm.params
    assert cfg.llm.params["thinking_budget"] == 0
    assert cfg.data.datasets == CFG.data.datasets
    assert cfg.pricing[NANO]["input_per_1m"] == CFG.pricing[NANO]["input_per_1m"]
    assert cfg.pricing["gemini-2.5-flash-lite"]["output_per_1m"] == 0.40
    assert cfg.pricing["gemini-2.5-flash-lite"]["input_per_1m"] == 0.10


def test_deepseek_peak_hour_doubles_the_off_peak_price():
    from src.cost import call_usd
    rec = {"model": "deepseek-flash", "input_tokens": 1_000_000, "cached_input_tokens": 0,
           "output_tokens": 0}
    weekday_peak = {**rec, "timestamp": "2026-10-21T02:30:00+00:00"}
    weekend = {**rec, "timestamp": "2026-10-24T02:30:00+00:00"}
    assert call_usd(CFG, weekday_peak) == pytest.approx(0.30)
    assert call_usd(CFG, weekend) == pytest.approx(0.15)
    assert call_usd(CFG, rec) == pytest.approx(0.15)


def test_gemini_logs_are_not_written_next_to_openai(tmp_path):
    nano = CFG.model_copy(update={"paths": CFG.paths.model_copy(update={"results": str(tmp_path)})})
    gem = load_config("configs/gemini.yaml").model_copy(
        update={"paths": CFG.paths.model_copy(update={"results": str(tmp_path)})})
    assert out_path(nano, "llm_only", False, False) == tmp_path / "raw" / "llm_only.jsonl"
    assert out_path(gem, "llm_only", False, False) == (
        tmp_path / "models" / "gemini-2.5-flash-lite" / "raw" / "llm_only.jsonl")
    ds = load_config("configs/deepseek.yaml").model_copy(
        update={"paths": CFG.paths.model_copy(update={"results": str(tmp_path)})})
    assert ds.llm.model == "deepseek-flash" and ds.llm.params["reasoning_effort"] == "none"
    assert "verbosity" not in ds.llm.params
    assert out_path(ds, "llm_only", False, False) == (
        tmp_path / "models" / "deepseek-flash" / "raw" / "llm_only.jsonl")
    qwen = load_config("configs/qwen.yaml")
    assert qwen.llm.provider == "ollama" and qwen.llm.ollama_tag == "qwen3.5:4b"
    assert qwen.llm.params["think"] is False
    assert qwen.pricing["qwen3.5-4b"]["output_per_1m"] == 0
    assert out_path(qwen, "llm_only", False, False).parts[-3:] == (
        "qwen3.5-4b", "raw", "llm_only.jsonl")


def test_ollama_parse_rejects_a_thinking_trace_and_keeps_length_tokens():
    text, usage, kind = parse_chat({
        "message": {"content": "OK", "thinking": "step"},
        "prompt_eval_count": 4, "eval_count": 8, "done_reason": "stop"})
    assert kind == "thinking" and usage is None and text == "OK"
    text, usage, kind = parse_chat({
        "message": {"content": "Paris"},
        "prompt_eval_count": 10, "eval_count": 2, "done_reason": "length"})
    assert kind == "incomplete" and usage["output_tokens"] == 2 and text == "Paris"
    body = request_body("qwen3.5:4b", "hi", {"temperature": 0, "max_output_tokens": 256, "think": False})
    assert body["think"] is False and body["options"]["num_predict"] == 256
    assert body["messages"] == [{"role": "user", "content": "hi"}]


def test_gemini_run_uses_its_own_directory(tmp_path, monkeypatch):
    cfg = load_config("configs/gemini.yaml").model_copy(
        update={"paths": CFG.paths.model_copy(update={"results": str(tmp_path)})})
    monkeypatch.setattr("src.run_baselines.open_client", lambda *a, **k: FakeClient(None, None))
    qs = [{"qid": "q1", "dataset": "nq", "split": "test", "question": "fine"}]
    asyncio.run(run_system(cfg, "llm_only", qs, dry_run=False, latency=False, retriever=None,
                           sent={}, dropped={}, run_id="t", yes=True))
    path = tmp_path / "models" / "gemini-2.5-flash-lite" / "raw" / "llm_only.jsonl"
    assert path.exists()
    assert not (tmp_path / "raw" / "llm_only.jsonl").exists()


def test_dispatch_marks_a_filtered_question_sent_but_out_of_comparison():
    questions = {"q1": {"qid": "q1", "dataset": "nq", "split": "test"},
                 "q2": {"qid": "q2", "dataset": "popqa", "split": "dev"}}
    recs = {
        "llm_only": {"q1": {"error": None, "error_kind": None, "router_route": None},
                     "q2": {"error": "blocked", "error_kind": "flagged"}},
        "always_rag": {"q1": {"error": None}, "q2": {"error": None}},
        "llm_decision": {"q1": {"error": None, "router_route": "llm_only"},
                         "q2": {"error": None, "router_route": "always_rag"}},
    }
    meta = {"q1": {"hop_type": "single", "hotpot_level": None, "hotpot_type": None,
                   "musique_hops": None, "wiki_type": None, "s_pop": None, "pop_tertile": None},
            "q2": {"hop_type": "single", "hotpot_level": None, "hotpot_type": None,
                   "musique_hops": None, "wiki_type": None, "s_pop": 10, "pop_tertile": "low"}}
    rows = {(r["qid"], r["system"]): r for r in dispatch_rows(questions, recs, meta, NANO, {"q2"})}
    assert rows[("q1", "llm_only")]["sent"] and rows[("q1", "llm_only")]["status"] == "ok"
    assert rows[("q1", "llm_only")]["in_comparison"]
    assert rows[("q1", "llm_decision")]["route"] == "llm_only"
    assert rows[("q2", "llm_only")]["sent"] and rows[("q2", "llm_only")]["status"] == "flagged"
    assert rows[("q2", "llm_decision")]["in_comparison"] is False
    assert rows[("q2", "llm_only")]["pop_tertile"] == "low"


def _rows():
    def rec(qid, dataset, correct, usd):
        return {"qid": qid, "dataset": dataset, "split": "test", "system": "llm_only",
                "em": float(correct), "f1": float(correct), "accuracy": float(correct),
                "correct": bool(correct), "total_usd": usd}
    return pd.DataFrame([
        rec("a", "musique", 1, 0.1), rec("b", "musique", 0, 0.2), rec("c", "nq", 1, 0.3),
    ])


def test_stratum_table_reports_n_and_interval():
    meta = {
        "a": {"qid": "a", "hop_type": "multi", "musique_hops": 2, "hotpot_level": None,
              "hotpot_type": None, "wiki_type": None, "s_pop": None, "pop_tertile": None},
        "b": {"qid": "b", "hop_type": "multi", "musique_hops": 4, "hotpot_level": None,
              "hotpot_type": None, "wiki_type": None, "s_pop": None, "pop_tertile": None},
        "c": {"qid": "c", "hop_type": "single", "musique_hops": None, "hotpot_level": None,
              "hotpot_type": None, "wiki_type": None, "s_pop": None, "pop_tertile": None},
    }
    # one system only; stratum_table skips empty systems
    frame = with_meta(_rows(), meta)
    table = stratum_table(frame, NANO, _cfg_small())
    hops = table[table.stratum == "musique_hops"].set_index("stratum_value")
    assert list(hops.index) == [2, 4]
    assert hops.loc[2, "n"] == 1 and hops.loc[2, "accuracy"] == 1
    hop = table[table.stratum == "hop_type"].set_index("stratum_value")
    assert hop.loc["multi", "n"] == 2 and hop.loc["single", "n"] == 1
    assert hop.loc["single", "acc_ci_lo"] <= hop.loc["single", "accuracy"] <= hop.loc["single", "acc_ci_hi"]
    assert compare_table({NANO: frame}, _cfg_small()).empty
