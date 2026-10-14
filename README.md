# Adaptive RAG — experiment infrastructure

Infrastructure for a master's thesis on adaptive retrieval-augmented generation: a router decides,
per question, whether to retrieve. This repository holds the data preparation, BM25 retrieval, the
two baseline systems (`llm_only`, `always_rag`), evaluation, and the oracle router (upper bound).
Learned routers are out of scope for now; the record schema already has fields for them.

The setup follows Adaptive-RAG (Jeong et al., NAACL 2024, <https://github.com/starsuzi/Adaptive-RAG>)
and the IRCoT data/corpus pipeline it builds on (<https://github.com/StonyBrookNLP/ircot>).
Every deviation is listed under [Differences from Adaptive-RAG](#differences-from-adaptive-rag).

## Setup

Requirements: macOS/Linux, ~50 GB free disk (peak), 16 GB RAM, JDK 21 (for Pyserini), Python 3.12.

```bash
# uv (Python + locked dependencies) — user-local install, no sudo
curl -LsSf https://astral.sh/uv/install.sh | sh
# JDK 21 (any distribution). Used here: Eclipse Temurin 21.0.12.1+1, aarch64, extracted to ~/.local/jdk
export JAVA_HOME=~/.local/jdk/jdk-21.0.12.1+1/Contents/Home

uv sync                       # creates .venv from uv.lock (exact versions)
cp .env.example .env          # put OPENAI_API_KEY (and JAVA_HOME) here; .env is git-ignored
uv run pytest                 # unit tests
```

Python 3.12 rather than 3.11: Pyserini 2.4.0 requires Python >= 3.12.

## Running, step by step

Every step is a standalone module and supports `--dry-run` (8 questions per dataset). Dry-run outputs go
to `runs/dryrun/` and never touch the real split or results.

| Step | Command | Output |
|---|---|---|
| Download question sources (~1.5 GB, each file < 1 GB) | `uv run python -m src.download --stage 1` | `data/raw/`, `data/raw/MANIFEST.json` (sha256) |
| Stage 1: sample + split | `uv run python -m src.prepare_data [--dry-run]` | `data/processed/questions.jsonl`, `data/splits/split.jsonl`, `data/processed/summary.md` |

`data/splits/split.jsonl` is **write-once**: re-running `prepare_data` fails instead of overwriting it.
Delete `data/processed/questions.jsonl` and `data/splits/{split.jsonl,manifest.json}` by hand to regenerate
(the procedure is deterministic, so it regenerates the identical split).

All settings live in [configs/default.yaml](configs/default.yaml). Seed: 42.

## Stage 1 — data

Common format (`data/processed/questions.jsonl`):
`qid`, `dataset`, `question`, `answers` (all valid variants), `hop_type` (single/multi), plus
`answers_primary` (the single answer Adaptive-RAG/IRCoT scores against), `source_id`, `source_file`.
Split assignment is in `data/splits/split.jsonl` (`qid`, `dataset`, `split`).

Only questions and gold answers are used. Ready-made contexts (DPR positive/negative passages,
HotpotQA distractor paragraphs, 2Wiki/MuSiQue `context`/`paragraphs`) are never read into our records;
context comes only from our retriever.

Procedure ([src/prepare_data.py](src/prepare_data.py)):
1. Load each pool, sort by source id.
2. Drop unscorable questions (no gold answer survives SQuAD normalization: NQ `#`, HotpotQA `The The`, `!!!`).
3. Drop questions whose normalized text appears more than once in the pool (PopQA asks e.g. "What is
   John Smith's occupation?" about different entities with different answers; such duplicates could also
   leak across splits).
4. Sample 500 with `random.Random("42:<dataset>")`, shuffle, cut 300/100/100 (train/dev/test).
5. Assert no qid and no normalized question text crosses splits.

### Sources and licenses

| Dataset | Pool (same as Adaptive-RAG) | Answers | License |
|---|---|---|---|
| NQ (open) | DPR `biencoder-nq-dev.json` (6,515) | DPR answer list | CC BY-SA 3.0 |
| TriviaQA | DPR `biencoder-trivia-dev.json` (8,837) | DPR answer list (incl. aliases) | Apache 2.0 |
| PopQA | HF `akariasai/PopQA` @ `098765c`, `test.tsv` (14,267) | `possible_answers` | MIT (GitHub repo; HF card has none) |
| HotpotQA | IRCoT `processed_data/hotpotqa/dev.jsonl` (7,405; = official dev distractor) | single answer | CC BY-SA 4.0 |
| 2WikiMultihopQA | IRCoT `processed_data/2wikimultihopqa/dev.jsonl` (12,576) | answer + `id_aliases.json` aliases and demonyms (as in the official 2Wiki evaluator) | Apache 2.0 |
| MuSiQue (answerable) | IRCoT `processed_data/musique/dev.jsonl` (2,417 = MuSiQue-Ans dev) | answer + `answer_aliases` | CC BY 4.0 |

Download URLs and sha256 of every file: [src/download.py](src/download.py), `data/raw/MANIFEST.json`,
`data/splits/manifest.json`.

### Answer-variant policy

Some datasets list very short aliases, e.g. PopQA `India` → `in`, 2Wiki `Norwegian` → `no`,
MuSiQue `University of South Carolina` → `SC`, TriviaQA emoji aliases. Under the accuracy metric
(gold contained in the prediction) these would make answers like "born **in** Delhi" count as correct.

Policy (`eval.accuracy_min_alias_chars: 3` in the config):
- **EM and F1** score against every answer variant (max over variants).
- **Accuracy** ignores aliases whose normalized form has ≤ 2 characters. The primary answer is always kept,
  even when short (e.g. `US`).
- An additional report scores everything against the **primary answer only** (`answers_primary`), which is
  what Adaptive-RAG/IRCoT score against (`eval.answer_sets: [all, primary_only]`).

Questions with at least one alias that accuracy ignores (from `data/processed/summary.md`):

| dataset | train | dev | test | total |
|---|---|---|---|---|
| nq | 0 | 0 | 0 | 0 |
| triviaqa | 22 | 6 | 4 | 32 |
| popqa | 28 | 12 | 8 | 48 |
| hotpotqa | 0 | 0 | 0 | 0 |
| 2wikimultihopqa | 21 | 6 | 9 | 36 |
| musique | 10 | 5 | 1 | 16 |
| **total** | 81 | 29 | 22 | 132 |

## Differences from Adaptive-RAG

| Topic | Adaptive-RAG | Here | Why |
|---|---|---|---|
| Single-hop datasets | NQ, TriviaQA, SQuAD | NQ, TriviaQA, **PopQA** | Thesis design; PopQA probes long-tail knowledge where retrieval matters most |
| Sampling | 500 test per dataset, seed 13370, + separate dev sample | 500 per dataset from the same pools, seed 42, split 300/100/100 | One fixed sample with train/dev for future routers |
| Answer variants (2Wiki, MuSiQue) | IRCoT keeps one gold span | gold + aliases (`answers`); primary kept in `answers_primary` | Task requires all valid variants |
| Accuracy | normalized gold is a substring of the prediction | normalized gold occurs as whole tokens in the prediction; aliases ≤ 2 chars ignored (primary kept) | avoids false matches of short aliases (`ca` in `canada`, `in` in "born in") |
| Gold answers | single primary answer | all variants (main report) + primary-only (comparison report) | see [Answer-variant policy](#answer-variant-policy) |
| Unscorable / duplicate-text questions | kept | dropped before sampling (counts in `data/processed/summary.md`) | can never be scored correct; duplicate texts risk split leakage |

(Retrieval, generation and evaluation differences are added as those stages are built.)
