"""Convert raw corpora to Pyserini JsonCollection shards (stage 2).

    python -m src.build_corpus wiki|hotpotqa|2wikimultihopqa|musique

Mirrors IRCoT/Adaptive-RAG retriever_server/build_index.py:
  wiki             DPR psgs_w100.tsv (id, text, title), no dedup                 -> 21,015,324 docs
  hotpotqa         HotpotQA 2017-10 Wikipedia abstracts, text sentences joined   ->  5,233,329 docs
  2wikimultihopqa  train/dev/test `context` paragraphs, dedup on title+text hash ->    430,225 docs
  musique          ans+full train/dev/test `paragraphs`, dedup on title+text hash ->   139,416 docs

Each doc: {"id", "contents": paragraph text, "title"}; `title` is indexed as a second field so the
query can match title and text separately, like the ES `title_paragraph_text` mode.
"""
from __future__ import annotations

import argparse
import bz2
import csv
import gzip
import hashlib
import json
import logging
import sys
import time
from pathlib import Path
from typing import Iterator

from src.config import load_config
from src.io_utils import setup_logging, write_json

log = logging.getLogger("build_corpus")

EXPECTED_DOCS = {
    "wiki": 21_015_324,
    "hotpotqa": 5_233_329,
    "2wikimultihopqa": 430_225,
    "musique": 139_416,
}
SHARD_SIZE = 1_000_000


def _hash_id(title: str, text: str) -> str:
    return hashlib.sha256(" ".join([title, text]).encode()).hexdigest()[:32]


def iter_wiki(raw: Path) -> Iterator[dict]:
    csv.field_size_limit(sys.maxsize)
    with gzip.open(raw / "dpr_wiki/psgs_w100.tsv.gz", "rt", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        assert header == ["id", "text", "title"], header
        for pid, text, title in reader:
            yield {"id": pid, "contents": text, "title": title}


def iter_hotpotqa(raw: Path) -> Iterator[dict]:
    base = raw / "hotpotqa_wiki/extracted"
    files = sorted(base.glob("*/*/wiki_*.bz2"))
    if not files:
        raise FileNotFoundError(f"no wiki_*.bz2 under {base}")
    for fp in files:
        with bz2.open(fp, "rt") as f:
            for line in f:
                j = json.loads(line)
                text = " ".join(s.strip() for s in j["text"]).strip()
                yield {"id": str(j["id"]), "contents": text, "title": j["title"].strip()}


def _dedup(pairs: Iterator[tuple[str, str]]) -> Iterator[dict]:
    seen: set[str] = set()
    for title, text in pairs:
        h = _hash_id(title, text)
        if h in seen:
            continue
        seen.add(h)
        yield {"id": h, "contents": text, "title": title}


def iter_2wiki(raw: Path) -> Iterator[dict]:
    base = raw / "2wiki_raw/extracted/data_ids"

    def pairs():
        for split in ("train", "dev", "test"):
            for inst in json.load(open(base / f"{split}.json")):
                for title, sents in inst["context"]:
                    yield title, " ".join(sents)

    return _dedup(pairs())


def iter_musique(raw: Path) -> Iterator[dict]:
    base = raw / "musique_raw/extracted/data"

    def pairs():
        for kind in ("ans", "full"):
            for split in ("train", "dev", "test"):
                with open(base / f"musique_{kind}_v1.0_{split}.jsonl") as f:
                    for line in f:
                        if line.strip():
                            for p in json.loads(line)["paragraphs"]:
                                yield p["title"], p["paragraph_text"]

    return _dedup(pairs())


ITERATORS = {"wiki": iter_wiki, "hotpotqa": iter_hotpotqa,
             "2wikimultihopqa": iter_2wiki, "musique": iter_musique}


def run(name: str) -> None:
    cfg = load_config()
    out_dir = cfg.path("corpora") / name
    if out_dir.exists() and any(out_dir.glob("docs-*.jsonl")):
        raise SystemExit(f"{out_dir} already has shards; delete it to rebuild")
    out_dir.mkdir(parents=True, exist_ok=True)

    t0, n, shard, f = time.time(), 0, -1, None
    ids: set[str] = set()
    for doc in ITERATORS[name](cfg.path("raw")):
        if doc["id"] in ids:
            raise ValueError(f"duplicate doc id {doc['id']}")
        ids.add(doc["id"])
        if n % SHARD_SIZE == 0:
            if f:
                f.close()
            shard += 1
            f = open(out_dir / f"docs-{shard:03d}.jsonl", "w")
        f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        n += 1
        if n % 1_000_000 == 0:
            log.info("%s: %d docs (%.0fs)", name, n, time.time() - t0)
    if f:
        f.close()

    meta = {"name": name, "docs": n, "expected_docs": EXPECTED_DOCS[name],
            "matches_expected": n == EXPECTED_DOCS[name], "shards": shard + 1,
            "seconds": round(time.time() - t0, 1)}
    write_json(cfg.path("results") / "meta" / f"corpus_{name}.json", meta)
    log.info("%s", meta)
    if n != EXPECTED_DOCS[name]:
        log.error("%s: %d docs, IRCoT/Adaptive-RAG expect %d", name, n, EXPECTED_DOCS[name])
        raise SystemExit(1)


def main() -> None:
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("name", choices=sorted(ITERATORS))
    run(ap.parse_args().name)


if __name__ == "__main__":
    main()
