import numpy as np
import pandas as pd
import pytest

from src.cascade import abstains, esc_threshold_for_budget, evaluate_policy, no_loss_threshold
from src.config import load_config

CFG = load_config()


def test_abstain_rule():
    assert abstains("I don't know.", False) and abstains("Paris?", False) and abstains("", False)
    assert abstains("Paris", True)                       # failed call escalates
    assert not abstains("Christopher Lloyd", False)


def test_cascade_cost_and_accuracy():
    t = pd.DataFrame({"c_lo": [1.0, 0.0, 0.0, 1.0], "c_ar": [1.0, 1.0, 0.0, 0.0],
                      "usd_lo": 1.0, "usd_ar": 4.0, "tok_lo": 10, "tok_ar": 100,
                      "dataset": ["nq", "nq", "musique", "musique"]})
    r = evaluate_policy(CFG, "m", "x", t, np.array([False, True, False, False]), "p")
    assert r["accuracy"] == 0.75                         # q1 rescued, q3 kept its own right answer
    assert r["relative_cost"] == pytest.approx((4 * 1.0 + 4.0) / (4 * 4.0))
    assert r["breakeven_escalation"] == pytest.approx(0.75)
    assert r["cost_unit"] == "usd"


def test_thresholds():
    p = np.array([0.9, 0.1, 0.5, 0.3])
    assert ((p >= esc_threshold_for_budget(p, 0.5)).mean()) == 0.5
    t = pd.DataFrame({"c_lo": [0.0, 1.0, 1.0, 1.0], "c_ar": [1.0, 1.0, 1.0, 0.0]})
    tau = no_loss_threshold(t, p)
    assert tau == pytest.approx(0.9)                     # escalate only q0: accuracy 1.0 >= 0.75
