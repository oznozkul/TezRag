"""Load each source pool into the common question format.

Only questions and gold answers are read. Ready-made contexts (DPR positive/negative ctxs,
HotpotQA/2Wiki/MuSiQue `contexts`/`paragraphs`) are never copied into our records.

Pools match Adaptive-RAG (Jeong et al., 2024):
  nq, triviaqa         -> DPR biencoder-{nq,trivia}-dev.json  (same files Adaptive-RAG samples from)
  hotpotqa, 2wiki, musique -> IRCoT processed_data/<ds>/dev.jsonl (pool of IRCoT/Adaptive-RAG test sets)
  popqa                -> akariasai/PopQA test.tsv (not in Adaptive-RAG; replaces SQuAD)

Answer variants:
  IRCoT's processed files keep only one gold span, so aliases are joined from raw files:
  2Wiki: id_aliases.json aliases + demonyms of answer_id (as in the official 2Wiki evaluator);
  MuSiQue: answer_aliases. `answers_primary` keeps the single IRCoT/DPR primary answer.
"""
from __future__ import annotations

import csv
import gzip
import json
import logging
from pathlib import Path
from typing import Callable

from src.config import hop_type
from src.metrics import normalize_answer

log = logging.getLogger("loaders")

IRCOT_DIR = "ircot_processed/extracted/processed_data"
TWOWIKI_DIR = "2wiki_raw/extracted/data_ids"
MUSIQUE_DEV = "musique_raw/extracted/data/musique_ans_v1.0_dev.jsonl"
# raw files read only for answer aliases (recorded in the split manifest)
ALIAS_FILES = {f"{TWOWIKI_DIR}/id_aliases.json", f"{TWOWIKI_DIR}/dev.json", MUSIQUE_DEV}


def _dedup(xs: list[str]) -> list[str]:
    """Keep order, drop exact duplicates and answers that normalize to the empty string."""
    seen, out = set(), []
    for x in xs:
        x = x.strip()
        if x and x not in seen and normalize_answer(x):
            seen.add(x)
            out.append(x)
    return out


def _record(dataset: str, source_id: str, question: str, answers: list[str],
            primary: str, source_file: str) -> dict:
    answers = _dedup([primary] + answers)  # may be empty; prepare_data drops those as unscorable
    return {
        "qid": f"{dataset}__{source_id}",
        "dataset": dataset,
        "question": question.strip(),
        "answers": answers,
        "answers_primary": [primary.strip()],
        "hop_type": hop_type(dataset),
        "source_id": source_id,
        "source_file": source_file,
    }


def _dpr(raw: Path, dataset: str, rel: str) -> list[dict]:
    rows = json.load(gzip.open(raw / rel))
    out = []
    for i, r in enumerate(rows):
        # source_id mirrors Adaptive-RAG's question_id "single_<ds>_dev_<index>"
        out.append(_record(dataset, f"dev_{i}", r["question"], r["answers"], r["answers"][0], rel))
    return out


def load_nq(raw: Path) -> list[dict]:
    return _dpr(raw, "nq", "nq_dev/biencoder-nq-dev.json.gz")


def load_triviaqa(raw: Path) -> list[dict]:
    return _dpr(raw, "triviaqa", "trivia_dev/biencoder-trivia-dev.json.gz")


def load_popqa(raw: Path) -> list[dict]:
    rel = "popqa/popqa_test.tsv"
    with open(raw / rel, newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    out = [
        _record("popqa", r["id"], r["question"], json.loads(r["possible_answers"]),
                json.loads(r["possible_answers"])[0], rel)
        for r in rows
    ]
    return out


def _ircot(raw: Path, dataset: str, aliases_for: Callable[[str, str], list[str]]) -> list[dict]:
    rel = f"{IRCOT_DIR}/{dataset}/dev.jsonl"
    out = []
    with open(raw / rel) as f:
        for line in f:
            r = json.loads(line)
            (obj,) = r["answers_objects"]          # verified: exactly one object, one span each
            (primary,) = obj["spans"]
            extra = aliases_for(r["question_id"], primary)
            out.append(_record(dataset, r["question_id"], r["question_text"], extra, primary, rel))
    return out


def load_hotpotqa(raw: Path) -> list[dict]:
    return _ircot(raw, "hotpotqa", lambda qid, primary: [])


def load_2wikimultihopqa(raw: Path) -> list[dict]:
    base = raw / TWOWIKI_DIR
    alias_map = {}
    with open(base / "id_aliases.json") as f:
        for line in f:
            j = json.loads(line)
            alias_map[j["Q_id"]] = j["aliases"] + j["demonyms"]
    dev = {r["_id"]: r for r in json.load(open(base / "dev.json"))}
    mismatches = 0

    def aliases(qid: str, primary: str) -> list[str]:
        nonlocal mismatches
        r = dev[qid]
        if r["answer"].strip() != primary.strip():
            mismatches += 1
        return alias_map.get(r.get("answer_id") or "", [])

    out = _ircot(raw, "2wikimultihopqa", aliases)
    if mismatches:
        log.warning("2wiki: %d IRCoT primary answers differ from raw answer", mismatches)
    return out


def load_musique(raw: Path) -> list[dict]:
    dev = {}
    with open(raw / MUSIQUE_DEV) as f:
        for line in f:
            r = json.loads(line)
            dev[r["id"]] = r
    mismatches = 0

    def aliases(qid: str, primary: str) -> list[str]:
        nonlocal mismatches
        r = dev[qid]  # KeyError here would mean the IRCoT pool is not MuSiQue-Ans dev
        if not r["answerable"]:
            raise ValueError(f"musique {qid} is not answerable")
        if r["answer"].strip() != primary.strip():
            mismatches += 1
        return r["answer_aliases"]

    out = _ircot(raw, "musique", aliases)
    if mismatches:
        log.warning("musique: %d IRCoT primary answers differ from raw answer", mismatches)
    return out


LOADERS: dict[str, Callable[[Path], list[dict]]] = {
    "nq": load_nq,
    "triviaqa": load_triviaqa,
    "popqa": load_popqa,
    "hotpotqa": load_hotpotqa,
    "2wikimultihopqa": load_2wikimultihopqa,
    "musique": load_musique,
}
