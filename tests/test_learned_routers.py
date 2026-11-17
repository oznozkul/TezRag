import numpy as np
import pandas as pd
import pytest

from src.learned_routers import (budget_tau, choose_tau, skip_score, target_label, feature_frames, fit_predict, random_accuracy, routed,
                                 sweep)
from src.router_features import bm25_features, context_of, rule_features


def _table(n=40, seed=0):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, 2, n)
    t = pd.DataFrame({
        "qid": [f"q{i}" for i in range(n)], "split": ["train"] * (n // 2) + ["dev"] * (n // 4) + ["test"] * (n - n // 2 - n // 4),
        "dataset": ["nq", "musique"] * (n // 2), "y": y, "c_lo": y.astype(float),
        "c_ar": rng.integers(0, 2, n).astype(float), "usd_lo": 1.0, "usd_ar": 4.0, "tok_lo": 50, "tok_ar": 700,
        "question": [("who wrote book %d" % i) if i % 2 else ("when did event %d happen" % i) for i in range(n)],
        "bm25_scores": [[10.0 + i % 5, 9.0, 8.0, 7.0, 6.0] for i in range(n)],
        "rag_prompt": ["Context:\nbook event wrote\nQuestion: x"] * n})
    return t


def test_rule_and_bm25_features():
    f = rule_features("How many counties does Ohio have?")
    assert f["wh_how_many"] == 1.0 and f["wh_how"] == 0.0 and f["has_digit"] == 0.0
    assert rule_features("Is Paris in France?")["yes_no"] == 1.0
    b = bm25_features("Who wrote Hamlet", [20.0, 15.0, 10.0], "Context:\nHamlet was written\n\nQuestion: Who wrote Hamlet\nAnswer:")
    assert b["bm25_gap12"] == 5.0 and b["q_overlap"] == pytest.approx(0.5)    # 'wrote' not in context
    assert context_of("no context here") == ""


def test_sweep_and_tau_choice():
    t = pd.DataFrame({"c_lo": [1.0, 1.0, 0.0, 0.0], "c_ar": [1.0, 0.0, 1.0, 0.0],
                      "usd_lo": 1.0, "usd_ar": 4.0, "tok_lo": 10, "tok_ar": 100})
    p = np.array([0.9, 0.8, 0.1, 0.2])
    c = sweep(t, p)
    never = c[c.tau == np.inf].iloc[0]
    assert never.retrieval_rate == 1.0 and never.accuracy == 0.5
    assert choose_tau(c, always_acc=0.5, slack=0.0) == pytest.approx(0.1)   # skip all: still 0.5
    tau = choose_tau(c, always_acc=0.6, slack=0.0)
    assert tau == pytest.approx(0.2)               # skip q0, q1, q3: accuracy 0.75 at rate 0.25
    r = routed(t, p >= tau)
    assert r["correct"].mean() == 0.75 and r["usd"].tolist() == [1.0, 1.0, 4.0, 1.0]
    assert random_accuracy(t, 0.5) == pytest.approx(0.5 + 0.5 * 0.0)


def test_fit_uses_only_training_labels():
    t = _table()
    feats = feature_frames(t)
    emb = np.random.default_rng(1).normal(size=(len(t), 8)).astype(np.float32)
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)
    train = (t.split == "train").to_numpy()
    t2 = t.copy()
    t2.loc[~train, "y"] = 1 - t2.loc[~train, "y"]                    # flip every non-train label
    for name in ("dataset_prior", "rules", "bm25", "tfidf", "embed", "knn", "embed+bm25"):
        p1 = fit_predict(name, t, feats, emb, train, 0)
        p2 = fit_predict(name, t2, feats, emb, train, 0)
        assert np.allclose(p1[~train], p2[~train]), name
        assert ((p1 >= 0) & (p1 <= 1)).all()


def test_knn_excludes_own_label():
    t = _table(20)
    emb = np.eye(20, dtype=np.float32)              # every row is only similar to itself
    train = np.ones(20, bool)
    p = fit_predict("knn", t, feature_frames(t), emb, train, 0)
    own = t.y.to_numpy()
    # with its own label excluded a row cannot be predicted perfectly from itself
    assert not np.allclose(p, own)


def test_targets_and_budget_threshold():
    t = pd.DataFrame({"c_lo": [1.0, 1.0, 0.0, 0.0], "c_ar": [1.0, 0.0, 1.0, 0.0]})
    assert target_label(t, "lo_correct").tolist() == [1, 1, 0, 0]
    assert target_label(t, "need").tolist() == [0, 0, 1, 0]          # both wrong = safe to skip
    assert skip_score(np.array([0.2]), "need")[0] == pytest.approx(0.8)
    s = np.array([0.9, 0.1, 0.5, 0.3, 0.7])
    assert ((s >= budget_tau(s, 0.6)).mean()) == pytest.approx(0.4)
    assert budget_tau(s, 1.0) == np.inf
