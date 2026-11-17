import pandas as pd
import pytest

from src import evaluate
from src.annotation import agreement, stratified_sample
from src.config import load_config
from src.judge import build_judge_prompt, gold_list, parse_verdict

CFG = load_config()
MODEL = CFG.llm.model


def test_parse_verdict():
    assert parse_verdict("CORRECT") == "correct"
    assert parse_verdict("  incorrect.\n") == "incorrect"
    assert parse_verdict("CORRECT? No, INCORRECT") == "incorrect"   # INCORRECT wins
    assert parse_verdict("Yes") == "invalid"
    assert parse_verdict(None) == "invalid"


def test_gold_list_primary_first_and_capped():
    q = {"answers_primary": ["Ringo Starr"], "answers": ["RINGO", "Ringo Starr", "Richard Starkey"]}
    assert gold_list(q, 2) == ["Ringo Starr", "RINGO"]


def test_judge_prompt_has_question_golds_and_answer():
    q = {"question": "Who?", "answers_primary": ["A"], "answers": ["A", "B"]}
    p = build_judge_prompt(CFG, q, "  B \n")
    assert "Question: Who?" in p and "A | B" in p and "Model answer: B\n" in p
    assert p.rstrip().endswith("Reply with only CORRECT or INCORRECT.")


def _rec(qid, system, pred, error=None):
    return {"model": MODEL, "system": system, "qid": qid, "prediction": pred, "input_tokens": 10,
            "output_tokens": 5, "reasoning_tokens": 0, "cached_input_tokens": 0, "error": error,
            "router_decision": "no", "status": "completed"}


def test_judge_answer_set_uses_verdicts():
    qs = {"q1": {"qid": "q1", "dataset": "nq", "split": "test", "answers": ["Christopher Allen Lloyd"],
                 "answers_primary": ["Christopher Allen Lloyd"]}}
    recs = {"llm_only": {"q1": _rec("q1", "llm_only", "Christopher Lloyd")},
            "always_rag": {"q1": _rec("q1", "always_rag", "Michael J. Fox", error="incomplete")},
            "llm_decision": {"q1": _rec("q1", "llm_decision", "NO")}}
    evaluate.JUDGE_VERDICTS.clear()
    evaluate.JUDGE_VERDICTS.update({(MODEL, "llm_only", "q1"): "correct",
                                    (MODEL, "always_rag", "q1"): "correct"})
    rows = {(r["system"]): r for r in evaluate.build_rows(CFG, qs, recs, evaluate.JUDGE_SET)}
    assert rows["llm_only"]["correct"] is True              # judge accepts what accuracy misses
    assert rows["llm_only"]["accuracy"] == 0.0               # the accuracy score itself is unchanged
    assert rows["always_rag"]["correct"] is False            # a failed call stays wrong
    assert rows["oracle_realistic"]["route"] == "llm_only"
    plain = {(r["system"]): r for r in evaluate.build_rows(CFG, qs, recs, "all")}
    assert plain["llm_only"]["correct"] is False
    evaluate.JUDGE_VERDICTS.clear()


def test_stratified_sample_balances_cells_and_records_weights():
    rows = [{"dataset": d, "accuracy_correct": c, "i": i}
            for d in ("nq", "musique") for c in (True, False) for i in range(50 if c else 10)]
    s = stratified_sample(rows, 20, seed=1)
    assert len(s) == 20 and len({r["item_id"] for r in s}) == 20
    cells = pd.DataFrame(s).groupby(["dataset", "accuracy_correct"]).size()
    assert (cells == 5).all()
    big = [r for r in s if r["accuracy_correct"]][0]
    assert big["cell_size"] == 50 and big["cell_sampled"] == 5


def test_agreement_counts_and_weights():
    lab = pd.DataFrame({
        "answer_model": [MODEL] * 4, "system": ["llm_only"] * 4, "qid": ["a", "b", "c", "d"],
        "ref_correct": [True, True, False, False], "labeller": ["human"] * 4,
        "item_id": ["A1", "A2", "A3", "A4"], "accuracy_correct": [True, False, False, True],
        "cell_size": [10, 10, 10, 10], "cell_sampled": [2, 2, 2, 2]})
    verdicts = {(MODEL, "llm_only", q): v for q, v in zip("abcd", ["correct", "correct", "incorrect", "incorrect"])}
    t = agreement(lab, verdicts, MODEL, {"opus": {"A1": True, "A2": False}}).set_index("criterion")
    assert t.loc["labels: opus", "n_labelled"] == 2 and t.loc["labels: opus", "agreement"] == 0.5
    assert t.loc["judge: own model's answers", "n_labelled"] == 4
    assert "judge: other models' answers" not in t.index
    assert t.loc["accuracy", "agreement"] == 0.5
    assert t.loc["accuracy", "missed_correct"] == 1 and t.loc["accuracy", "accepted_wrong"] == 1
    assert t.loc["judge", "agreement"] == 1.0 and t.loc["judge", "cohen_kappa"] == pytest.approx(1.0)
