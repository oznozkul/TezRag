"""Build a Pyserini (Lucene) BM25 index for one corpus (stage 2).

    python -m src.build_index wiki|hotpotqa|2wikimultihopqa|musique [--threads 8] [--heap 6g]

Indexes `contents` (paragraph text) and `title` as separate fields with Lucene's default English
analyzer (Porter stemming + English stopwords), stores raw docs for prompt construction, and checks the
document count against IRCoT/Adaptive-RAG's expected index size.

Anserini skips documents whose `contents` is empty (Elasticsearch would index them by title only).
The check therefore expects `expected_docs - empty_docs`, and both numbers are recorded. In practice
this only affects HotpotQA (94 abstracts with no text in the 2017 dump).

    python -m src.build_index <name> --verify-only   # re-check an existing index, no rebuild
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import time
from pathlib import Path

from src.build_corpus import EXPECTED_DOCS
from src.config import load_config
from src.io_utils import setup_logging, write_json

log = logging.getLogger("build_index")


def start_jvm(heap: str) -> None:
    """Must run before anything imports pyserini (the JVM can only be configured once)."""
    import jnius_config

    if not jnius_config.vm_running:
        jnius_config.add_options(f"-Xmx{heap}")


def dir_size(p: Path) -> int:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def count_empty(corpus_dir: Path) -> int:
    n = 0
    for fp in sorted(corpus_dir.glob("docs-*.jsonl")):
        with open(fp) as f:
            for line in f:
                if not json.loads(line)["contents"].strip():
                    n += 1
    return n


def verify(cfg, name: str, extra: dict) -> None:
    from pyserini.index.lucene import LuceneIndexReader

    index_dir = cfg.path("indexes") / name
    empty = count_empty(cfg.path("corpora") / name)
    expected_indexable = EXPECTED_DOCS[name] - empty
    stats = LuceneIndexReader(str(index_dir)).stats()
    meta = {"name": name, "docs": stats["documents"], "expected_docs": EXPECTED_DOCS[name],
            "empty_docs_skipped": empty, "expected_indexed": expected_indexable,
            "matches_expected": stats["documents"] == expected_indexable,
            "index_bytes": dir_size(index_dir),
            "analyzer": "Lucene DefaultEnglishAnalyzer (Porter, English stopwords)",
            "fields": ["contents", "title"], **extra}
    write_json(cfg.path("results") / "meta" / f"index_{name}.json", meta)
    log.info("%s", meta)
    if not meta["matches_expected"]:
        raise SystemExit(f"{name}: indexed {meta['docs']} docs, expected {expected_indexable} "
                         f"({EXPECTED_DOCS[name]} minus {empty} empty)")


def run(name: str, threads: int, heap: str, verify_only: bool = False) -> None:
    cfg = load_config()
    corpus_dir = cfg.path("corpora") / name
    index_dir = cfg.path("indexes") / name
    if not any(corpus_dir.glob("docs-*.jsonl")):
        raise SystemExit(f"no shards in {corpus_dir}; run `python -m src.build_corpus {name}` first")
    if verify_only:
        prev_path = cfg.path("results") / "meta" / f"index_{name}.json"
        prev = json.loads(prev_path.read_text()) if prev_path.exists() else {}
        keep = {k: prev[k] for k in ("seconds", "threads", "heap") if k in prev}
        verify(cfg, name, keep)
        return
    if index_dir.exists() and any(index_dir.iterdir()):
        raise SystemExit(f"{index_dir} exists; delete it to rebuild")

    start_jvm(heap)
    from pyserini.pyclass import autoclass  # adds the Anserini fat jar to the classpath, starts the JVM

    args = ["-collection", "JsonCollection", "-input", str(corpus_dir), "-index", str(index_dir),
            "-generator", "DefaultLuceneDocumentGenerator", "-threads", str(threads),
            "-fields", "title", "-storeRaw"]
    log.info("indexing %s with %s", name, " ".join(args))
    t0 = time.time()
    autoclass("io.anserini.index.IndexCollection").main(args)
    seconds = time.time() - t0
    verify(cfg, name, {"seconds": round(seconds, 1), "threads": threads, "heap": heap})


def main() -> None:
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("name", choices=sorted(EXPECTED_DOCS))
    ap.add_argument("--threads", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--heap", default="6g")
    ap.add_argument("--verify-only", action="store_true")
    args = ap.parse_args()
    run(args.name, args.threads, args.heap, args.verify_only)


if __name__ == "__main__":
    main()
