import math

import pytest

from src.question_meta import assign_tertile, build_records, musique_hops, tertile_edges


def _q(dataset, source_id, hop):
    return {"qid": f"{dataset}__{source_id}", "dataset": dataset, "source_id": source_id,
            "hop_type": hop, "question": "q"}


def test_musique_hops_collapse_subtypes():
    assert musique_hops("2hop__1_2") == 2
    assert musique_hops("3hop1__1_2") == 3
    assert musique_hops("3hop2__1_2") == 3
    assert musique_hops("4hop3__1_2") == 4
    with pytest.raises(ValueError):
        musique_hops("nohop")


def test_tertile_boundary_goes_to_lower_bin():
    assert assign_tertile(1.0, 1.0, 2.0) == "low"
    assert assign_tertile(2.0, 1.0, 2.0) == "mid"
    assert assign_tertile(2.1, 1.0, 2.0) == "high"


def test_tertile_edges_are_linear_quantiles():
    q33, q66 = tertile_edges([1.0, 2.0, 3.0])
    assert q33 == pytest.approx(1 + 2 / 3)
    assert q66 == pytest.approx(2 + 1 / 3)


def test_build_records_joins_sources_and_leaves_nq_blank():
    questions = [
        _q("nq", "dev_1", "single"),
        _q("triviaqa", "dev_2", "single"),
        _q("hotpotqa", "h1", "multi"),
        _q("musique", "4hop2__9_8", "multi"),
        _q("2wikimultihopqa", "w1", "multi"),
        _q("popqa", "10", "single"),
        _q("popqa", "11", "single"),
        _q("popqa", "12", "single"),
    ]
    pop = {"10": 10, "11": 100, "12": 1000}
    rows, edges = build_records(
        questions,
        hotpot={"h1": {"level": "hard", "type": "bridge"}},
        wiki={"w1": "comparison"},
        pop=pop,
        edges=None,
    )
    by = {r["qid"]: r for r in rows}
    nq = by["nq__dev_1"]
    assert nq["hop_type"] == "single"
    assert nq["hotpot_level"] is None and nq["s_pop"] is None and nq["pop_tertile"] is None
    assert by["hotpotqa__h1"]["hotpot_level"] == "hard"
    assert by["hotpotqa__h1"]["hotpot_type"] == "bridge"
    assert by["musique__4hop2__9_8"]["musique_hops"] == 4
    assert by["2wikimultihopqa__w1"]["wiki_type"] == "comparison"
    assert by["popqa__10"]["pop_tertile"] == "low"
    assert by["popqa__12"]["pop_tertile"] == "high"
    assert edges["n"] == 3
    # reused edges are not recomputed
    again, edges2 = build_records(questions, {"h1": {"level": "hard", "type": "bridge"}},
                                  {"w1": "comparison"}, pop, edges)
    assert edges2 is edges
    assert [r["pop_tertile"] for r in again if r["dataset"] == "popqa"] == \
           [r["pop_tertile"] for r in rows if r["dataset"] == "popqa"]


def test_build_records_rejects_nonpositive_popularity():
    with pytest.raises(ValueError):
        build_records([_q("popqa", "1", "single")], {}, {}, {"1": 0}, None)


def test_log_matches_assignment():
    questions = [_q("popqa", str(i), "single") for i in range(9)]
    pop = {str(i): 10 ** i for i in range(9)}
    rows, edges = build_records(questions, {}, {}, pop, None)
    for r in rows:
        got = assign_tertile(math.log10(r["s_pop"]), edges["q33_log10"], edges["q66_log10"])
        assert r["pop_tertile"] == got
