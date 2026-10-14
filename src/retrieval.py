"""BM25 retrieval over Pyserini indexes, with a persistent SQLite cache.

Mirrors the Elasticsearch retriever used by IRCoT/Adaptive-RAG (`title_paragraph_text` mode):
  - BM25 k1/b from config (ES 7.10 defaults 1.2/0.75)
  - query matched against `contents` (paragraph text) and `title`, scores summed (ES bool/should)
  - fetch `candidate_k` hits, dedup by stripped+lowercased paragraph text (first-seen order, last hit
    wins, as in IRCoT's elasticsearch_retriever.py), re-sort by score, keep top_k

retrieval_ms covers search + stored-doc fetch + dedup, measured with perf_counter_ns. A cache hit
returns the originally measured retrieval_ms and sets cached=True; latency runs bypass the cache.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from src.config import Config

FIELDS = {"contents": 1.0, "title": 1.0}


@dataclass
class RetrievalResult:
    corpus: str
    query: str
    ids: list[str]
    scores: list[float]
    retrieval_ms: float
    cached: bool
    passages: list[dict] = field(default_factory=list)   # [{"id", "title", "text"}]


def index_fingerprint(index_dir: Path) -> str:
    """Identifies an index build (file names + sizes); part of the cache key."""
    h = hashlib.sha256()
    for f in sorted(p for p in index_dir.iterdir() if p.is_file()):
        h.update(f"{f.name}:{f.stat().st_size}\n".encode())
    return h.hexdigest()[:16]


def dedup_hits(hits: list[tuple[str, float, str]], top_k: int) -> list[tuple[str, float]]:
    """hits: (docid, score, text) in engine order -> top_k (docid, score) after IRCoT-style dedup."""
    by_text: dict[str, tuple[str, float]] = {}
    for docid, score, text in hits:
        by_text[text.strip().lower()] = (docid, score)
    return sorted(by_text.values(), key=lambda x: -x[1])[:top_k]


class RetrievalCache:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS retrieval (
            key TEXT PRIMARY KEY, corpus TEXT, index_fp TEXT, query TEXT, top_k INT,
            candidate_k INT, k1 REAL, b REAL, ids TEXT, scores TEXT, retrieval_ms REAL,
            created_at TEXT)""")
        self.db.commit()

    @staticmethod
    def key(*parts) -> str:
        return hashlib.sha256(json.dumps(parts).encode()).hexdigest()

    def get(self, key: str) -> tuple[list[str], list[float], float] | None:
        row = self.db.execute("SELECT ids, scores, retrieval_ms FROM retrieval WHERE key=?",
                              (key,)).fetchone()
        return (json.loads(row[0]), json.loads(row[1]), row[2]) if row else None

    def put(self, key: str, corpus: str, index_fp: str, query: str, top_k: int, candidate_k: int,
            k1: float, b: float, ids: list[str], scores: list[float], ms: float) -> None:
        self.db.execute("INSERT OR IGNORE INTO retrieval VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (key, corpus, index_fp, query, top_k, candidate_k, k1, b, json.dumps(ids),
                         json.dumps(scores), ms, datetime.now(timezone.utc).isoformat()))
        self.db.commit()


class BM25Retriever:
    def __init__(self, cfg: Config, use_cache: bool = True, cache_path: Path | None = None,
                 index_root: Path | None = None):
        self.cfg = cfg
        self.rc = cfg.retrieval
        self.index_root = index_root or cfg.path("indexes")
        self.cache = RetrievalCache(cache_path or cfg.path("cache") / "retrieval.sqlite") \
            if use_cache else None
        self._searchers: dict = {}
        self._fp: dict[str, str] = {}

    def _searcher(self, corpus: str):
        if corpus not in self._searchers:
            from pyserini.search.lucene import LuceneSearcher

            index_dir = self.index_root / corpus
            if not index_dir.exists():
                raise FileNotFoundError(f"index {index_dir} missing; run src.build_index {corpus}")
            s = LuceneSearcher(str(index_dir))
            s.set_bm25(self.rc.bm25.k1, self.rc.bm25.b)
            self._searchers[corpus] = s
            self._fp[corpus] = index_fingerprint(index_dir)
        return self._searchers[corpus]

    def fetch(self, corpus: str, ids: list[str]) -> list[dict]:
        s = self._searcher(corpus)
        out = []
        for docid in ids:
            d = json.loads(s.doc(docid).raw())
            out.append({"id": docid, "title": d.get("title", ""), "text": d["contents"]})
        return out

    def _search_uncached(self, corpus: str, query: str) -> tuple[list[str], list[float], float]:
        s = self._searcher(corpus)
        t0 = time.perf_counter_ns()
        hits = s.search(query, self.rc.candidate_k, fields=FIELDS)
        triples = [(h.docid, h.score, json.loads(h.lucene_document.get("raw"))["contents"])
                   for h in hits]
        if self.rc.dedup_by_text:
            kept = dedup_hits(triples, self.rc.top_k)
        else:
            kept = [(d, sc) for d, sc, _ in triples[: self.rc.top_k]]
        ms = (time.perf_counter_ns() - t0) / 1e6
        return [d for d, _ in kept], [float(sc) for _, sc in kept], ms

    def search(self, query: str, corpus: str, with_passages: bool = True,
               use_cache: bool = True) -> RetrievalResult:
        self._searcher(corpus)
        bm = self.rc.bm25
        key = RetrievalCache.key(corpus, self._fp[corpus], query, self.rc.top_k,
                                 self.rc.candidate_k, bm.k1, bm.b, self.rc.dedup_by_text)
        hit = self.cache.get(key) if (self.cache and use_cache) else None
        if hit:
            ids, scores, ms = hit
            cached = True
        else:
            ids, scores, ms = self._search_uncached(corpus, query)
            cached = False
            if self.cache and use_cache:
                self.cache.put(key, corpus, self._fp[corpus], query, self.rc.top_k,
                               self.rc.candidate_k, bm.k1, bm.b, ids, scores, ms)
        res = RetrievalResult(corpus, query, ids, scores, ms, cached)
        if with_passages:
            res.passages = self.fetch(corpus, ids)
        return res
