import pandas as pd
import pytest

from src.config import load_config
from src.difficulty import dataset_counts, difficulty_table, question_tiers, tier_of
from src.tables import price_sensitivity_table

CFG = load_config()
SYSTEMS = ("llm_only", "always_rag", "oracle_optimistic", "oracle_realistic", "llm_decision_router")


def _frame(correct: dict[str, bool], rag_correct: bool = True) -> pd.DataFrame:
    """Minimal build_rows-shaped frame: llm_only correctness per qid, fixed token counts."""
    rows = []
    for qid, ok in correct.items():
        for s in SYSTEMS:
            routes_rag = s == "always_rag" or (s == "oracle_realistic" and not ok)
            c = rag_correct if s == "always_rag" else ok
            rows.append({"qid": qid, "dataset": "nq", "system": s, "correct": c, "total_usd": 0.0,
                         "billed_input_tokens": 700 if routes_rag else 40,
                         "input_tokens": 700 if routes_rag else 40, "output_tokens": 20,
                         "router_input_tokens": 40 if s == "llm_decision_router" else 0,
                         "router_output_tokens": 20 if s == "llm_decision_router" else 0,
                         "retrieval_calls": int(routes_rag),
                         "decision": "yes" if s == "llm_decision_router" else None})
    return pd.DataFrame(rows)


def test_tier_boundaries():
    assert tier_of(0, 5) == "very_hard"
    assert tier_of(1, 5) == "hard" and tier_of(2, 4) == "hard"
    assert tier_of(3, 5) == "medium" and tier_of(4, 5) == "medium"
    assert tier_of(5, 5) == "easy"
    with pytest.raises(ValueError):
        tier_of(0, 0)


def test_tiers_leave_own_model_out():
    frames = {"a": _frame({"q1": True, "q2": False}), "b": _frame({"q1": True, "q2": True}),
              "c": _frame({"q1": True, "q2": True})}
    t = question_tiers(frames).set_index(["model", "qid"])
    # q2: a is wrong, b and c right. For a, both others are right -> easy, even though a is wrong.
    assert t.loc[("a", "q2"), "tier"] == "easy" and t.loc[("a", "q2"), "others_correct"] == 2
    # For b, the others are a (wrong) and c (right) -> 1/2 -> hard; b's own answer does not count.
    assert t.loc[("b", "q2"), "tier"] == "hard"
    assert (t.n_other_models == 2).all()


def test_tiers_need_enough_models():
    assert question_tiers({"a": _frame({"q1": True}), "b": _frame({"q1": True})}).empty


def test_difficulty_table_gain_and_counts():
    frames = {m: _frame({"q1": True, "q2": False}, rag_correct=True) for m in "abc"}
    d = difficulty_table(frames, question_tiers(frames), CFG)
    row = d[(d.model == "ALL") & (d.tier == "very_hard") & (d.system == "llm_only")].iloc[0]
    assert row.n == 3 and row.retrieval_gain == pytest.approx(1.0)
    easy = d[(d.model == "a") & (d.tier == "easy") & (d.system == "always_rag")].iloc[0]
    assert easy.retrieval_gain == pytest.approx(0.0) and easy.decision_yes_rate == 1.0
    c = dataset_counts(frames).set_index("dataset")
    assert c.loc["ALL", "0/3"] == 1 and c.loc["ALL", "3/3"] == 1


def test_price_sensitivity_is_scale_free_and_adds_decision_cost():
    frames = {CFG.llm.model: _frame({"q1": True, "q2": False})}
    p = price_sensitivity_table(frames, CFG.pricing)
    r = p[p.price_ratio == "1:1"].set_index("system")
    # always_rag 720/q; llm_only 60/q; realistic oracle (q1 llm_only, q2 rag) = 390/q; decision 60/q
    assert r.loc["always_rag", "relative_cost"] == pytest.approx(1.0)
    assert r.loc["oracle_realistic", "relative_cost"] == pytest.approx(390 / 720)
    assert r.loc["oracle_optimistic", "relative_cost"] == pytest.approx(60 / 720)
    assert r.loc["oracle_realistic+decision", "relative_cost"] == pytest.approx(450 / 720)
    assert r.loc["llm_decision_router", "breakeven_skip_rate"] == pytest.approx(60 / 660)
    assert any(lbl.startswith("actual") for lbl in p.price_ratio)
