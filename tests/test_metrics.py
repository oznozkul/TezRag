import pytest

from src.metrics import accuracy_golds, contains, exact_match, f1, is_correct, normalize_answer, score


def test_normalize_squad_rules():
    assert normalize_answer("The  Beatles!") == "beatles"
    assert normalize_answer("An apple, a day") == "apple day"
    assert normalize_answer("  U.S.A. ") == "usa"
    assert normalize_answer("Theatre") == "theatre"          # article removal is word-bounded
    assert normalize_answer(None) == ""
    assert normalize_answer("") == ""
    assert normalize_answer("!!!") == ""


def test_exact_match_and_f1():
    assert exact_match("the Eiffel Tower", "Eiffel Tower") == 1.0
    assert exact_match("Eiffel", "Eiffel Tower") == 0.0
    assert f1("Eiffel", "Eiffel Tower") == pytest.approx(2 * 1 * 0.5 / 1.5)
    assert f1("Paris France", "Paris") == pytest.approx(2 * 0.5 * 1 / 1.5)
    assert f1("London", "Paris") == 0.0


def test_accuracy_is_token_bounded_containment():
    assert contains("It was Linda Davis.", "Linda Davis") == 1.0
    assert contains("Canada", "ca") == 0.0                   # no sub-word matches
    assert contains("in ca", "CA") == 1.0
    assert contains("anything", "!!!") == 0.0                # empty gold never matches


def test_multiple_answers_take_max():
    s = score("Helicopter", ["🚁", "Helicopters", "Helicopter"])
    assert s == {"em": 1.0, "f1": 1.0, "accuracy": 1.0}
    s = score("a cargo helicopter", ["Helicopter", "Cargo helicopter"])
    assert s["em"] == 1.0                                     # second gold matches exactly


def test_empty_prediction():
    s = score("", ["Paris"])
    assert s == {"em": 0.0, "f1": 0.0, "accuracy": 0.0}
    s = score(None, ["Paris"])
    assert s == {"em": 0.0, "f1": 0.0, "accuracy": 0.0}


def test_yes_no():
    assert score("Yes.", ["yes"])["em"] == 1.0
    assert score("no", ["yes"])["accuracy"] == 0.0


def test_all_golds_empty_raises():
    with pytest.raises(ValueError):
        score("x", ["!!!"])


def test_is_correct():
    s = {"em": 0.0, "f1": 0.6, "accuracy": 1.0}
    assert is_correct(s, "accuracy")
    assert not is_correct(s, "em")
    assert is_correct(s, "f1", 0.5)
    assert not is_correct(s, "f1", 0.7)


def test_short_alias_ignored_for_accuracy_only():
    golds, primary = ["India", "in", "IN"], ["India"]
    s = score("born in Delhi", golds, primary, min_alias_chars=3)
    assert s["accuracy"] == 0.0                              # "in" must not count
    assert score("born in Delhi", golds)["accuracy"] == 1.0  # without the policy it would
    s = score("IN", golds, primary, min_alias_chars=3)
    assert s["em"] == 1.0                                     # EM still uses every alias
    assert s["accuracy"] == 0.0
    s = score("no", ["Norwegian", "no"], ["Norwegian"], min_alias_chars=3)
    assert s["accuracy"] == 0.0 and s["em"] == 1.0


def test_short_primary_is_kept():
    assert accuracy_golds(["US", "U.S."], ["US"], 3) == ["US"]
    assert score("the US", ["US"], ["US"], min_alias_chars=3)["accuracy"] == 1.0


def test_single_gold_answer_set():
    # comparison report for multi-hop datasets: golds = the single IRCoT answer
    assert score("Helicopters", ["Helicopter"], ["Helicopter"], 3)["accuracy"] == 0.0


def test_adaptive_rag_gold_set():
    from src.config import load_config
    from src.evaluate import golds_for

    cfg = load_config()
    tq = {"dataset": "triviaqa", "answers": ["Titfer", "Hat", "Hats"], "answers_primary": ["Titfer"]}
    hp = {"dataset": "hotpotqa", "answers": ["yes"], "answers_primary": ["yes"]}
    wk = {"dataset": "2wikimultihopqa", "answers": ["Norwegian", "no"], "answers_primary": ["Norwegian"]}
    assert golds_for(cfg, tq, "adaptive_rag") == (["Titfer", "Hat", "Hats"], None, 0)
    assert golds_for(cfg, hp, "adaptive_rag") == (["yes"], None, 0)
    assert golds_for(cfg, wk, "adaptive_rag") == (["Norwegian"], None, 0)
    assert golds_for(cfg, wk, "all") == (["Norwegian", "no"], ["Norwegian"], 3)
