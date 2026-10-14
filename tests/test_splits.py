import pytest

from src.config import load_config
from src.io_utils import WriteOnceError, read_jsonl, write_once_jsonl
from src.metrics import normalize_answer
from src.prepare_data import (SPLITS, check_no_leakage, dry_run_subset, sample_and_split,
                              split_sizes)

CFG = load_config()


def _pool(ds: str, n: int) -> list[dict]:
    return [{"qid": f"{ds}__{i}", "dataset": ds, "question": f"question {ds} {i}",
             "answers": ["a"], "source_id": f"{i:05d}"} for i in range(n)]


def test_split_sizes():
    assert split_sizes(500, CFG.data.split_ratios) == {"train": 300, "dev": 100, "test": 100}
    assert sum(split_sizes(7, CFG.data.split_ratios).values()) == 7


def test_split_is_disjoint_and_proportional():
    rows = sample_and_split(CFG, "nq", _pool("nq", 2000))
    by_split = {s: {r["qid"] for r in rows if r["split"] == s} for s in SPLITS}
    assert by_split["train"].isdisjoint(by_split["dev"])
    assert by_split["train"].isdisjoint(by_split["test"])
    assert by_split["dev"].isdisjoint(by_split["test"])
    assert {s: len(v) for s, v in by_split.items()} == split_sizes(CFG.data.n_per_dataset,
                                                                   CFG.data.split_ratios)


def test_split_is_deterministic_and_order_independent():
    pool = _pool("musique", 1000)
    a = sample_and_split(CFG, "musique", pool)
    b = sample_and_split(CFG, "musique", list(reversed(pool)))
    assert [(r["qid"], r["split"]) for r in a] == [(r["qid"], r["split"]) for r in b]


def test_leakage_check_catches_duplicates():
    rows = [{"qid": "x", "question": "q1", "split": "train"},
            {"qid": "x", "question": "q2", "split": "test"}]
    with pytest.raises(AssertionError):
        check_no_leakage(rows)
    rows = [{"qid": "a", "question": "Same Q?", "split": "train"},
            {"qid": "b", "question": "same q", "split": "test"}]
    with pytest.raises(AssertionError):
        check_no_leakage(rows)


def test_dry_run_subset_size():
    rows = sample_and_split(CFG, "nq", _pool("nq", 600))
    sub = dry_run_subset(CFG.model_copy(update={"data": CFG.data.model_copy(
        update={"datasets": ["nq"]})}), rows)
    assert len(sub) == CFG.data.dry_run_n


def test_write_once(tmp_path):
    p = tmp_path / "split.jsonl"
    write_once_jsonl(p, [{"qid": "a"}])
    with pytest.raises(WriteOnceError):
        write_once_jsonl(p, [{"qid": "b"}])
    assert list(read_jsonl(p)) == [{"qid": "a"}]


@pytest.mark.skipif(not (CFG.path("splits") / "split.jsonl").exists(), reason="real split not created")
def test_real_split_has_no_leakage():
    split = list(read_jsonl(CFG.path("splits") / "split.jsonl"))
    questions = {q["qid"]: q for q in read_jsonl(CFG.path("processed") / "questions.jsonl")}
    assert len(split) == len({r["qid"] for r in split}) == len(questions)
    by_split = {s: {r["qid"] for r in split if r["split"] == s} for s in SPLITS}
    for i, a in enumerate(SPLITS):
        for b in SPLITS[i + 1:]:
            assert by_split[a].isdisjoint(by_split[b]), (a, b)
    # also no normalized question text shared between splits
    text = {s: {normalize_answer(questions[q]["question"]) for q in ids} for s, ids in by_split.items()}
    for i, a in enumerate(SPLITS):
        for b in SPLITS[i + 1:]:
            assert text[a].isdisjoint(text[b]), (a, b)
    for ds in CFG.data.datasets:
        counts = {s: sum(r["dataset"] == ds and r["split"] == s for r in split) for s in SPLITS}
        assert counts == split_sizes(CFG.data.n_per_dataset, CFG.data.split_ratios)
