import numpy as np
import pytest

from src.bootstrap import paired_mean_diff, paired_stat_diff
from src.config import load_config
from src.cost import call_usd
from src.evaluate import build_rows
from src.records import final_records
from src.io_utils import write_jsonl
from src.leakage import leak_flags
from src.routers import oracle_route, outcome_label

CFG = load_config()
MODEL = CFG.llm.model


def test_outcome_labels_and_oracle():
    assert outcome_label(True, True) == "both_ok"
    assert outcome_label(True, False) == "rag_hurts"
    assert outcome_label(False, True) == "retrieval_needed"
    assert outcome_label(False, False) == "both_fail"
    assert oracle_route(True, False) == "llm_only"
    assert oracle_route(True, True) == "llm_only"
    assert oracle_route(False, True) == "always_rag"
    assert oracle_route(False, False) == "llm_only"         # both wrong -> the cheaper path


def test_call_cost():
    p = CFG.pricing[MODEL]
    rec = {"model": MODEL, "input_tokens": 1000, "cached_input_tokens": 200, "output_tokens": 50}
    expect = (800 * p["input_per_1m"] + 200 * p["cached_input_per_1m"] + 50 * p["output_per_1m"]) / 1e6
    assert call_usd(CFG, rec) == pytest.approx(expect)
    assert call_usd(CFG, {"model": MODEL, "input_tokens": None}) == 0.0     # rejected prompt: not billed


def test_final_record_prefers_last_success(tmp_path):
    p = tmp_path / "x.jsonl"
    write_jsonl(p, [{"qid": "a", "error": "flagged", "n": 1}, {"qid": "a", "error": None, "n": 2},
                    {"qid": "b", "error": "x", "n": 3}, {"qid": "b", "error": "y", "n": 4}])
    final, calls = final_records(p)
    assert final["a"]["n"] == 2 and final["b"]["n"] == 4 and calls == {"a": 2, "b": 2}


def _rec(pred, inp, out, error=None, decision=None):
    return {"model": MODEL, "prediction": pred, "input_tokens": inp, "output_tokens": out,
            "reasoning_tokens": 0, "cached_input_tokens": 0, "error": error, "router_decision": decision,
            "status": "completed" if error is None else "incomplete"}


def test_build_rows_composes_routers():
    qs = {"q1": {"qid": "q1", "dataset": "nq", "split": "test", "answers": ["Paris"], "answers_primary": ["Paris"]},
          "q2": {"qid": "q2", "dataset": "nq", "split": "test", "answers": ["Rome"], "answers_primary": ["Rome"]}}
    recs = {
        "llm_only": {"q1": _rec("Paris", 40, 20), "q2": _rec("Milan", 40, 20)},
        "always_rag": {"q1": _rec("Lyon", 700, 20), "q2": _rec("Rome", 700, 20, error="incomplete")},
        "llm_decision": {"q1": _rec("YES", 40, 19, decision="yes"), "q2": _rec("NO", 40, 19, decision="no")},
    }
    rows = {(r["qid"], r["system"]): r for r in build_rows(CFG, qs, recs, "all")}
    assert rows[("q1", "llm_only")]["label"] == "rag_hurts"
    assert rows[("q2", "always_rag")]["correct"] is False          # failed call counts as wrong
    assert rows[("q2", "always_rag")]["generation_usd"] > 0          # ...but its tokens are billed
    assert rows[("q1", "oracle")]["route"] == "llm_only" and rows[("q1", "oracle")]["correct"]
    assert rows[("q2", "oracle")]["route"] == "llm_only"             # both wrong -> cheaper
    dr1, dr2 = rows[("q1", "llm_decision_router")], rows[("q2", "llm_decision_router")]
    assert dr1["route"] == "llm_only" and dr1["retrieval_calls"] == 0 and dr1["correct"]
    assert dr2["route"] == "always_rag" and dr2["retrieval_calls"] == 1
    assert dr1["router_usd"] == pytest.approx(call_usd(CFG, recs["llm_decision"]["q1"]))
    assert dr1["total_usd"] == pytest.approx(dr1["generation_usd"] + dr1["router_usd"])


def test_leak_flags():
    assert leak_flags({"prediction": "Paris", "status": "completed", "input_tokens": 5})["leak"] is False
    f = leak_flags({"prediction": "Hats? Wait. The museum is about hats.", "status": "completed",
                    "input_tokens": 5})
    assert f["marker"] and f["leak"]
    assert leak_flags({"prediction": "x", "error_kind": "incomplete"})["incomplete"]
    assert leak_flags({"prediction": " ".join(["w"] * 17), "status": "completed", "input_tokens": 5})["long"]


def test_bootstrap_ci_contains_true_difference():
    rng = np.random.default_rng(0)
    a = rng.binomial(1, 0.6, 2000)
    b = rng.binomial(1, 0.5, 2000)
    m, lo, hi = paired_mean_diff(a, b, n_boot=2000)
    assert lo < m < hi and lo > 0
    m, lo, hi = paired_mean_diff(a, a, n_boot=1000)
    assert m == lo == hi == 0
    strata = np.repeat([0, 1], 1000)
    m2, lo2, hi2 = paired_mean_diff(a, b, strata, n_boot=2000)
    assert m2 == pytest.approx((a - b).mean())
    d, lo, hi = paired_stat_diff(np.arange(100) + 10.0, np.arange(100), n_boot=1000)
    assert d == 10 and lo == hi == 10
