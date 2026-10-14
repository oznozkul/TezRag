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
# create .env (git-ignored) with two lines:
#   OPENAI_API_KEY=sk-...
#   JAVA_HOME=/path/to/jdk-21
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
| Download corpora (6.2 GB; needs ≥ 60 GB free) | `uv run python -m src.download --stage 2 --yes-large` | `data/raw/` (resumable) |
| Stage 2: corpus → shards | `uv run python -m src.build_corpus {wiki,hotpotqa,2wikimultihopqa,musique}` | `data/corpora/<name>/docs-*.jsonl` |
| Stage 2: BM25 index | `uv run python -m src.build_index <name>` | `indexes/<name>/`, `results/meta/index_<name>.json` |
| Stage 2: precompute retrieval | `uv run python -m src.retrieve [--dry-run]` | `cache/retrieval.sqlite`, `results/retrieval/retrieval.jsonl` |

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

## Stage 2 — retrieval

Sparse retrieval with BM25 via Pyserini 2.4.0 (Lucene / Anserini 2.3.0, JDK 21). Chosen over
Elasticsearch (no ARM-macOS build of ES 7.10.2) and `bm25s` (in-memory indexing of 21M passages does not
fit in 16 GB RAM). Lucene is the engine underneath Elasticsearch, so BM25 scoring is the same.

Corpora — one index per dataset family, exactly as in IRCoT/Adaptive-RAG
([src/build_corpus.py](src/build_corpus.py) mirrors their `retriever_server/build_index.py`):

| Index | Used for | Source | Download | License | Docs (expected = ours) | Indexed | Convert | Index time | Index size |
|---|---|---|---|---|---|---|---|---|---|
| `wiki` | NQ, TriviaQA, PopQA | DPR `psgs_w100.tsv.gz` (Wikipedia 2018-12, 100-word passages) | 4.69 GB | CC BY-SA 3.0 | 21,015,324 | 21,015,324 | 26.7 min | 4.5 min | 11.56 GB |
| `hotpotqa` | HotpotQA | `enwiki-20171001-pages-meta-current-withlinks-abstracts.tar.bz2` (first paragraphs) | 1.55 GB | CC BY-SA 4.0 | 5,233,329 | 5,233,235 (94 empty skipped) | 4.9 min | 0.7 min | 1.53 GB |
| `2wikimultihopqa` | 2WikiMultihopQA | train+dev+test `context` paragraphs, dedup on title+text | 259 MB (zip) | Apache 2.0 | 430,225 | 430,225 | 0.1 min | 0.2 min | 0.21 GB |
| `musique` | MuSiQue | ans+full train/dev/test `paragraphs`, dedup on title+text | 272 MB (zip) | CC BY 4.0 | 139,416 | 139,416 | 0.1 min | 0.1 min | 0.07 GB |

Measured on an Apple M1 (8 cores, 16 GB RAM), 8 indexing threads, 6 GB JVM heap. HotpotQA: 94 abstracts in the 2017 dump have no text; Anserini skips empty documents, whereas Elasticsearch would index them by title only. They carry no text, so the effect on answers is nil; the index check expects 5,233,329 − 94.

Retriever ([src/retrieval.py](src/retrieval.py)), matching Adaptive-RAG's one-step retrieval config
(`oner_qa_*`: `retrieval_count: 5`, `document_type: title_paragraph_text`):
- BM25 `k1=1.2, b=0.75` (Elasticsearch defaults).
- The question is matched against the paragraph text **and** the title field, scores summed
  (ES `query_title_field_too=True`, a `bool`/`should` of two `match` queries).
- 100 candidates → dedup by stripped, lowercased paragraph text (as IRCoT) → top-k = 5.
- Every query's `retrieval_ms` (search + stored-doc fetch + dedup) and passage ids are recorded.
  Results are cached in SQLite, keyed by (corpus, index fingerprint, query, k, candidate k, k1, b);
  a cache hit returns the originally measured latency with `cached=true`. The sequential latency run
  bypasses the cache.

## Differences from Adaptive-RAG

| Topic | Adaptive-RAG | Here | Why |
|---|---|---|---|
| Single-hop datasets | NQ, TriviaQA, SQuAD | NQ, TriviaQA, **PopQA** | Thesis design; PopQA probes long-tail knowledge where retrieval matters most |
| Sampling | 500 test per dataset, seed 13370, + separate dev sample | 500 per dataset from the same pools, seed 42, split 300/100/100 | One fixed sample with train/dev for future routers |
| Answer variants (2Wiki, MuSiQue) | IRCoT keeps one gold span | gold + aliases (`answers`); primary kept in `answers_primary` | Task requires all valid variants |
| Accuracy | normalized gold is a substring of the prediction | normalized gold occurs as whole tokens in the prediction; aliases ≤ 2 chars ignored (primary kept) | avoids false matches of short aliases (`ca` in `canada`, `in` in "born in") |
| Gold answers | single primary answer | all variants (main report) + primary-only (comparison report) | see [Answer-variant policy](#answer-variant-policy) |
| Unscorable / duplicate-text questions | kept | dropped before sampling (counts in `data/processed/summary.md`) | can never be scored correct; duplicate texts risk split leakage |
| Retrieval engine | Elasticsearch 7.10.2, `english` analyzer | Pyserini/Lucene, `DefaultEnglishAnalyzer` (Porter + English stopwords) | ES 7.10.2 has no ARM-macOS build. Same BM25 (k1 1.2, b 0.75), same title+text query, same 100-candidate dedup. Remaining difference: ES `english` analyzer also applies a possessive filter and keyword marker; tokenization of rare edge cases can differ |
| Document ids | first 32 hex chars of an ES-side hash | DPR passage id (wiki), Wikipedia page id (hotpotqa), sha256(title+text)[:32] (2wiki, musique) | ids are internal; corpora and dedup are the same, document counts match exactly |
| Retrieval strategy | no / single-step / multi-step (IRCoT) | no retrieval and single-step only | multi-step retrieval is out of scope |

(Retrieval, generation and evaluation differences are added as those stages are built.)

## Limitations

- **Always-RAG is single-step retrieval.** The question is sent to BM25 once and the top-k passages are
  given to the model. Multi-step retrieval (IRCoT-style interleaving of retrieval and chain-of-thought,
  Adaptive-RAG's third strategy) is out of scope. Multi-hop datasets (HotpotQA, 2Wiki, MuSiQue) are
  therefore evaluated with a retrieval strategy that is known to be weaker for them; answer recall@5 on
  MuSiQue is 0.20 (`results/meta/retrieval_summary.json`).
- Sparse retrieval only (BM25); no dense retriever or reranker.
- Corpus dates (Wikipedia 2017/2018) differ from the generator's knowledge cutoff (GPT-5 nano: May 2024);
  some gold answers may be outdated relative to the model's knowledge.
