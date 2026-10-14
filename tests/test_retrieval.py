"""Retrieval integration test on a tiny fixture corpus (no downloads needed)."""
import json

import pytest

from src.config import load_config
from src.retrieval import BM25Retriever, dedup_hits

DOCS = [
    ("d1", "Eiffel Tower", "The Eiffel Tower is a wrought-iron lattice tower in Paris, France."),
    ("d2", "Eiffel Tower (copy)", "The Eiffel Tower is a wrought-iron lattice tower in Paris, France."),
    ("d3", "Louvre", "The Louvre is the world's most-visited museum, located in Paris."),
    ("d4", "Big Ben", "Big Ben is the nickname for the Great Bell of the clock in London."),
    ("d5", "Gustave Eiffel", "Gustave Eiffel was a French civil engineer whose company built the tower."),
    ("d6", "Colosseum", "The Colosseum is an elliptical amphitheatre in the centre of Rome."),
]


@pytest.fixture(scope="module")
def retriever(tmp_path_factory):
    root = tmp_path_factory.mktemp("ret")
    corpus = root / "corpora" / "mini"
    corpus.mkdir(parents=True)
    with open(corpus / "docs-000.jsonl", "w") as f:
        for i, t, x in DOCS:
            f.write(json.dumps({"id": i, "contents": x, "title": t}) + "\n")
    from src.build_index import start_jvm

    start_jvm("1g")
    from pyserini.pyclass import autoclass

    autoclass("io.anserini.index.IndexCollection").main(
        ["-collection", "JsonCollection", "-input", str(corpus), "-index", str(root / "indexes" / "mini"),
         "-generator", "DefaultLuceneDocumentGenerator", "-threads", "1", "-fields", "title", "-storeRaw"])
    cfg = load_config()
    cfg = cfg.model_copy(update={"retrieval": cfg.retrieval.model_copy(update={"top_k": 3})})
    return BM25Retriever(cfg, cache_path=root / "cache.sqlite", index_root=root / "indexes")


def test_dedup_hits_keeps_order_and_last_duplicate():
    hits = [("a", 3.0, "Same text "), ("b", 2.5, "other"), ("c", 2.0, "same text")]
    assert dedup_hits(hits, 5) == [("b", 2.5), ("c", 2.0)]


def test_search_dedups_and_ranks(retriever):
    r = retriever.search("Eiffel Tower Paris", "mini")
    assert len(r.ids) == 3
    assert len({p["text"].lower() for p in r.passages}) == 3        # d1/d2 identical text -> one kept
    assert len({"d1", "d2"} & set(r.ids)) == 1
    assert r.scores == sorted(r.scores, reverse=True)
    assert not r.cached and r.retrieval_ms > 0


def test_title_field_is_searched(retriever):
    # "Colosseum" occurs in d6 title and text; both fields contribute to the score
    r = retriever.search("Colosseum", "mini")
    assert r.ids[0] == "d6"


def test_cache_hit_returns_same_result(retriever):
    a = retriever.search("museum in Paris", "mini")
    b = retriever.search("museum in Paris", "mini")
    assert b.cached and b.ids == a.ids and b.retrieval_ms == a.retrieval_ms
    c = retriever.search("museum in Paris", "mini", use_cache=False)
    assert not c.cached and c.ids == a.ids
