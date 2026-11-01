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
#   GEMINI_API_KEY=...
#   DEEPSEEK_API_KEY=...
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
| Stage 3: probe model params (paid, ~10 tiny calls) | `uv run python -m src.llm --probe` | `results/meta/param_probe.json` |
| Stage 3: runs (paid; full runs need `--yes`) | `uv run python -m src.run_baselines [--dry-run] [--system ...] [--yes]` | `results/raw/<system>.jsonl` |
| Stage 3: sequential latency run (paid) | `uv run python -m src.run_baselines --latency --yes` | `results/latency/<system>.jsonl` |
| Inspect runs | `uv run python -m src.inspect_runs [--dry-run]` | `results/summary/inspection.md` |
| Question attributes (no model calls) | `uv run python -m src.question_meta` | `data/processed/question_meta.jsonl` (write-once) |
| Stage 4: evaluation + report | `uv run python -m src.evaluate [--dry-run]` | `results/summary/*.csv`, `results/summary/summary.md` |
| Gemini probe (paid, a few calls) | `uv run python -m src.llm --probe --config configs/gemini.yaml` | `results/models/gemini-2.5-flash-lite/meta/param_probe.json` |
| Gemini runs (paid; full runs need `--yes`) | `uv run python -m src.run_baselines --config configs/gemini.yaml [--dry-run] [--yes]` | `results/models/gemini-2.5-flash-lite/raw/` |
| DeepSeek probe (paid, a few calls) | `uv run python -m src.llm --probe --config configs/deepseek.yaml` | `results/models/deepseek-flash/meta/param_probe.json` |
| DeepSeek runs (paid; full runs need `--yes`) | `uv run python -m src.run_baselines --config configs/deepseek.yaml [--dry-run] [--yes]` | `results/models/deepseek-flash/raw/` |
| Qwen3.5-4B (local Ollama; full runs need `--yes`) | `uv run python -m src.run_baselines --config configs/qwen.yaml [--dry-run] [--yes]` | `results/models/qwen3.5-4b/raw/` |
| Gemma 4 E2B (local Ollama; full runs need `--yes`) | `uv run python -m src.run_baselines --config configs/gemma.yaml [--dry-run] [--yes]` | `results/models/gemma4-e2b/raw/` |

End-to-end dry run (8 questions per dataset, ≈ $0.003, never touches the real split or results):

```bash
uv run python -m src.prepare_data --dry-run
uv run python -m src.retrieve --dry-run
uv run python -m src.run_baselines --dry-run
uv run python -m src.evaluate --dry-run      # -> runs/dryrun/results/summary/summary.md
```

`data/splits/split.jsonl` is **write-once**: re-running `prepare_data` fails instead of overwriting it.
Delete `data/processed/questions.jsonl` and `data/splits/{split.jsonl,manifest.json}` by hand to regenerate
(the procedure is deterministic, so it regenerates the identical split).

All settings live in [configs/default.yaml](configs/default.yaml). Seed: 42.

## Stage 1 — data

Common format (`data/processed/questions.jsonl`):
`qid`, `dataset`, `question`, `answers` (all valid variants), `hop_type` (single/multi), plus
`answers_primary` (first listed answer: the single IRCoT answer for HotpotQA/2Wiki/MuSiQue; for
NQ/TriviaQA/PopQA just the first entry of the source list, which for TriviaQA is an arbitrary alias),
`source_id`, `source_file`.
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
- An additional report scores the base systems against **Adaptive-RAG's own gold answers**, without the
  short-alias filter (`eval.answer_sets: [all, adaptive_rag]`): NQ and TriviaQA the full DPR answer list
  (Adaptive-RAG's `process_nq.py` / `process_trivia.py` store all DPR answers as spans), HotpotQA/2Wiki/
  MuSiQue the single IRCoT answer, PopQA (not in Adaptive-RAG) all `possible_answers` as in its original
  evaluation.

  Correction (2026-10-14): this report was first specified as "primary answer only". That matches
  Adaptive-RAG for the multi-hop datasets but not for NQ/TriviaQA, where Adaptive-RAG uses the whole
  list and the first TriviaQA entry is an arbitrary alias (e.g. `Titfer` for "hat"), so it was replaced.

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

## Stage 3 — model calls

Model: `gpt-5-nano-2025-08-07` (pinned snapshot) via the OpenAI Responses API, `store=false`.
API key only from `.env` (`OPENAI_API_KEY`).

Three call types, each logged one line per call with the same schema ([src/run_baselines.py](src/run_baselines.py)):

| system | prompt | notes |
|---|---|---|
| `llm_only` | [prompts/llm_only.txt](prompts/llm_only.txt) | question only |
| `always_rag` | [prompts/always_rag.txt](prompts/always_rag.txt) | identical text plus a `Context:` block with the BM25 top-5 passages (`Wikipedia Title: …` format); a test enforces that this block is the only difference |
| `llm_decision` | [prompts/llm_decision.txt](prompts/llm_decision.txt) | "Can you answer … without any external source? Answer only YES or NO." Exactly `yes`/`no` (case and punctuation ignored) is parsed; anything else is `invalid` and routed like NO (retrieve), counted separately |

Generation parameters were probed against the API (2026-10-14, `results/meta/param_probe.json`):

| parameter | requested | outcome |
|---|---|---|
| reasoning effort | `minimal` | accepted; `none` is rejected for this model ("Supported values are: 'minimal', …"), so `minimal` is the lowest level |
| verbosity | `low` | accepted |
| max_output_tokens | 256 | accepted |
| top_p | 1 | accepted |
| temperature | 0 | **rejected** ("not supported with this model") → dropped, listed in every record's `dropped_params` |
| seed | 42 | **rejected** ("Unknown parameter") → dropped, listed in `dropped_params` |

Without temperature or seed control the API is not guaranteed to be deterministic; each prediction is a
single sample.

Record fields: `qid, dataset, split, system, model, prompt_hash, input_tokens, output_tokens,
reasoning_tokens, cached_input_tokens, retrieval_ms, llm_ms, total_ms, retrieved_ids, retrieved_scores,
retrieval_cached, prediction, timestamp, error, error_kind`, provenance (`run_id, mode, config_hash,
response_model, response_id, status, attempts, request_params, dropped_params, prompt`) and router
fields (`router_name, router_decision, router_route, router_ms, router_input_tokens,
router_output_tokens`; filled by `llm_decision`, reserved for learned routers).
Token counts come only from the API's `usage`. `output_tokens` already includes `reasoning_tokens`
(billed at the output price), so cost uses `output_tokens` and reasoning is not added twice.

Resume rule per (qid, system, model, prompt_hash) — `prompt_hash` covers the model, the full rendered
prompt and the parameters sent. Failed records are never deleted from the log.

| record state | next run |
|---|---|
| success | never called again |
| `incomplete` (hit `max_output_tokens`), `permanent` (4xx), `no_usage` | never called again; counted as a wrong answer |
| `transient_exhausted` (429/5xx/timeout after all backoff retries) | called again automatically |
| `flagged` (OpenAI prompt filter: "flagged as potentially violating our usage policy") | called again only with `--retry-flagged`, at most once |

A qid whose prompt was flagged twice for any system is removed from **all** systems' comparisons
(evaluation runs on the common question set); removed qids are listed in the report.
Concurrency, RPM/TPM limits and exponential backoff with jitter come from the config.

Latency: the main runs are concurrent and use cached retrieval, so their timings are not used for
latency claims. `--latency` runs a fixed test subset (200 questions, `random.Random("42:latency")`)
sequentially (concurrency 1), with fresh retrieval right before each model call; P50/P95 come only
from this run.

### Observations (dry run, 144 calls)

- **Fixed output overhead.** Every response is billed at least 19 output tokens with
  `reasoning_tokens = 0`, even a one-word `NO`. The API does not attribute these ~18 tokens to
  reasoning or visible text. They are included in cost (they are billed), and should be kept in mind
  when comparing the cost of a short routing call with the context tokens it saves.
- **Reasoning leakage into the answer.** With `minimal` effort the model occasionally writes its
  deliberation into the answer text (1 of 48 `llm_only` answers in the dry run: "…Wait. There's 'The
  Hat Museum'?…"). Decision: answers are left as they are (no post-processing); the leakage rate per
  system is reported in Stage 4.

### Full run (2026-10-14)

9,000 calls + 600 latency calls, $0.21 in total. Errors after the main run: 34 `flagged` (false positives
on benign questions such as "Who is Titus Tarquinius's paternal grandfather?"; non-overlapping between
systems, none for `llm_decision`) and 15 `incomplete` (answer turned into a deliberation that hit 256
output tokens). One `--retry-flagged` pass recovered 27 of 34; 6 qids were flagged twice
(TriviaQA 1, HotpotQA 4, MuSiQue 1) and are excluded from all comparisons; one MuSiQue qid was
flagged, then `incomplete` on retry, and is counted as wrong.

## Stage 4 — evaluation

[src/evaluate.py](src/evaluate.py) writes `results/summary/` (report: [summary.md](results/summary/summary.md)).

- **Final record** per (qid, system): last successful call, else last call. Failed calls (`incomplete`,
  permanent errors) count as wrong; their billed tokens still count as cost.
- **Common question set**: a qid whose prompt was rejected by the filter twice in any system is removed
  from all systems (`excluded_qids.csv`).
- **Metrics**: SQuAD-normalized EM, F1, accuracy (token-bounded containment), max over gold variants;
  "correct" = `eval.correct_metric` (default accuracy). Two answer sets: `all` (main) and `adaptive_rag`
  (comparison, see [Answer-variant policy](#answer-variant-policy)).
- **Outcome labels** (`question_labels.jsonl`, `labels.csv`): `both_ok`, `rag_hurts`, `retrieval_needed`,
  `both_fail` (`no_retrieval_ok` = both_ok + rag_hurts), per dataset and split.
- **Composed systems** ([src/routers/](src/routers/__init__.py)), no extra API calls:
  `oracle` (llm_only if correct, else always_rag; both wrong → llm_only) and `llm_decision_router`
  (YES → llm_only, NO/invalid → always_rag; decision call charged as router cost).
- **Cost** per component (`retrieval_usd` = 0 for local BM25, `generation_usd`, `router_usd`), prices
  and their date from the config.
- **Decision analysis**: YES/NO/invalid, agreement with the oracle route, confusion matrix,
  P(llm_only correct | YES).
- **Break-even**: decision cost vs. context tokens and money saved on skipped retrievals, and the skip
  rate the router would need to break even.
- **Latency**: sequential run only; adaptive = decision call + chosen path, compared with Always-RAG and
  LLM-only (paired bootstrap on mean and median).
- **Bootstrap**: 10,000 paired resamples over questions, stratified by dataset for pooled rows, 95%
  percentile CIs for accuracy and cost per 1,000 questions.
- **Reasoning leakage** ([src/leakage.py](src/leakage.py)): `incomplete`, ≥ 17 words, or a deliberation
  marker; reported per criterion.
- **Dispatch** (`dispatch.csv`): for every question, whether a call was logged, its final status, and the
  decision route. Both paths call the model. A question rejected twice by the provider filter stays
  marked sent and drops out of the comparison.
- **Source attributes** (`question_meta.jsonl`, joined in `strata.csv`). Written from the dataset
  files, before accuracy, and used as separate cuts in the report. There is no single
  easy/medium/hard label, and none is invented.

  HotpotQA does publish easy/medium/hard. The IRCoT pool of 7,405 and the frozen sample of 500 are
  entirely `level=hard`, so that label cannot split this sample. Level is stored. The cut that varies
  is `type` (bridge 395, comparison 105), which is not a difficulty rank. MuSiQue's source difficulty
  is the hop count on the question id (2-hop 251, 3-hop 155, 4-hop 94 here). PopQA has no difficulty
  field; the cut is a tertile of `log10(s_pop)` on the frozen 500, edges written once, low = least
  popular. 2Wiki `type` is a reasoning type (compositional, comparison, bridge_comparison, inference).
  NQ and TriviaQA have no source difficulty field; they appear only under `hop_type` (single / multi),
  the only cut defined for every question. A second model is not asked to judge difficulty, and
  outcome labels (`both_fail`, `rag_hurts`, and the rest) stay outcomes. The nano report states where
  these cuts move accuracy and whether the decision router beats Always-RAG inside them.

Gemini 2.5 Flash-Lite uses the same prompts, the same BM25 cache, and the same three call types.
`thinking_budget` is 0. Prices are the standard paid text tier on the Gemini pricing page
(retrieved 2026-10-24): $0.10/1M input, $0.01/1M cached input, $0.40/1M output, thinking tokens included
in the output price. Its logs are `results/models/gemini-2.5-flash-lite/`. The key probed on 2026-10-24 is on the
free tier: 20 generateContent requests per day for this model, so the 3,000-question run needs
billing on that Google project. Re-run `src.evaluate` after
that run; the report adds paired accuracy and cost by the attributes above when both models are complete.
There is no Gemini latency run.

DeepSeek uses the same prompts and the same three call types, through the OpenAI Responses API at
`https://api.deepseek.com`. The model is `deepseek-flash` (DeepSeek-V4.1-Flash-1017) with thinking
turned off (`reasoning_effort: none`). Off-peak prices, retrieved 2026-10-24: $0.15/1M cache-miss
input, $0.003/1M cache-hit input, $0.60/1M output. Weekday peak hours (01:00-04:00 and 06:00-10:00 UTC)
are double. Logs go to `results/models/deepseek-flash/`.

Qwen and Gemma run locally through Ollama, on the same prompts and the same three call types.
The machine has 16 GB of memory, so the nano-sized builds are `qwen3.5:4b` (Qwen3.5-4B, Q4_K_M,
about 3.4 GB; `think` off) and `gemma4:e2b` (Gemma 4 E2B, 2.3B effective parameters). The larger
small-tier builds, Qwen3.5-9B and Gemma 4 E4B, do not leave room beside the OS. Their API price
is 0. One call at a time. Logs go to `results/models/qwen3.5-4b/` and `results/models/gemma4-e2b/`.

## Differences from Adaptive-RAG

| Topic | Adaptive-RAG | Here | Why |
|---|---|---|---|
| Single-hop datasets | NQ, TriviaQA, SQuAD | NQ, TriviaQA, **PopQA** | Thesis design; PopQA probes long-tail knowledge where retrieval matters most |
| Sampling | 500 test per dataset, seed 13370, + separate dev sample | 500 per dataset from the same pools, seed 42, split 300/100/100 | One fixed sample with train/dev for future routers |
| Answer variants (2Wiki, MuSiQue) | IRCoT keeps one gold span | gold + aliases (`answers`); primary kept in `answers_primary` | Task requires all valid variants |
| Accuracy | normalized gold is a substring of the prediction | normalized gold occurs as whole tokens in the prediction; aliases ≤ 2 chars ignored (primary kept) | avoids false matches of short aliases (`ca` in `canada`, `in` in "born in") |
| Gold answers | NQ/TriviaQA: full DPR list; multi-hop: single IRCoT answer | all variants with short-alias filter for accuracy (main report) + Adaptive-RAG's gold set (comparison report) | see [Answer-variant policy](#answer-variant-policy) |
| Unscorable / duplicate-text questions | kept | dropped before sampling (counts in `data/processed/summary.md`) | can never be scored correct; duplicate texts risk split leakage |
| Retrieval engine | Elasticsearch 7.10.2, `english` analyzer | Pyserini/Lucene, `DefaultEnglishAnalyzer` (Porter + English stopwords) | ES 7.10.2 has no ARM-macOS build. Same BM25 (k1 1.2, b 0.75), same title+text query, same 100-candidate dedup. Remaining difference: ES `english` analyzer also applies a possessive filter and keyword marker; tokenization of rare edge cases can differ |
| Document ids | first 32 hex chars of an ES-side hash | DPR passage id (wiki), Wikipedia page id (hotpotqa), sha256(title+text)[:32] (2wiki, musique) | ids are internal; corpora and dedup are the same, document counts match exactly |
| Retrieval strategy | no / single-step / multi-step (IRCoT) | no retrieval and single-step only | multi-step retrieval is out of scope |
| Generator | FLAN-T5-XL/XXL, GPT-3.5 (`gpt-3.5-turbo-instruct`), with few-shot CoT prompts | GPT-5 nano (`gpt-5-nano-2025-08-07`), and separately Gemini 2.5 Flash-Lite (`gemini-2.5-flash-lite`, thinking budget 0); zero-shot, short-answer prompt | thesis design; cost-sensitive small models. Gemini logs live under `results/models/` and do not mix with the nano logs |
| Router | trained T5 query-complexity classifier | none yet; oracle upper bound + the model's own YES/NO decision (`llm_decision`) | learned routers come later |

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
