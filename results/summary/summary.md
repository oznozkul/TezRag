# Results

Model `gpt-5-nano-2025-08-07`; prices $0.05/1M input, $0.005/1M cached input, $0.4/1M output (source: https://developers.openai.com/api/docs/models/gpt-5-nano, retrieved 2026-10-14). BM25 retrieval cost $0.0/call (local). "Correct" = **accuracy**. Main answer set: `all` (accuracy ignores aliases of <= 2 normalized chars). Bootstrap: 10,000 paired resamples, stratified by dataset for pooled rows, 95% percentile CI.

## Question set

3000 questions; **2994 in the common comparison set**; 6 excluded because the prompt was rejected by the provider's filter twice (first call + one `--retry-flagged`).

| qid | dataset | split | flagged in | calls |
|---|---|---|---|---|
| hotpotqa__5a7fd7305542992e7d278dc2 | hotpotqa | dev | llm_only | llm_only:2 |
| hotpotqa__5a870a8e55429960ec39b707 | hotpotqa | train | always_rag | always_rag:2 |
| hotpotqa__5adddf5d5542997dc7907078 | hotpotqa | train | always_rag | always_rag:2 |
| hotpotqa__5ae617285542996de7b71b4c | hotpotqa | train | always_rag | always_rag:2 |
| musique__2hop__42027_42004 | musique | test | llm_only | llm_only:2 |
| triviaqa__dev_8240 | triviaqa | train | llm_only | llm_only:2 |

Excluded per dataset: hotpotqa 4, musique 1, triviaqa 1

Calls and retries:

| system | calls | qids retried | recovered on retry |
|---|---|---|---|
| llm_only | 3023 | 23 | 20 |
| always_rag | 3011 | 11 | 7 |
| llm_decision | 3000 | 0 | 0 |

## Main results (all splits)

Tokens and cost include the router call for `llm_decision_router`. Failed calls count as wrong.

| dataset | system | n | EM | F1 | Acc | in tok | out tok | reas tok | $/q | retr calls | failed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2wikimultihopqa | llm_only | 500 | 0.214 | 0.302 | 0.276 | 43.5 | 24.1 | 0.00 | 0.0000118 | 0 | 0 |
| 2wikimultihopqa | always_rag | 500 | 0.266 | 0.412 | 0.404 | 663.8 | 25.5 | 0.00 | 0.0000434 | 500 | 0 |
| 2wikimultihopqa | oracle | 500 | 0.356 | 0.480 | 0.494 | 181.7 | 24.6 | 0.00 | 0.0000189 | 109 | 0 |
| 2wikimultihopqa | llm_decision_router | 500 | 0.244 | 0.392 | 0.382 | 623.5 | 44.4 | 0.00 | 0.0000489 | 420 | 0 |
| ALL | llm_only | 2994 | 0.198 | 0.317 | 0.310 | 43.0 | 25.3 | 0.00 | 0.0000123 | 0 | 7 |
| ALL | always_rag | 2994 | 0.273 | 0.412 | 0.403 | 669.9 | 24.7 | 0.00 | 0.0000434 | 2994 | 9 |
| ALL | oracle | 2994 | 0.310 | 0.448 | 0.478 | 149.6 | 25.4 | 0.00 | 0.0000176 | 503 | 7 |
| ALL | llm_decision_router | 2994 | 0.263 | 0.403 | 0.392 | 622.4 | 43.7 | 0.00 | 0.0000486 | 2523 | 10 |
| hotpotqa | llm_only | 496 | 0.171 | 0.294 | 0.248 | 47.0 | 26.9 | 0.00 | 0.0000131 | 0 | 3 |
| hotpotqa | always_rag | 496 | 0.272 | 0.442 | 0.385 | 437.3 | 25.5 | 0.00 | 0.0000321 | 496 | 4 |
| hotpotqa | oracle | 496 | 0.294 | 0.433 | 0.427 | 116.8 | 27.4 | 0.00 | 0.0000168 | 89 | 3 |
| hotpotqa | llm_decision_router | 496 | 0.250 | 0.415 | 0.353 | 386.6 | 44.3 | 0.00 | 0.0000371 | 370 | 4 |
| musique | llm_only | 499 | 0.032 | 0.125 | 0.080 | 48.2 | 26.1 | 0.00 | 0.0000129 | 0 | 3 |
| musique | always_rag | 499 | 0.050 | 0.157 | 0.114 | 642.0 | 26.7 | 0.00 | 0.0000428 | 499 | 4 |
| musique | oracle | 499 | 0.072 | 0.183 | 0.166 | 94.1 | 26.0 | 0.00 | 0.0000151 | 43 | 3 |
| musique | llm_decision_router | 499 | 0.048 | 0.153 | 0.110 | 587.3 | 45.8 | 0.00 | 0.0000477 | 411 | 5 |
| nq | llm_only | 500 | 0.152 | 0.309 | 0.320 | 38.1 | 25.6 | 0.00 | 0.0000122 | 0 | 0 |
| nq | always_rag | 500 | 0.280 | 0.444 | 0.454 | 752.1 | 24.1 | 0.00 | 0.0000472 | 500 | 0 |
| nq | oracle | 500 | 0.298 | 0.473 | 0.530 | 189.5 | 25.6 | 0.00 | 0.0000197 | 105 | 0 |
| nq | llm_decision_router | 500 | 0.266 | 0.431 | 0.440 | 684.5 | 43.4 | 0.00 | 0.0000516 | 427 | 0 |
| popqa | llm_only | 500 | 0.174 | 0.276 | 0.294 | 35.7 | 24.0 | 0.00 | 0.0000114 | 0 | 0 |
| popqa | always_rag | 500 | 0.292 | 0.400 | 0.420 | 757.2 | 22.8 | 0.00 | 0.0000470 | 500 | 0 |
| popqa | oracle | 500 | 0.316 | 0.441 | 0.498 | 189.4 | 23.9 | 0.00 | 0.0000190 | 102 | 0 |
| popqa | llm_decision_router | 500 | 0.290 | 0.398 | 0.418 | 763.3 | 41.8 | 0.00 | 0.0000549 | 480 | 0 |
| triviaqa | llm_only | 499 | 0.443 | 0.595 | 0.639 | 45.5 | 24.8 | 0.00 | 0.0000122 | 0 | 1 |
| triviaqa | always_rag | 499 | 0.477 | 0.620 | 0.643 | 765.0 | 23.4 | 0.00 | 0.0000476 | 499 | 1 |
| triviaqa | oracle | 499 | 0.521 | 0.676 | 0.749 | 125.6 | 24.9 | 0.00 | 0.0000162 | 55 | 1 |
| triviaqa | llm_decision_router | 499 | 0.477 | 0.627 | 0.649 | 687.3 | 42.6 | 0.00 | 0.0000514 | 415 | 1 |

## Test split only

| dataset | system | n | EM | F1 | Acc | in tok | out tok | reas tok | $/q | retr calls | failed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ALL | llm_only | 599 | 0.200 | 0.316 | 0.307 | 43.1 | 25.9 | 0.00 | 0.0000125 | 0 | 2 |
| ALL | always_rag | 599 | 0.282 | 0.417 | 0.419 | 663.6 | 24.1 | 0.00 | 0.0000428 | 599 | 1 |
| ALL | oracle | 599 | 0.321 | 0.463 | 0.494 | 158.4 | 25.4 | 0.00 | 0.0000181 | 112 | 2 |
| ALL | llm_decision_router | 599 | 0.274 | 0.412 | 0.401 | 613.5 | 43.4 | 0.00 | 0.0000480 | 500 | 2 |

## Adaptive-RAG comparison: Adaptive-RAG's gold answers

Gold = what Adaptive-RAG/IRCoT score against, without our short-alias filter: NQ/TriviaQA the full DPR answer list, HotpotQA/2Wiki/MuSiQue the single IRCoT answer, PopQA (not in Adaptive-RAG) all `possible_answers`. Accuracy is still token-bounded containment. Base systems only.

| dataset | system | EM | F1 | Acc |
|---|---|---|---|---|
| 2wikimultihopqa | llm_only | 0.202 | 0.278 | 0.262 |
| 2wikimultihopqa | always_rag | 0.242 | 0.373 | 0.378 |
| ALL | llm_only | 0.195 | 0.311 | 0.304 |
| ALL | always_rag | 0.267 | 0.403 | 0.395 |
| hotpotqa | llm_only | 0.171 | 0.294 | 0.248 |
| hotpotqa | always_rag | 0.272 | 0.442 | 0.385 |
| musique | llm_only | 0.026 | 0.114 | 0.060 |
| musique | always_rag | 0.040 | 0.142 | 0.090 |
| nq | llm_only | 0.152 | 0.309 | 0.320 |
| nq | always_rag | 0.280 | 0.444 | 0.454 |
| popqa | llm_only | 0.174 | 0.276 | 0.294 |
| popqa | always_rag | 0.292 | 0.400 | 0.420 |
| triviaqa | llm_only | 0.443 | 0.595 | 0.641 |
| triviaqa | always_rag | 0.477 | 0.620 | 0.643 |

## Outcome labels

`no_retrieval_ok` = llm_only correct (= both_ok + rag_hurts); `rag_hurts` = llm_only correct, always_rag wrong; `retrieval_needed` = llm_only wrong, always_rag correct; `both_fail` = both wrong.

| dataset | n | no_retrieval_ok | both_ok | rag_hurts | retrieval_needed | both_fail |
|---|---|---|---|---|---|---|
| 2wikimultihopqa | 500 | 138 | 93 | 45 | 109 | 253 |
| hotpotqa | 496 | 123 | 102 | 21 | 89 | 284 |
| musique | 499 | 40 | 14 | 26 | 43 | 416 |
| nq | 500 | 160 | 122 | 38 | 105 | 235 |
| popqa | 500 | 147 | 108 | 39 | 102 | 251 |
| triviaqa | 499 | 319 | 266 | 53 | 55 | 125 |
| ALL | 2994 | 927 | 705 | 222 | 503 | 1564 |

### rag_hurts per dataset and split

| dataset | train | dev | test | all |
|---|---|---|---|---|
| 2wikimultihopqa | 31 | 3 | 11 | 45 |
| hotpotqa | 13 | 5 | 3 | 21 |
| musique | 17 | 3 | 6 | 26 |
| nq | 21 | 10 | 7 | 38 |
| popqa | 22 | 8 | 9 | 39 |
| triviaqa | 32 | 12 | 9 | 53 |
| ALL | 136 | 41 | 45 | 222 |

## Oracle vs Always-RAG

Oracle accuracy 0.478 vs Always-RAG 0.403; cost per question $0.0000176 vs $0.0000434 (**59.3% cheaper**); retrieval calls 503 vs 2994 (83.2% fewer).

## llm_decision router (the model's own YES/NO)

Route: YES -> llm_only, NO/invalid -> always_rag. Decision cost is charged as router cost. `agree w/ oracle` is dominated by both_fail questions (the oracle sends them to llm_only by convention); `agree on decisive` uses only rag_hurts + retrieval_needed, where the route changes the outcome.

| dataset | n | YES | NO | invalid | agree w/ oracle | decisive q | agree on decisive | YES<->llm_only correct | P(llm_only correct | YES) | llm_only correct rate |
|---|---|---|---|---|---|---|---|---|---|---|
| 2wikimultihopqa | 500 | 80 | 420 | 0 | 0.286 | 154 | 0.636 | 0.704 | 0.438 | 0.276 |
| hotpotqa | 496 | 126 | 370 | 0 | 0.353 | 110 | 0.664 | 0.667 | 0.333 | 0.248 |
| musique | 499 | 88 | 411 | 0 | 0.242 | 69 | 0.594 | 0.764 | 0.057 | 0.080 |
| nq | 500 | 73 | 427 | 0 | 0.308 | 143 | 0.685 | 0.642 | 0.370 | 0.320 |
| popqa | 500 | 20 | 480 | 0 | 0.236 | 141 | 0.716 | 0.694 | 0.350 | 0.294 |
| triviaqa | 499 | 84 | 415 | 0 | 0.251 | 108 | 0.537 | 0.417 | 0.667 | 0.639 |
| ALL | 2994 | 471 | 2523 | 0 | 0.279 | 725 | 0.647 | 0.648 | 0.365 | 0.310 |

Confusion vs oracle route (all datasets):

| | oracle: llm_only | oracle: always_rag |
|---|---|---|
| decision YES | 402 | 69 |
| decision NO/invalid | 2089 | 434 |

Score and cost (incl. decision call): accuracy 0.392, $0.0000486/q (router $0.0000097, generation $0.0000389); retrieval rate 84.3%.

Decision call tokens (mean per question): input 42.0, output 19.0, reasoning 0.00.

## Break-even: decision cost vs. skipped context

For questions the decision routes to llm_only (YES), skipping retrieval saves the context tokens (always_rag input − llm_only input) and the cost difference. Ratio < 1 means the decision call pays for itself. `breakeven_skip_rate` = decision cost per question / mean saving per skipped question; the router must skip at least this share of questions to break even on cost.

| dataset | n | skipped | saved ctx tok | decision tok (in+out) | tok ratio | decision $ | saved $ | $ ratio | break-even skip rate | actual skip rate |
|---|---|---|---|---|---|---|---|---|---|---|
| 2wikimultihopqa | 500 | 80 | 41437 | 30772 | 0.743 | 0.00486 | 0.00209 | 2.331 | 0.308 | 0.160 |
| hotpotqa | 496 | 126 | 47986 | 32258 | 0.672 | 0.00491 | 0.00243 | 2.024 | 0.523 | 0.254 |
| musique | 499 | 88 | 50848 | 33015 | 0.649 | 0.00497 | 0.00253 | 1.965 | 0.333 | 0.176 |
| nq | 500 | 73 | 52332 | 28068 | 0.536 | 0.00473 | 0.00256 | 1.850 | 0.270 | 0.146 |
| popqa | 500 | 20 | 14289 | 26848 | 1.879 | 0.00467 | 0.00072 | 6.486 | 0.262 | 0.040 |
| triviaqa | 499 | 84 | 60951 | 31674 | 0.520 | 0.00490 | 0.00301 | 1.626 | 0.277 | 0.168 |
| ALL | 2994 | 471 | 267843 | 182635 | 0.682 | 0.02904 | 0.01333 | 2.178 | 0.312 | 0.157 |

## Latency (sequential run, test subset)

198 test questions with valid records for all three calls (dropped: 1); concurrency 1, fresh retrieval. Adaptive = decision call followed by the chosen path, run sequentially; 30 of 198 routed to llm_only.

| system | n | mean ms | P50 ms | P95 ms |
|---|---|---|---|---|
| llm_only | 198 | 1434 | 991 | 2660 |
| always_rag | 198 | 1624 | 1028 | 4121 |
| llm_decision_call_only | 198 | 1097 | 888 | 1383 |
| adaptive_llm_decision (decision + chosen path) | 198 | 2758 | 1990 | 6405 |
| always_rag: retrieval part only | 198 | 68 | 62 | 140 |

| comparison | mean diff ms | CI lo | CI hi | median diff ms | CI lo | CI hi |
|---|---|---|---|---|---|---|
| adaptive - always_rag | 1134 | 878 | 1417 | 961 | 902 | 1013 |
| adaptive - llm_only | 1324 | 899 | 1762 | 999 | 931 | 1088 |
| always_rag - llm_only | 190 | -242 | 640 | 37 | -2 | 125 |

## Paired bootstrap differences (all datasets)

| comparison | metric | diff | CI lo | CI hi | CI excludes 0 |
|---|---|---|---|---|---|
| always_rag - llm_only | accuracy | 0.0939 | 0.0768 | 0.1109 | True |
| always_rag - llm_only | usd_per_1k_q | 0.0311 | 0.0306 | 0.0316 | True |
| oracle - always_rag | accuracy | 0.0741 | 0.0651 | 0.0835 | True |
| oracle - always_rag | usd_per_1k_q | -0.0257 | -0.0263 | -0.0251 | True |
| oracle - llm_only | accuracy | 0.1680 | 0.1553 | 0.1817 | True |
| oracle - llm_only | usd_per_1k_q | 0.0054 | 0.0049 | 0.0058 | True |
| llm_decision_router - always_rag | accuracy | -0.0114 | -0.0184 | -0.0047 | True |
| llm_decision_router - always_rag | usd_per_1k_q | 0.0052 | 0.0048 | 0.0056 | True |
| llm_decision_router - llm_only | accuracy | 0.0825 | 0.0665 | 0.0982 | True |
| llm_decision_router - llm_only | usd_per_1k_q | 0.0364 | 0.0358 | 0.0369 | True |
| llm_decision_router - oracle | accuracy | -0.0855 | -0.0959 | -0.0758 | True |
| llm_decision_router - oracle | usd_per_1k_q | 0.0310 | 0.0303 | 0.0317 | True |

Per-dataset intervals: `bootstrap.csv`.

## Reasoning leakage

Leak = `incomplete` (hit max_output_tokens) or >= 17 words or a deliberation marker (see `src/leakage.py`). Common question set; final record per question.

| system | n | leaked | rate | incomplete | >=17 words | marker |
|---|---|---|---|---|---|---|
| llm_only | 2994 | 86 | 0.029 | 7 | 65 | 80 |
| always_rag | 2994 | 55 | 0.018 | 9 | 36 | 51 |
| llm_decision | 2994 | 0 | 0.000 | 0 | 0 | 0 |

Per dataset: `leakage.csv`.


## Calls logged per question

Sent means a call was logged. Both paths call the model; `route` on `llm_decision` is which path that call selected (`llm_only` or `always_rag`). A question rejected by the filter twice stays sent and leaves `in_comparison`. Source attributes on the same rows are in `dispatch.csv`.

- `deepseek-flash`: 3000/3000 questions have an `llm_only` call; 3000 are in the comparison set.
- `gpt-5-nano-2025-08-07`: 3000/3000 questions have an `llm_only` call; 2994 are in the comparison set.

## Accuracy and cost by source attribute

Cuts are the attributes the source datasets define. They are not one difficulty scale, and they are not model outcomes. NQ and TriviaQA have no source difficulty field; they appear only under `hop_type`. Intervals are percentile bootstrap CIs of the mean. Full tables: `strata.csv`, `model_compare.csv`.

### deepseek-flash

**hop_type.** single vs multi; the only cut defined for every question

| value | system | n | Acc | CI lo | CI hi | $/q |
|---|---|---|---|---|---|---|
| multi | llm_only | 1500 | 0.293 | 0.270 | 0.315 | 0.0000088 |
| multi | always_rag | 1500 | 0.374 | 0.350 | 0.399 | 0.0000891 |
| multi | oracle | 1500 | 0.441 | 0.416 | 0.466 | 0.0000207 |
| multi | llm_decision_router | 1500 | 0.363 | 0.339 | 0.388 | 0.0000852 |
| single | llm_only | 1500 | 0.580 | 0.555 | 0.605 | 0.0000076 |
| single | always_rag | 1500 | 0.568 | 0.543 | 0.593 | 0.0001151 |
| single | oracle | 1500 | 0.679 | 0.655 | 0.703 | 0.0000186 |
| single | llm_decision_router | 1500 | 0.575 | 0.550 | 0.601 | 0.0000906 |

**pop_tertile.** thirds of log10(s_pop) on the frozen PopQA sample; low is least popular. Not a difficulty ranking.

| value | system | n | Acc | CI lo | CI hi | $/q |
|---|---|---|---|---|---|---|
| high | llm_only | 167 | 0.647 | 0.575 | 0.719 | 0.0000068 |
| high | always_rag | 167 | 0.491 | 0.413 | 0.569 | 0.0001103 |
| high | oracle | 167 | 0.701 | 0.629 | 0.766 | 0.0000129 |
| high | llm_decision_router | 167 | 0.503 | 0.425 | 0.581 | 0.0000945 |
| low | llm_only | 167 | 0.371 | 0.299 | 0.449 | 0.0000072 |
| low | always_rag | 167 | 0.461 | 0.383 | 0.533 | 0.0001127 |
| low | oracle | 167 | 0.545 | 0.467 | 0.623 | 0.0000271 |
| low | llm_decision_router | 167 | 0.461 | 0.383 | 0.533 | 0.0001106 |
| mid | llm_only | 166 | 0.392 | 0.319 | 0.464 | 0.0000070 |
| mid | always_rag | 166 | 0.386 | 0.313 | 0.458 | 0.0001137 |
| mid | oracle | 166 | 0.512 | 0.440 | 0.584 | 0.0000206 |
| mid | llm_decision_router | 166 | 0.392 | 0.319 | 0.464 | 0.0001064 |

**musique_hops.** hop count from the MuSiQue id; subtypes such as 3hop1 and 4hop2 collapse to 3 and 4

| value | system | n | Acc | CI lo | CI hi | $/q |
|---|---|---|---|---|---|---|
| 2 | llm_only | 251 | 0.151 | 0.108 | 0.195 | 0.0000083 |
| 2 | always_rag | 251 | 0.227 | 0.175 | 0.279 | 0.0000952 |
| 2 | oracle | 251 | 0.299 | 0.243 | 0.355 | 0.0000208 |
| 2 | llm_decision_router | 251 | 0.215 | 0.167 | 0.267 | 0.0000956 |
| 3 | llm_only | 155 | 0.110 | 0.065 | 0.161 | 0.0000095 |
| 3 | always_rag | 155 | 0.123 | 0.071 | 0.181 | 0.0001003 |
| 3 | oracle | 155 | 0.181 | 0.123 | 0.245 | 0.0000157 |
| 3 | llm_decision_router | 155 | 0.123 | 0.071 | 0.181 | 0.0001071 |
| 4 | llm_only | 94 | 0.043 | 0.011 | 0.085 | 0.0000102 |
| 4 | always_rag | 94 | 0.085 | 0.032 | 0.149 | 0.0000980 |
| 4 | oracle | 94 | 0.085 | 0.032 | 0.149 | 0.0000133 |
| 4 | llm_decision_router | 94 | 0.085 | 0.032 | 0.149 | 0.0001066 |

**hotpot_type.** HotpotQA level is hard for every question in this sample; type is not a difficulty rank

| value | system | n | Acc | CI lo | CI hi | $/q |
|---|---|---|---|---|---|---|
| bridge | llm_only | 395 | 0.271 | 0.228 | 0.314 | 0.0000090 |
| bridge | always_rag | 395 | 0.365 | 0.319 | 0.413 | 0.0000691 |
| bridge | oracle | 395 | 0.456 | 0.408 | 0.506 | 0.0000200 |
| bridge | llm_decision_router | 395 | 0.352 | 0.306 | 0.400 | 0.0000648 |
| comparison | llm_only | 105 | 0.705 | 0.619 | 0.790 | 0.0000077 |
| comparison | always_rag | 105 | 0.733 | 0.648 | 0.819 | 0.0000645 |
| comparison | oracle | 105 | 0.752 | 0.667 | 0.829 | 0.0000098 |
| comparison | llm_decision_router | 105 | 0.705 | 0.619 | 0.790 | 0.0000409 |

**wiki_type.** 2Wiki reasoning type, not a difficulty rank

| value | system | n | Acc | CI lo | CI hi | $/q |
|---|---|---|---|---|---|---|
| bridge_comparison | llm_only | 96 | 0.573 | 0.469 | 0.677 | 0.0000094 |
| bridge_comparison | always_rag | 96 | 0.677 | 0.583 | 0.771 | 0.0000810 |
| bridge_comparison | oracle | 96 | 0.802 | 0.719 | 0.875 | 0.0000268 |
| bridge_comparison | llm_decision_router | 96 | 0.656 | 0.562 | 0.750 | 0.0000631 |
| comparison | llm_only | 137 | 0.752 | 0.679 | 0.825 | 0.0000088 |
| comparison | always_rag | 137 | 0.883 | 0.832 | 0.934 | 0.0000863 |
| comparison | oracle | 137 | 0.942 | 0.898 | 0.978 | 0.0000245 |
| comparison | llm_decision_router | 137 | 0.854 | 0.796 | 0.912 | 0.0000672 |
| compositional | llm_only | 205 | 0.146 | 0.102 | 0.195 | 0.0000077 |
| compositional | always_rag | 205 | 0.263 | 0.205 | 0.322 | 0.0001139 |
| compositional | oracle | 205 | 0.302 | 0.239 | 0.366 | 0.0000250 |
| compositional | llm_decision_router | 205 | 0.254 | 0.195 | 0.312 | 0.0001180 |
| inference | llm_only | 62 | 0.177 | 0.081 | 0.274 | 0.0000104 |
| inference | always_rag | 62 | 0.258 | 0.161 | 0.371 | 0.0001294 |
| inference | oracle | 62 | 0.371 | 0.258 | 0.500 | 0.0000345 |
| inference | llm_decision_router | 62 | 0.290 | 0.177 | 0.403 | 0.0001256 |

**Taken into account.** These cuts stay separate. No easy/medium/hard label is assigned: HotpotQA's official level is hard on every question in this sample, NQ and TriviaQA publish none, PopQA's tertiles are popularity, and 2Wiki's type is a reasoning type. Outcome labels are not treated as difficulty.

On the point estimate, the decision router is above Always-RAG only on: hop_type=single +0.007 (n=1500; intervals overlap), pop_tertile=high +0.012 (n=167; intervals overlap), pop_tertile=mid +0.006 (n=166; intervals overlap), wiki_type=inference +0.032 (n=62; intervals overlap). The largest gap elsewhere is wiki_type=comparison -0.029 (n=137; intervals overlap).

Where retrieval itself moves accuracy: PopQA least popular: Always-RAG 0.461 against llm-only 0.371 (n=167); PopQA most popular: Always-RAG 0.491 against llm-only 0.647 (n=167); MuSiQue 4-hop: Always-RAG 0.085 against llm-only 0.043 (n=94).


### gpt-5-nano-2025-08-07

**hop_type.** single vs multi; the only cut defined for every question

| value | system | n | Acc | CI lo | CI hi | $/q |
|---|---|---|---|---|---|---|
| multi | llm_only | 1495 | 0.201 | 0.181 | 0.221 | 0.0000126 |
| multi | always_rag | 1495 | 0.301 | 0.278 | 0.325 | 0.0000394 |
| multi | oracle | 1495 | 0.363 | 0.338 | 0.387 | 0.0000169 |
| multi | llm_decision_router | 1495 | 0.282 | 0.259 | 0.305 | 0.0000446 |
| single | llm_only | 1499 | 0.418 | 0.392 | 0.443 | 0.0000119 |
| single | always_rag | 1499 | 0.506 | 0.480 | 0.531 | 0.0000473 |
| single | oracle | 1499 | 0.592 | 0.568 | 0.617 | 0.0000183 |
| single | llm_decision_router | 1499 | 0.502 | 0.477 | 0.527 | 0.0000526 |

**pop_tertile.** thirds of log10(s_pop) on the frozen PopQA sample; low is least popular. Not a difficulty ranking.

| value | system | n | Acc | CI lo | CI hi | $/q |
|---|---|---|---|---|---|---|
| high | llm_only | 167 | 0.443 | 0.365 | 0.521 | 0.0000117 |
| high | always_rag | 167 | 0.449 | 0.371 | 0.527 | 0.0000465 |
| high | oracle | 167 | 0.581 | 0.503 | 0.653 | 0.0000167 |
| high | llm_decision_router | 167 | 0.449 | 0.371 | 0.527 | 0.0000534 |
| low | llm_only | 167 | 0.210 | 0.150 | 0.275 | 0.0000113 |
| low | always_rag | 167 | 0.431 | 0.359 | 0.509 | 0.0000475 |
| low | oracle | 167 | 0.467 | 0.389 | 0.545 | 0.0000212 |
| low | llm_decision_router | 167 | 0.431 | 0.359 | 0.509 | 0.0000566 |
| mid | llm_only | 166 | 0.229 | 0.169 | 0.295 | 0.0000112 |
| mid | always_rag | 166 | 0.380 | 0.307 | 0.452 | 0.0000470 |
| mid | oracle | 166 | 0.446 | 0.373 | 0.524 | 0.0000193 |
| mid | llm_decision_router | 166 | 0.373 | 0.301 | 0.446 | 0.0000547 |

**musique_hops.** hop count from the MuSiQue id; subtypes such as 3hop1 and 4hop2 collapse to 3 and 4

| value | system | n | Acc | CI lo | CI hi | $/q |
|---|---|---|---|---|---|---|
| 2 | llm_only | 250 | 0.096 | 0.060 | 0.136 | 0.0000133 |
| 2 | always_rag | 250 | 0.164 | 0.120 | 0.212 | 0.0000415 |
| 2 | oracle | 250 | 0.224 | 0.172 | 0.276 | 0.0000165 |
| 2 | llm_decision_router | 250 | 0.160 | 0.116 | 0.208 | 0.0000474 |
| 3 | llm_only | 155 | 0.065 | 0.026 | 0.103 | 0.0000127 |
| 3 | always_rag | 155 | 0.097 | 0.052 | 0.148 | 0.0000437 |
| 3 | oracle | 155 | 0.129 | 0.077 | 0.187 | 0.0000146 |
| 3 | llm_decision_router | 155 | 0.077 | 0.039 | 0.123 | 0.0000479 |
| 4 | llm_only | 94 | 0.064 | 0.021 | 0.117 | 0.0000119 |
| 4 | always_rag | 94 | 0.011 | 0.000 | 0.032 | 0.0000446 |
| 4 | oracle | 94 | 0.074 | 0.021 | 0.128 | 0.0000122 |
| 4 | llm_decision_router | 94 | 0.032 | 0.000 | 0.074 | 0.0000481 |

**hotpot_type.** HotpotQA level is hard for every question in this sample; type is not a difficulty rank

| value | system | n | Acc | CI lo | CI hi | $/q |
|---|---|---|---|---|---|---|
| bridge | llm_only | 391 | 0.136 | 0.102 | 0.169 | 0.0000137 |
| bridge | always_rag | 391 | 0.299 | 0.253 | 0.345 | 0.0000327 |
| bridge | oracle | 391 | 0.335 | 0.289 | 0.381 | 0.0000178 |
| bridge | llm_decision_router | 391 | 0.263 | 0.220 | 0.307 | 0.0000379 |
| comparison | llm_only | 105 | 0.667 | 0.571 | 0.752 | 0.0000111 |
| comparison | always_rag | 105 | 0.705 | 0.619 | 0.790 | 0.0000297 |
| comparison | oracle | 105 | 0.771 | 0.686 | 0.848 | 0.0000130 |
| comparison | llm_decision_router | 105 | 0.686 | 0.600 | 0.771 | 0.0000340 |

**wiki_type.** 2Wiki reasoning type, not a difficulty rank

| value | system | n | Acc | CI lo | CI hi | $/q |
|---|---|---|---|---|---|---|
| bridge_comparison | llm_only | 96 | 0.490 | 0.385 | 0.594 | 0.0000114 |
| bridge_comparison | always_rag | 96 | 0.531 | 0.427 | 0.635 | 0.0000353 |
| bridge_comparison | oracle | 96 | 0.750 | 0.656 | 0.833 | 0.0000186 |
| bridge_comparison | llm_decision_router | 96 | 0.500 | 0.396 | 0.604 | 0.0000377 |
| comparison | llm_only | 137 | 0.496 | 0.409 | 0.577 | 0.0000116 |
| comparison | always_rag | 137 | 0.723 | 0.642 | 0.796 | 0.0000374 |
| comparison | oracle | 137 | 0.847 | 0.781 | 0.905 | 0.0000210 |
| comparison | llm_decision_router | 137 | 0.672 | 0.591 | 0.752 | 0.0000411 |
| compositional | llm_only | 205 | 0.093 | 0.054 | 0.137 | 0.0000114 |
| compositional | always_rag | 205 | 0.185 | 0.132 | 0.239 | 0.0000477 |
| compositional | oracle | 205 | 0.210 | 0.156 | 0.268 | 0.0000163 |
| compositional | llm_decision_router | 205 | 0.180 | 0.127 | 0.234 | 0.0000550 |
| inference | llm_only | 62 | 0.065 | 0.016 | 0.129 | 0.0000143 |
| inference | always_rag | 62 | 0.226 | 0.129 | 0.339 | 0.0000550 |
| inference | oracle | 62 | 0.258 | 0.161 | 0.371 | 0.0000236 |
| inference | llm_decision_router | 62 | 0.226 | 0.129 | 0.339 | 0.0000636 |

**Taken into account.** These cuts stay separate. No easy/medium/hard label is assigned: HotpotQA's official level is hard on every question in this sample, NQ and TriviaQA publish none, PopQA's tertiles are popularity, and 2Wiki's type is a reasoning type. Outcome labels are not treated as difficulty.

On the point estimate, the decision router is above Always-RAG only on: musique_hops=4 +0.021 (n=94; intervals overlap). The largest gap elsewhere is wiki_type=comparison -0.051 (n=137; intervals overlap).

Where retrieval itself moves accuracy: PopQA least popular: Always-RAG 0.431 against llm-only 0.210 (n=167); PopQA most popular: Always-RAG 0.449 against llm-only 0.443 (n=167); MuSiQue 4-hop: Always-RAG 0.011 against llm-only 0.064 (n=94).

### Paired model difference (A − B)

Same questions, same route. A positive accuracy difference means A is higher.

| stratum | value | system | n | acc A-B | CI lo | CI hi | $/q A-B |
|---|---|---|---|---|---|---|---|
| hop_type | multi | llm_only | 1495 | -0.092 | -0.114 | -0.071 | 0.0000038 |
| hop_type | multi | always_rag | 1495 | -0.074 | -0.094 | -0.052 | -0.0000498 |
| hop_type | multi | oracle | 1495 | -0.079 | -0.101 | -0.057 | -0.0000038 |
| hop_type | multi | llm_decision_router | 1495 | -0.082 | -0.104 | -0.060 | -0.0000406 |
| hop_type | single | llm_only | 1499 | -0.162 | -0.185 | -0.139 | 0.0000043 |
| hop_type | single | always_rag | 1499 | -0.063 | -0.082 | -0.044 | -0.0000678 |
| hop_type | single | oracle | 1499 | -0.087 | -0.107 | -0.067 | -0.0000003 |
| hop_type | single | llm_decision_router | 1499 | -0.073 | -0.093 | -0.053 | -0.0000380 |
| pop_tertile | high | llm_only | 167 | -0.204 | -0.275 | -0.132 | 0.0000049 |
| pop_tertile | high | always_rag | 167 | -0.042 | -0.090 | 0.006 | -0.0000638 |
| pop_tertile | high | oracle | 167 | -0.120 | -0.186 | -0.054 | 0.0000038 |
| pop_tertile | high | llm_decision_router | 167 | -0.054 | -0.108 | 0.000 | -0.0000411 |
| pop_tertile | low | llm_only | 167 | -0.162 | -0.234 | -0.090 | 0.0000041 |
| pop_tertile | low | always_rag | 167 | -0.030 | -0.072 | 0.006 | -0.0000652 |
| pop_tertile | low | oracle | 167 | -0.078 | -0.132 | -0.024 | -0.0000059 |
| pop_tertile | low | llm_decision_router | 167 | -0.030 | -0.072 | 0.006 | -0.0000540 |
| pop_tertile | mid | llm_only | 166 | -0.163 | -0.229 | -0.096 | 0.0000043 |
| pop_tertile | mid | always_rag | 166 | -0.006 | -0.030 | 0.018 | -0.0000667 |
| pop_tertile | mid | oracle | 166 | -0.066 | -0.114 | -0.018 | -0.0000013 |
| pop_tertile | mid | llm_decision_router | 166 | -0.018 | -0.054 | 0.018 | -0.0000517 |
| musique_hops | 2.0 | llm_only | 250 | -0.056 | -0.104 | -0.012 | 0.0000050 |
| musique_hops | 2.0 | always_rag | 250 | -0.064 | -0.116 | -0.012 | -0.0000536 |
| musique_hops | 2.0 | oracle | 250 | -0.076 | -0.132 | -0.020 | -0.0000044 |
| musique_hops | 2.0 | llm_decision_router | 250 | -0.056 | -0.108 | -0.004 | -0.0000482 |
| musique_hops | 3.0 | llm_only | 155 | -0.045 | -0.097 | 0.000 | 0.0000032 |
| musique_hops | 3.0 | always_rag | 155 | -0.026 | -0.071 | 0.019 | -0.0000566 |
| musique_hops | 3.0 | oracle | 155 | -0.052 | -0.103 | 0.000 | -0.0000011 |
| musique_hops | 3.0 | llm_decision_router | 155 | -0.045 | -0.097 | 0.006 | -0.0000592 |
| musique_hops | 4.0 | llm_only | 94 | 0.021 | -0.043 | 0.085 | 0.0000017 |
| musique_hops | 4.0 | always_rag | 94 | -0.074 | -0.128 | -0.021 | -0.0000534 |
| musique_hops | 4.0 | oracle | 94 | -0.011 | -0.085 | 0.064 | -0.0000012 |
| musique_hops | 4.0 | llm_decision_router | 94 | -0.053 | -0.117 | 0.011 | -0.0000585 |
| hotpot_type | bridge | llm_only | 391 | -0.138 | -0.176 | -0.100 | 0.0000046 |
| hotpot_type | bridge | always_rag | 391 | -0.066 | -0.107 | -0.028 | -0.0000365 |
| hotpot_type | bridge | oracle | 391 | -0.123 | -0.164 | -0.082 | -0.0000022 |
| hotpot_type | bridge | llm_decision_router | 391 | -0.090 | -0.133 | -0.046 | -0.0000268 |
| hotpot_type | comparison | llm_only | 105 | -0.038 | -0.124 | 0.048 | 0.0000034 |
| hotpot_type | comparison | always_rag | 105 | -0.029 | -0.086 | 0.029 | -0.0000348 |
| hotpot_type | comparison | oracle | 105 | 0.019 | -0.038 | 0.076 | 0.0000031 |
| hotpot_type | comparison | llm_decision_router | 105 | -0.019 | -0.076 | 0.038 | -0.0000069 |
| wiki_type | bridge_comparison | llm_only | 96 | -0.083 | -0.208 | 0.042 | 0.0000020 |
| wiki_type | bridge_comparison | always_rag | 96 | -0.146 | -0.271 | -0.031 | -0.0000457 |
| wiki_type | bridge_comparison | oracle | 96 | -0.052 | -0.156 | 0.052 | -0.0000082 |
| wiki_type | bridge_comparison | llm_decision_router | 96 | -0.156 | -0.281 | -0.031 | -0.0000254 |
| wiki_type | comparison | llm_only | 137 | -0.255 | -0.358 | -0.153 | 0.0000028 |
| wiki_type | comparison | always_rag | 137 | -0.161 | -0.248 | -0.073 | -0.0000490 |
| wiki_type | comparison | oracle | 137 | -0.095 | -0.168 | -0.022 | -0.0000035 |
| wiki_type | comparison | llm_decision_router | 137 | -0.182 | -0.270 | -0.095 | -0.0000261 |
| wiki_type | compositional | llm_only | 205 | -0.054 | -0.098 | -0.010 | 0.0000037 |
| wiki_type | compositional | always_rag | 205 | -0.078 | -0.137 | -0.020 | -0.0000663 |
| wiki_type | compositional | oracle | 205 | -0.093 | -0.156 | -0.029 | -0.0000087 |
| wiki_type | compositional | llm_decision_router | 205 | -0.073 | -0.132 | -0.015 | -0.0000630 |
| wiki_type | inference | llm_only | 62 | -0.113 | -0.226 | -0.016 | 0.0000038 |
| wiki_type | inference | always_rag | 62 | -0.032 | -0.145 | 0.081 | -0.0000744 |
| wiki_type | inference | oracle | 62 | -0.113 | -0.242 | 0.016 | -0.0000109 |
| wiki_type | inference | llm_decision_router | 62 | -0.065 | -0.177 | 0.048 | -0.0000619 |

