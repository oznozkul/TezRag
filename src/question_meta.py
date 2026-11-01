"""Source-native question attributes for the frozen sample. Does not rewrite the split.

    python -m src.question_meta

Writes data/processed/question_meta.jsonl (one row per qid) and
data/processed/pop_tertile_edges.json. Both are write-once.

There is no single easy/medium/hard scale across the six datasets, and none is invented.
NQ and TriviaQA have no source difficulty field. HotpotQA's IRCoT pool is entirely level=hard,
so that field is recorded but is not a cut. PopQA tertiles are thirds of log10(s_pop) on this
sample (low = least popular); a value on a boundary goes to the lower bin. MuSiQue hops come
from the id prefix (3hop1 and 3hop2 both become 3). 2Wiki `type` is a reasoning type.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import re
from pathlib import Path

import numpy as np

from src.config import Config, load_config
from src.data import load_questions
from src.datasets.loaders import IRCOT_DIR, TWOWIKI_DIR
from src.io_utils import read_jsonl, setup_logging, write_once_json, write_once_jsonl

log = logging.getLogger("question_meta")

_HOP = re.compile(r"^(\d+)hop")
POP_REL = "popqa/popqa_test.tsv"
EDGES_NAME = "pop_tertile_edges.json"
META_NAME = "question_meta.jsonl"


def musique_hops(source_id: str) -> int:
    m = _HOP.match(source_id)
    if not m:
        raise ValueError(f"musique id has no hop prefix: {source_id}")
    return int(m.group(1))


def tertile_edges(log_pops: list[float]) -> tuple[float, float]:
    """Linear quantiles at 1/3 and 2/3. Assignment uses <=, so a tie falls in the lower bin."""
    q33, q66 = np.quantile(np.asarray(log_pops, dtype=float), [1 / 3, 2 / 3], method="linear")
    return float(q33), float(q66)


def assign_tertile(log_pop: float, q33: float, q66: float) -> str:
    if log_pop <= q33:
        return "low"
    if log_pop <= q66:
        return "mid"
    return "high"


def _blank(q: dict) -> dict:
    return {
        "qid": q["qid"], "dataset": q["dataset"], "hop_type": q["hop_type"],
        "hotpot_level": None, "hotpot_type": None, "musique_hops": None,
        "wiki_type": None, "s_pop": None, "pop_tertile": None,
    }


def build_records(questions: list[dict], hotpot: dict[str, dict], wiki: dict[str, str],
                  pop: dict[str, int], edges: dict | None) -> tuple[list[dict], dict]:
    """Join source attributes onto questions. `edges` is reused when already written."""
    pop_qs = [q for q in questions if q["dataset"] == "popqa"]
    logs = []
    for q in pop_qs:
        if q["source_id"] not in pop:
            raise KeyError(f"popqa {q['qid']} missing from the TSV")
        s_pop = pop[q["source_id"]]
        if s_pop <= 0:
            raise ValueError(f"popqa {q['qid']} has s_pop={s_pop}; log10 is undefined")
        logs.append(math.log10(s_pop))
    if edges is None:
        q33, q66 = tertile_edges(logs)
        edges = {
            "n": len(logs), "q33_log10": q33, "q66_log10": q66,
            "rule": "low: log10(s_pop) <= q33; mid: <= q66; high: above q66. "
                    "A value on a boundary goes to the lower bin. "
                    "Edges are tertiles of the frozen PopQA sample, not of the full pool.",
        }
    q33, q66 = float(edges["q33_log10"]), float(edges["q66_log10"])

    rows = []
    for q in questions:
        row = _blank(q)
        ds, sid = q["dataset"], q["source_id"]
        if ds == "hotpotqa":
            if sid not in hotpot:
                raise KeyError(f"hotpotqa {q['qid']} missing from the IRCoT pool")
            row["hotpot_level"] = hotpot[sid]["level"]
            row["hotpot_type"] = hotpot[sid]["type"]
        elif ds == "musique":
            row["musique_hops"] = musique_hops(sid)
        elif ds == "2wikimultihopqa":
            if sid not in wiki:
                raise KeyError(f"2wiki {q['qid']} missing from dev.json")
            row["wiki_type"] = wiki[sid]
        elif ds == "popqa":
            row["s_pop"] = pop[sid]
            row["pop_tertile"] = assign_tertile(math.log10(pop[sid]), q33, q66)
        elif ds not in {"nq", "triviaqa"}:
            raise ValueError(f"no metadata rule for dataset {ds}")
        rows.append(row)
    rows.sort(key=lambda r: r["qid"])
    return rows, edges


def _load_hotpot(raw: Path, needed: set[str]) -> dict[str, dict]:
    path = raw / IRCOT_DIR / "hotpotqa" / "dev.jsonl"
    out = {}
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            if r["question_id"] in needed:
                out[r["question_id"]] = {"level": r["level"], "type": r["type"]}
    return out


def _load_wiki(raw: Path, needed: set[str]) -> dict[str, str]:
    path = raw / TWOWIKI_DIR / "dev.json"
    out = {}
    for r in json.load(open(path)):
        if r["_id"] in needed:
            out[r["_id"]] = r["type"]
    return out


def _load_pop(raw: Path, needed: set[str]) -> dict[str, int]:
    out = {}
    with open(raw / POP_REL, newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["id"] in needed:
                out[r["id"]] = int(r["s_pop"])
    return out


def meta_path(cfg: Config) -> Path:
    return cfg.path("processed") / META_NAME


def edges_path(cfg: Config) -> Path:
    return cfg.path("processed") / EDGES_NAME


def load_meta(cfg: Config) -> dict[str, dict]:
    path = meta_path(cfg)
    if not path.exists():
        raise FileNotFoundError(f"{path} missing; run `python -m src.question_meta`")
    rows = list(read_jsonl(path))
    by_q = {r["qid"]: r for r in rows}
    if len(by_q) != len(rows):
        raise ValueError(f"{path} has duplicate qids")
    return by_q


def _check_same_qids(questions: list[dict], rows: list[dict]) -> None:
    got, want = {r["qid"] for r in rows}, {q["qid"] for q in questions}
    if got != want:
        raise SystemExit(f"question_meta qids differ from the split "
                         f"(only in meta: {len(got - want)}, only in split: {len(want - got)})")


def build(cfg: Config) -> tuple[list[dict], dict]:
    questions = load_questions(cfg, dry_run=False)
    split_ids = {r["qid"] for r in read_jsonl(cfg.path("splits") / "split.jsonl")}
    qids = {q["qid"] for q in questions}
    if qids != split_ids:
        raise SystemExit("questions.jsonl and split.jsonl do not contain the same qids")
    raw = cfg.path("raw")
    needed = lambda ds: {q["source_id"] for q in questions if q["dataset"] == ds}
    edges = json.loads(edges_path(cfg).read_text()) if edges_path(cfg).exists() else None
    return build_records(questions, _load_hotpot(raw, needed("hotpotqa")),
                         _load_wiki(raw, needed("2wikimultihopqa")),
                         _load_pop(raw, needed("popqa")), edges)


def main() -> None:
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    args = ap.parse_args()
    cfg = load_config(args.config)
    dest = meta_path(cfg)
    if dest.exists():
        questions = load_questions(cfg, dry_run=False)
        _check_same_qids(questions, list(read_jsonl(dest)))
        log.info("%s already exists and matches the split (%d questions)", dest, len(questions))
        return
    rows, edges = build(cfg)
    _check_same_qids(load_questions(cfg, dry_run=False), rows)
    if not edges_path(cfg).exists():
        write_once_json(edges_path(cfg), edges)
    write_once_jsonl(dest, rows)
    log.info("wrote %s (%d rows) and %s", dest, len(rows), edges_path(cfg))


if __name__ == "__main__":
    main()
