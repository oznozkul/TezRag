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

Tokens, response time, and dollar cost include the router call for `llm_decision_router`. Response time is the logged model-call time. Local weights have a dollar cost of 0; tokens and response time are what stay comparable. Failed calls count as wrong.

| dataset | system | n | EM | F1 | Acc | in tok | out tok | reas tok | resp ms | $/q | retr calls | failed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2wikimultihopqa | llm_only | 500 | 0.214 | 0.302 | 0.276 | 43.5 | 24.1 | 0.00 | 1022 | 0.0000118 | 0 | 0 |
| 2wikimultihopqa | always_rag | 500 | 0.266 | 0.412 | 0.404 | 663.8 | 25.5 | 0.00 | 1154 | 0.0000434 | 500 | 0 |
| 2wikimultihopqa | oracle | 500 | 0.356 | 0.480 | 0.494 | 181.7 | 24.6 | 0.00 | 1033 | 0.0000189 | 109 | 0 |
| 2wikimultihopqa | llm_decision_router | 500 | 0.244 | 0.392 | 0.382 | 623.5 | 44.4 | 0.00 | 2008 | 0.0000489 | 420 | 0 |
| ALL | llm_only | 2994 | 0.198 | 0.317 | 0.310 | 43.0 | 25.3 | 0.00 | 1049 | 0.0000123 | 0 | 7 |
| ALL | always_rag | 2994 | 0.273 | 0.412 | 0.403 | 669.9 | 24.7 | 0.00 | 1100 | 0.0000434 | 2994 | 9 |
| ALL | oracle | 2994 | 0.310 | 0.448 | 0.478 | 149.6 | 25.4 | 0.00 | 1064 | 0.0000176 | 503 | 7 |
| ALL | llm_decision_router | 2994 | 0.263 | 0.403 | 0.392 | 622.4 | 43.7 | 0.00 | 1993 | 0.0000486 | 2523 | 10 |
| hotpotqa | llm_only | 496 | 0.171 | 0.294 | 0.248 | 47.0 | 26.9 | 0.00 | 1232 | 0.0000131 | 0 | 3 |
| hotpotqa | always_rag | 496 | 0.272 | 0.442 | 0.385 | 437.3 | 25.5 | 0.00 | 1018 | 0.0000321 | 496 | 4 |
| hotpotqa | oracle | 496 | 0.294 | 0.433 | 0.427 | 116.8 | 27.4 | 0.00 | 1158 | 0.0000168 | 89 | 3 |
| hotpotqa | llm_decision_router | 496 | 0.250 | 0.415 | 0.353 | 386.6 | 44.3 | 0.00 | 1957 | 0.0000371 | 370 | 4 |
| musique | llm_only | 499 | 0.032 | 0.125 | 0.080 | 48.2 | 26.1 | 0.00 | 969 | 0.0000129 | 0 | 3 |
| musique | always_rag | 499 | 0.050 | 0.157 | 0.114 | 642.0 | 26.7 | 0.00 | 1064 | 0.0000428 | 499 | 4 |
| musique | oracle | 499 | 0.072 | 0.183 | 0.166 | 94.1 | 26.0 | 0.00 | 965 | 0.0000151 | 43 | 3 |
| musique | llm_decision_router | 499 | 0.048 | 0.153 | 0.110 | 587.3 | 45.8 | 0.00 | 1978 | 0.0000477 | 411 | 5 |
| nq | llm_only | 500 | 0.152 | 0.309 | 0.320 | 38.1 | 25.6 | 0.00 | 1051 | 0.0000122 | 0 | 0 |
| nq | always_rag | 500 | 0.280 | 0.444 | 0.454 | 752.1 | 24.1 | 0.00 | 945 | 0.0000472 | 500 | 0 |
| nq | oracle | 500 | 0.298 | 0.473 | 0.530 | 189.5 | 25.6 | 0.00 | 1032 | 0.0000197 | 105 | 0 |
| nq | llm_decision_router | 500 | 0.266 | 0.431 | 0.440 | 684.5 | 43.4 | 0.00 | 1860 | 0.0000516 | 427 | 0 |
| popqa | llm_only | 500 | 0.174 | 0.276 | 0.294 | 35.7 | 24.0 | 0.00 | 1026 | 0.0000114 | 0 | 0 |
| popqa | always_rag | 500 | 0.292 | 0.400 | 0.420 | 757.2 | 22.8 | 0.00 | 1410 | 0.0000470 | 500 | 0 |
| popqa | oracle | 500 | 0.316 | 0.441 | 0.498 | 189.4 | 23.9 | 0.00 | 1206 | 0.0000190 | 102 | 0 |
| popqa | llm_decision_router | 500 | 0.290 | 0.398 | 0.418 | 763.3 | 41.8 | 0.00 | 2270 | 0.0000549 | 480 | 0 |
| triviaqa | llm_only | 499 | 0.443 | 0.595 | 0.639 | 45.5 | 24.8 | 0.00 | 995 | 0.0000122 | 0 | 1 |
| triviaqa | always_rag | 499 | 0.477 | 0.620 | 0.643 | 765.0 | 23.4 | 0.00 | 1005 | 0.0000476 | 499 | 1 |
| triviaqa | oracle | 499 | 0.521 | 0.676 | 0.749 | 125.6 | 24.9 | 0.00 | 992 | 0.0000162 | 55 | 1 |
| triviaqa | llm_decision_router | 499 | 0.477 | 0.627 | 0.649 | 687.3 | 42.6 | 0.00 | 1885 | 0.0000514 | 415 | 1 |

## Test split only

| dataset | system | n | EM | F1 | Acc | in tok | out tok | reas tok | resp ms | $/q | retr calls | failed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ALL | llm_only | 599 | 0.200 | 0.316 | 0.307 | 43.1 | 25.9 | 0.00 | 1058 | 0.0000125 | 0 | 2 |
| ALL | always_rag | 599 | 0.282 | 0.417 | 0.419 | 663.6 | 24.1 | 0.00 | 1166 | 0.0000428 | 599 | 1 |
| ALL | oracle | 599 | 0.321 | 0.463 | 0.494 | 158.4 | 25.4 | 0.00 | 1082 | 0.0000181 | 112 | 2 |
| ALL | llm_decision_router | 599 | 0.274 | 0.412 | 0.401 | 613.5 | 43.4 | 0.00 | 2016 | 0.0000480 | 500 | 2 |

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

- `claude-haiku-5-5`: 3000/3000 questions have an `llm_only` call; 3000 are in the comparison set.
- `deepseek-flash`: 3000/3000 questions have an `llm_only` call; 3000 are in the comparison set.
- `gemma4-e2b`: 3000/3000 questions have an `llm_only` call; 3000 are in the comparison set.
- `gpt-5-nano-2025-08-07`: 3000/3000 questions have an `llm_only` call; 2994 are in the comparison set.
- `llama3.2-3b`: 3000/3000 questions have an `llm_only` call; 3000 are in the comparison set.
- `qwen3.5-4b`: 3000/3000 questions have an `llm_only` call; 3000 are in the comparison set.

## Accuracy and cost by source attribute

Cuts are the attributes the source datasets define. They are not one difficulty scale, and they are not model outcomes. NQ and TriviaQA have no source difficulty field; they appear only under `hop_type`. Input tokens, output tokens, and response time include the router call. Dollar cost is 0 for local weights; tokens and response time are the comparable cost. Intervals are percentile bootstrap CIs of the mean. Full tables: `strata.csv`, `model_compare.csv`.

### claude-haiku-5-5

**hop_type.** single vs multi; the only cut defined for every question

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| multi | llm_only | 1500 | 0.241 | 0.219 | 0.263 | 67.7 | 34.4 | 954 | 0.0000240 |
| multi | always_rag | 1500 | 0.355 | 0.331 | 0.380 | 945.1 | 21.8 | 946 | 0.0001054 |
| multi | oracle | 1500 | 0.423 | 0.398 | 0.448 | 221.5 | 32.2 | 949 | 0.0000383 |
| multi | llm_decision_router | 1500 | 0.349 | 0.325 | 0.373 | 927.4 | 61.2 | 1898 | 0.0001234 |
| single | llm_only | 1500 | 0.532 | 0.507 | 0.557 | 56.8 | 16.7 | 913 | 0.0000140 |
| single | always_rag | 1500 | 0.559 | 0.534 | 0.584 | 1216.7 | 12.4 | 1045 | 0.0001279 |
| single | oracle | 1500 | 0.662 | 0.638 | 0.686 | 211.4 | 15.6 | 920 | 0.0000290 |
| single | llm_decision_router | 1500 | 0.567 | 0.542 | 0.592 | 1118.7 | 46.0 | 1960 | 0.0001349 |

**pop_tertile.** thirds of log10(s_pop) on the frozen PopQA sample; low is least popular. Not a difficulty ranking.

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| high | llm_only | 167 | 0.611 | 0.533 | 0.683 | 51.0 | 19.3 | 892 | 0.0000148 |
| high | always_rag | 167 | 0.509 | 0.431 | 0.587 | 1206.9 | 10.8 | 869 | 0.0001261 |
| high | oracle | 167 | 0.677 | 0.605 | 0.749 | 128.4 | 18.5 | 888 | 0.0000221 |
| high | llm_decision_router | 167 | 0.533 | 0.455 | 0.611 | 1102.9 | 45.4 | 1817 | 0.0001330 |
| low | llm_only | 167 | 0.216 | 0.156 | 0.281 | 52.1 | 24.5 | 916 | 0.0000174 |
| low | always_rag | 167 | 0.419 | 0.341 | 0.491 | 1230.1 | 13.7 | 876 | 0.0001299 |
| low | oracle | 167 | 0.485 | 0.407 | 0.563 | 381.5 | 21.9 | 908 | 0.0000491 |
| low | llm_decision_router | 167 | 0.413 | 0.335 | 0.491 | 1258.6 | 64.1 | 1892 | 0.0001579 |
| mid | llm_only | 166 | 0.295 | 0.229 | 0.361 | 51.7 | 21.8 | 912 | 0.0000161 |
| mid | always_rag | 166 | 0.386 | 0.313 | 0.458 | 1208.4 | 13.6 | 865 | 0.0001276 |
| mid | oracle | 166 | 0.494 | 0.416 | 0.572 | 289.0 | 20.0 | 901 | 0.0000389 |
| mid | llm_decision_router | 166 | 0.398 | 0.325 | 0.470 | 1205.0 | 59.9 | 1855 | 0.0001505 |

**musique_hops.** hop count from the MuSiQue id; subtypes such as 3hop1 and 4hop2 collapse to 3 and 4

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| 2 | llm_only | 251 | 0.175 | 0.127 | 0.223 | 62.2 | 36.6 | 964 | 0.0000245 |
| 2 | always_rag | 251 | 0.239 | 0.187 | 0.295 | 1016.4 | 22.8 | 941 | 0.0001130 |
| 2 | oracle | 251 | 0.339 | 0.279 | 0.398 | 205.5 | 35.2 | 964 | 0.0000381 |
| 2 | llm_decision_router | 251 | 0.235 | 0.183 | 0.287 | 999.3 | 65.6 | 1901 | 0.0001327 |
| 3 | llm_only | 155 | 0.142 | 0.090 | 0.200 | 73.7 | 62.5 | 1057 | 0.0000386 |
| 3 | always_rag | 155 | 0.174 | 0.116 | 0.239 | 1077.9 | 36.3 | 1024 | 0.0001260 |
| 3 | oracle | 155 | 0.226 | 0.161 | 0.290 | 148.8 | 58.4 | 1049 | 0.0000441 |
| 3 | llm_decision_router | 155 | 0.174 | 0.116 | 0.239 | 1086.8 | 88.1 | 2011 | 0.0001527 |
| 4 | llm_only | 94 | 0.096 | 0.043 | 0.160 | 79.5 | 89.3 | 1199 | 0.0000526 |
| 4 | always_rag | 94 | 0.117 | 0.053 | 0.181 | 1046.3 | 53.8 | 1037 | 0.0001315 |
| 4 | oracle | 94 | 0.170 | 0.096 | 0.245 | 157.2 | 86.8 | 1186 | 0.0000591 |
| 4 | llm_decision_router | 94 | 0.117 | 0.053 | 0.181 | 1114.7 | 118.8 | 2105 | 0.0001709 |

**hotpot_type.** HotpotQA level is hard for every question in this sample; type is not a difficulty rank

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| bridge | llm_only | 395 | 0.230 | 0.190 | 0.273 | 70.8 | 29.2 | 940 | 0.0000217 |
| bridge | always_rag | 395 | 0.344 | 0.299 | 0.392 | 728.7 | 15.8 | 918 | 0.0000808 |
| bridge | oracle | 395 | 0.410 | 0.362 | 0.458 | 188.6 | 25.9 | 932 | 0.0000318 |
| bridge | llm_decision_router | 395 | 0.329 | 0.284 | 0.375 | 688.0 | 46.7 | 1835 | 0.0000921 |
| comparison | llm_only | 105 | 0.686 | 0.590 | 0.771 | 64.3 | 11.7 | 836 | 0.0000123 |
| comparison | always_rag | 105 | 0.676 | 0.581 | 0.762 | 685.2 | 10.6 | 925 | 0.0000738 |
| comparison | oracle | 105 | 0.771 | 0.686 | 0.848 | 119.8 | 11.4 | 841 | 0.0000177 |
| comparison | llm_decision_router | 105 | 0.686 | 0.600 | 0.771 | 561.2 | 42.7 | 1837 | 0.0000775 |

**wiki_type.** 2Wiki reasoning type, not a difficulty rank

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| bridge_comparison | llm_only | 96 | 0.271 | 0.188 | 0.365 | 70.2 | 23.5 | 898 | 0.0000188 |
| bridge_comparison | always_rag | 96 | 0.531 | 0.427 | 0.635 | 852.2 | 20.7 | 916 | 0.0000956 |
| bridge_comparison | oracle | 96 | 0.583 | 0.479 | 0.677 | 310.6 | 22.5 | 900 | 0.0000423 |
| bridge_comparison | llm_decision_router | 96 | 0.521 | 0.417 | 0.625 | 828.6 | 78.3 | 1948 | 0.0001220 |
| comparison | llm_only | 137 | 0.482 | 0.401 | 0.569 | 66.9 | 17.2 | 884 | 0.0000153 |
| comparison | always_rag | 137 | 0.861 | 0.803 | 0.920 | 903.6 | 11.2 | 872 | 0.0000960 |
| comparison | oracle | 137 | 0.927 | 0.883 | 0.971 | 433.2 | 14.7 | 877 | 0.0000506 |
| comparison | llm_decision_router | 137 | 0.847 | 0.781 | 0.905 | 868.2 | 56.6 | 1834 | 0.0001151 |
| compositional | llm_only | 205 | 0.122 | 0.078 | 0.171 | 60.7 | 25.6 | 925 | 0.0000189 |
| compositional | always_rag | 205 | 0.215 | 0.161 | 0.273 | 1212.1 | 17.3 | 971 | 0.0001298 |
| compositional | oracle | 205 | 0.268 | 0.210 | 0.332 | 241.5 | 24.2 | 911 | 0.0000363 |
| compositional | llm_decision_router | 205 | 0.210 | 0.156 | 0.268 | 1227.4 | 39.1 | 1872 | 0.0001423 |
| inference | llm_only | 62 | 0.097 | 0.032 | 0.177 | 65.4 | 28.4 | 917 | 0.0000208 |
| inference | always_rag | 62 | 0.242 | 0.145 | 0.355 | 1343.0 | 30.1 | 966 | 0.0001494 |
| inference | oracle | 62 | 0.274 | 0.161 | 0.387 | 276.3 | 27.8 | 931 | 0.0000415 |
| inference | llm_decision_router | 62 | 0.242 | 0.145 | 0.355 | 1391.5 | 70.6 | 1952 | 0.0001744 |

**Taken into account.** These cuts stay separate. No easy/medium/hard label is assigned: HotpotQA's official level is hard on every question in this sample, NQ and TriviaQA publish none, PopQA's tertiles are popularity, and 2Wiki's type is a reasoning type. Outcome labels are not treated as difficulty.

On the point estimate, the decision router is above Always-RAG only on: hop_type=single +0.008 (n=1500; intervals overlap), pop_tertile=high +0.024 (n=167; intervals overlap), pop_tertile=mid +0.012 (n=166; intervals overlap), hotpot_type=comparison +0.010 (n=105; intervals overlap). The largest gap elsewhere is hotpot_type=bridge -0.015 (n=395; intervals overlap).

Where retrieval itself moves accuracy: PopQA least popular: Always-RAG 0.419 against llm-only 0.216 (n=167); PopQA most popular: Always-RAG 0.509 against llm-only 0.611 (n=167); MuSiQue 4-hop: Always-RAG 0.117 against llm-only 0.096 (n=94).


### deepseek-flash

**hop_type.** single vs multi; the only cut defined for every question

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| multi | llm_only | 1500 | 0.293 | 0.270 | 0.315 | 44.5 | 3.6 | 906 | 0.0000088 |
| multi | always_rag | 1500 | 0.374 | 0.350 | 0.399 | 584.7 | 3.9 | 843 | 0.0000891 |
| multi | oracle | 1500 | 0.441 | 0.416 | 0.466 | 123.4 | 3.7 | 898 | 0.0000207 |
| multi | llm_decision_router | 1500 | 0.363 | 0.339 | 0.388 | 554.2 | 4.9 | 1691 | 0.0000852 |
| single | llm_only | 1500 | 0.580 | 0.555 | 0.605 | 38.0 | 3.2 | 865 | 0.0000076 |
| single | always_rag | 1500 | 0.568 | 0.543 | 0.593 | 763.2 | 3.5 | 917 | 0.0001151 |
| single | oracle | 1500 | 0.679 | 0.655 | 0.703 | 111.3 | 3.2 | 867 | 0.0000186 |
| single | llm_decision_router | 1500 | 0.575 | 0.550 | 0.601 | 595.6 | 4.4 | 1725 | 0.0000906 |

**pop_tertile.** thirds of log10(s_pop) on the frozen PopQA sample; low is least popular. Not a difficulty ranking.

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| high | llm_only | 167 | 0.647 | 0.575 | 0.719 | 33.3 | 3.0 | 858 | 0.0000068 |
| high | always_rag | 167 | 0.491 | 0.413 | 0.569 | 752.1 | 3.5 | 883 | 0.0001103 |
| high | oracle | 167 | 0.701 | 0.629 | 0.766 | 73.6 | 3.0 | 863 | 0.0000129 |
| high | llm_decision_router | 167 | 0.503 | 0.425 | 0.581 | 643.2 | 4.5 | 1699 | 0.0000945 |
| low | llm_only | 167 | 0.371 | 0.299 | 0.449 | 34.3 | 3.4 | 874 | 0.0000072 |
| low | always_rag | 167 | 0.461 | 0.383 | 0.533 | 777.3 | 3.4 | 901 | 0.0001127 |
| low | oracle | 167 | 0.545 | 0.467 | 0.623 | 167.0 | 3.4 | 866 | 0.0000271 |
| low | llm_decision_router | 167 | 0.461 | 0.383 | 0.533 | 755.6 | 4.4 | 1730 | 0.0001106 |
| mid | llm_only | 166 | 0.392 | 0.319 | 0.464 | 33.8 | 3.2 | 877 | 0.0000070 |
| mid | always_rag | 166 | 0.386 | 0.313 | 0.458 | 759.6 | 3.8 | 887 | 0.0001137 |
| mid | oracle | 166 | 0.512 | 0.440 | 0.584 | 124.0 | 3.3 | 883 | 0.0000206 |
| mid | llm_decision_router | 166 | 0.392 | 0.319 | 0.464 | 706.8 | 4.7 | 1715 | 0.0001064 |

**musique_hops.** hop count from the MuSiQue id; subtypes such as 3hop1 and 4hop2 collapse to 3 and 4

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| 2 | llm_only | 251 | 0.151 | 0.108 | 0.195 | 41.3 | 3.5 | 913 | 0.0000083 |
| 2 | always_rag | 251 | 0.227 | 0.175 | 0.279 | 624.6 | 3.6 | 840 | 0.0000952 |
| 2 | oracle | 251 | 0.299 | 0.243 | 0.355 | 125.7 | 3.5 | 900 | 0.0000208 |
| 2 | llm_decision_router | 251 | 0.215 | 0.167 | 0.267 | 623.7 | 4.6 | 1697 | 0.0000956 |
| 3 | llm_only | 155 | 0.110 | 0.065 | 0.161 | 49.8 | 3.4 | 891 | 0.0000095 |
| 3 | always_rag | 155 | 0.123 | 0.071 | 0.181 | 672.4 | 4.1 | 844 | 0.0001003 |
| 3 | oracle | 155 | 0.181 | 0.123 | 0.245 | 90.9 | 3.4 | 886 | 0.0000157 |
| 3 | llm_decision_router | 155 | 0.123 | 0.071 | 0.181 | 713.9 | 5.1 | 1697 | 0.0001071 |
| 4 | llm_only | 94 | 0.043 | 0.011 | 0.085 | 54.1 | 3.5 | 905 | 0.0000102 |
| 4 | always_rag | 94 | 0.085 | 0.032 | 0.149 | 653.5 | 4.0 | 838 | 0.0000980 |
| 4 | oracle | 94 | 0.085 | 0.032 | 0.149 | 74.8 | 3.5 | 909 | 0.0000133 |
| 4 | llm_decision_router | 94 | 0.085 | 0.032 | 0.149 | 706.6 | 5.0 | 1698 | 0.0001066 |

**hotpot_type.** HotpotQA level is hard for every question in this sample; type is not a difficulty rank

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| bridge | llm_only | 395 | 0.271 | 0.228 | 0.314 | 46.5 | 3.4 | 903 | 0.0000090 |
| bridge | always_rag | 395 | 0.365 | 0.319 | 0.413 | 445.6 | 3.8 | 845 | 0.0000691 |
| bridge | oracle | 395 | 0.456 | 0.408 | 0.506 | 119.1 | 3.5 | 893 | 0.0000200 |
| bridge | llm_decision_router | 395 | 0.352 | 0.306 | 0.400 | 412.7 | 4.8 | 1685 | 0.0000648 |
| comparison | llm_only | 105 | 0.705 | 0.619 | 0.790 | 40.5 | 2.8 | 871 | 0.0000077 |
| comparison | always_rag | 105 | 0.733 | 0.648 | 0.819 | 419.2 | 2.8 | 872 | 0.0000645 |
| comparison | oracle | 105 | 0.752 | 0.667 | 0.829 | 54.5 | 2.8 | 870 | 0.0000098 |
| comparison | llm_decision_router | 105 | 0.705 | 0.619 | 0.790 | 256.9 | 3.9 | 1662 | 0.0000409 |

**wiki_type.** 2Wiki reasoning type, not a difficulty rank

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| bridge_comparison | llm_only | 96 | 0.573 | 0.469 | 0.677 | 46.1 | 4.1 | 942 | 0.0000094 |
| bridge_comparison | always_rag | 96 | 0.677 | 0.583 | 0.771 | 522.0 | 4.5 | 851 | 0.0000810 |
| bridge_comparison | oracle | 96 | 0.802 | 0.719 | 0.875 | 161.5 | 4.4 | 936 | 0.0000268 |
| bridge_comparison | llm_decision_router | 96 | 0.656 | 0.562 | 0.750 | 398.7 | 5.5 | 1729 | 0.0000631 |
| comparison | llm_only | 137 | 0.752 | 0.679 | 0.825 | 42.6 | 4.0 | 902 | 0.0000088 |
| comparison | always_rag | 137 | 0.883 | 0.832 | 0.934 | 558.8 | 4.1 | 833 | 0.0000863 |
| comparison | oracle | 137 | 0.942 | 0.898 | 0.978 | 146.5 | 4.2 | 896 | 0.0000245 |
| comparison | llm_decision_router | 137 | 0.854 | 0.796 | 0.912 | 427.6 | 5.0 | 1726 | 0.0000672 |
| compositional | llm_only | 205 | 0.146 | 0.102 | 0.195 | 40.0 | 2.9 | 916 | 0.0000077 |
| compositional | always_rag | 205 | 0.263 | 0.205 | 0.322 | 761.6 | 3.3 | 829 | 0.0001139 |
| compositional | oracle | 205 | 0.302 | 0.239 | 0.366 | 155.8 | 3.0 | 905 | 0.0000250 |
| compositional | llm_decision_router | 205 | 0.254 | 0.195 | 0.312 | 784.9 | 4.3 | 1667 | 0.0001180 |
| inference | llm_only | 62 | 0.177 | 0.081 | 0.274 | 39.2 | 7.6 | 926 | 0.0000104 |
| inference | always_rag | 62 | 0.258 | 0.161 | 0.371 | 834.5 | 7.0 | 844 | 0.0001294 |
| inference | oracle | 62 | 0.371 | 0.258 | 0.500 | 196.7 | 8.3 | 915 | 0.0000345 |
| inference | llm_decision_router | 62 | 0.290 | 0.177 | 0.403 | 806.5 | 7.6 | 1667 | 0.0001256 |

**Taken into account.** These cuts stay separate. No easy/medium/hard label is assigned: HotpotQA's official level is hard on every question in this sample, NQ and TriviaQA publish none, PopQA's tertiles are popularity, and 2Wiki's type is a reasoning type. Outcome labels are not treated as difficulty.

On the point estimate, the decision router is above Always-RAG only on: hop_type=single +0.007 (n=1500; intervals overlap), pop_tertile=high +0.012 (n=167; intervals overlap), pop_tertile=mid +0.006 (n=166; intervals overlap), wiki_type=inference +0.032 (n=62; intervals overlap). The largest gap elsewhere is wiki_type=comparison -0.029 (n=137; intervals overlap).

Where retrieval itself moves accuracy: PopQA least popular: Always-RAG 0.461 against llm-only 0.371 (n=167); PopQA most popular: Always-RAG 0.491 against llm-only 0.647 (n=167); MuSiQue 4-hop: Always-RAG 0.085 against llm-only 0.043 (n=94).


### gemma4-e2b

**hop_type.** single vs multi; the only cut defined for every question

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| multi | llm_only | 1500 | 0.113 | 0.097 | 0.129 | 51.4 | 2.6 | 315 | 0.0000000 |
| multi | always_rag | 1500 | 0.205 | 0.185 | 0.226 | 610.9 | 2.9 | 2209 | 0.0000000 |
| multi | oracle | 1500 | 0.253 | 0.231 | 0.275 | 120.9 | 2.6 | 549 | 0.0000000 |
| multi | llm_decision_router | 1500 | 0.205 | 0.185 | 0.226 | 658.8 | 3.9 | 2564 | 0.0000000 |
| single | llm_only | 1500 | 0.167 | 0.148 | 0.185 | 44.5 | 2.4 | 208 | 0.0000000 |
| single | always_rag | 1500 | 0.376 | 0.351 | 0.401 | 783.4 | 2.9 | 2854 | 0.0000000 |
| single | oracle | 1500 | 0.429 | 0.403 | 0.454 | 242.0 | 2.6 | 922 | 0.0000000 |
| single | llm_decision_router | 1500 | 0.375 | 0.350 | 0.399 | 817.4 | 4.0 | 3159 | 0.0000000 |

**pop_tertile.** thirds of log10(s_pop) on the frozen PopQA sample; low is least popular. Not a difficulty ranking.

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| high | llm_only | 167 | 0.216 | 0.156 | 0.281 | 40.0 | 2.2 | 185 | 0.0000000 |
| high | always_rag | 167 | 0.377 | 0.299 | 0.449 | 768.6 | 2.6 | 2547 | 0.0000000 |
| high | oracle | 167 | 0.419 | 0.341 | 0.491 | 193.5 | 2.3 | 703 | 0.0000000 |
| high | llm_decision_router | 167 | 0.383 | 0.305 | 0.455 | 781.3 | 3.6 | 2788 | 0.0000000 |
| low | llm_only | 167 | 0.102 | 0.060 | 0.150 | 41.1 | 2.1 | 181 | 0.0000000 |
| low | always_rag | 167 | 0.359 | 0.287 | 0.431 | 798.4 | 2.6 | 2630 | 0.0000000 |
| low | oracle | 167 | 0.389 | 0.317 | 0.461 | 267.5 | 2.3 | 945 | 0.0000000 |
| low | llm_decision_router | 167 | 0.359 | 0.287 | 0.431 | 837.4 | 3.7 | 2964 | 0.0000000 |
| mid | llm_only | 166 | 0.102 | 0.060 | 0.151 | 40.5 | 2.4 | 189 | 0.0000000 |
| mid | always_rag | 166 | 0.301 | 0.235 | 0.373 | 776.0 | 2.9 | 2644 | 0.0000000 |
| mid | oracle | 166 | 0.343 | 0.271 | 0.416 | 226.4 | 2.5 | 832 | 0.0000000 |
| mid | llm_decision_router | 166 | 0.301 | 0.235 | 0.373 | 814.5 | 4.0 | 2975 | 0.0000000 |

**musique_hops.** hop count from the MuSiQue id; subtypes such as 3hop1 and 4hop2 collapse to 3 and 4

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| 2 | llm_only | 251 | 0.040 | 0.016 | 0.068 | 48.2 | 2.3 | 347 | 0.0000000 |
| 2 | always_rag | 251 | 0.068 | 0.040 | 0.100 | 651.6 | 2.8 | 2388 | 0.0000000 |
| 2 | oracle | 251 | 0.100 | 0.064 | 0.139 | 77.4 | 2.4 | 443 | 0.0000000 |
| 2 | llm_decision_router | 251 | 0.068 | 0.040 | 0.100 | 697.8 | 3.9 | 2744 | 0.0000000 |
| 3 | llm_only | 155 | 0.019 | 0.000 | 0.045 | 56.8 | 2.5 | 364 | 0.0000000 |
| 3 | always_rag | 155 | 0.039 | 0.013 | 0.071 | 705.1 | 2.4 | 2505 | 0.0000000 |
| 3 | oracle | 155 | 0.058 | 0.026 | 0.097 | 88.1 | 2.5 | 463 | 0.0000000 |
| 3 | llm_decision_router | 155 | 0.039 | 0.013 | 0.071 | 759.8 | 3.4 | 2880 | 0.0000000 |
| 4 | llm_only | 94 | 0.000 | 0.000 | 0.000 | 61.1 | 2.3 | 381 | 0.0000000 |
| 4 | always_rag | 94 | 0.043 | 0.011 | 0.085 | 686.0 | 2.7 | 2464 | 0.0000000 |
| 4 | oracle | 94 | 0.043 | 0.011 | 0.085 | 94.0 | 2.3 | 496 | 0.0000000 |
| 4 | llm_decision_router | 94 | 0.043 | 0.011 | 0.085 | 745.1 | 3.8 | 2855 | 0.0000000 |

**hotpot_type.** HotpotQA level is hard for every question in this sample; type is not a difficulty rank

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| bridge | llm_only | 395 | 0.051 | 0.030 | 0.073 | 53.6 | 2.7 | 283 | 0.0000000 |
| bridge | always_rag | 395 | 0.200 | 0.162 | 0.241 | 467.4 | 3.0 | 1671 | 0.0000000 |
| bridge | oracle | 395 | 0.220 | 0.180 | 0.261 | 124.0 | 2.7 | 514 | 0.0000000 |
| bridge | llm_decision_router | 395 | 0.200 | 0.162 | 0.241 | 519.1 | 4.0 | 2037 | 0.0000000 |
| comparison | llm_only | 105 | 0.390 | 0.295 | 0.486 | 47.0 | 2.3 | 229 | 0.0000000 |
| comparison | always_rag | 105 | 0.543 | 0.448 | 0.638 | 440.8 | 2.4 | 1536 | 0.0000000 |
| comparison | oracle | 105 | 0.648 | 0.552 | 0.743 | 149.7 | 2.4 | 565 | 0.0000000 |
| comparison | llm_decision_router | 105 | 0.552 | 0.457 | 0.648 | 467.5 | 3.4 | 1821 | 0.0000000 |

**wiki_type.** 2Wiki reasoning type, not a difficulty rank

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| bridge_comparison | llm_only | 96 | 0.333 | 0.240 | 0.427 | 52.9 | 3.5 | 321 | 0.0000000 |
| bridge_comparison | always_rag | 96 | 0.469 | 0.365 | 0.573 | 541.6 | 3.8 | 1999 | 0.0000000 |
| bridge_comparison | oracle | 96 | 0.656 | 0.562 | 0.750 | 198.3 | 3.7 | 814 | 0.0000000 |
| bridge_comparison | llm_decision_router | 96 | 0.469 | 0.365 | 0.573 | 592.5 | 4.8 | 2351 | 0.0000000 |
| comparison | llm_only | 137 | 0.380 | 0.299 | 0.460 | 49.0 | 3.5 | 320 | 0.0000000 |
| comparison | always_rag | 137 | 0.613 | 0.533 | 0.693 | 582.9 | 3.7 | 2151 | 0.0000000 |
| comparison | oracle | 137 | 0.715 | 0.635 | 0.788 | 236.5 | 3.6 | 958 | 0.0000000 |
| comparison | llm_decision_router | 137 | 0.606 | 0.526 | 0.686 | 627.0 | 4.7 | 2489 | 0.0000000 |
| compositional | llm_only | 205 | 0.059 | 0.029 | 0.093 | 47.2 | 1.8 | 299 | 0.0000000 |
| compositional | always_rag | 205 | 0.068 | 0.034 | 0.102 | 790.5 | 2.2 | 2847 | 0.0000000 |
| compositional | oracle | 205 | 0.112 | 0.073 | 0.156 | 91.2 | 1.8 | 459 | 0.0000000 |
| compositional | llm_decision_router | 205 | 0.068 | 0.034 | 0.102 | 835.7 | 3.2 | 3195 | 0.0000000 |
| inference | llm_only | 62 | 0.000 | 0.000 | 0.000 | 46.7 | 3.2 | 352 | 0.0000000 |
| inference | always_rag | 62 | 0.032 | 0.000 | 0.081 | 874.4 | 3.9 | 3275 | 0.0000000 |
| inference | oracle | 62 | 0.032 | 0.000 | 0.081 | 74.7 | 3.3 | 452 | 0.0000000 |
| inference | llm_decision_router | 62 | 0.032 | 0.000 | 0.081 | 919.1 | 4.9 | 3624 | 0.0000000 |

**Taken into account.** These cuts stay separate. No easy/medium/hard label is assigned: HotpotQA's official level is hard on every question in this sample, NQ and TriviaQA publish none, PopQA's tertiles are popularity, and 2Wiki's type is a reasoning type. Outcome labels are not treated as difficulty.

On the point estimate, the decision router is above Always-RAG only on: pop_tertile=high +0.006 (n=167; intervals overlap), hotpot_type=comparison +0.010 (n=105; intervals overlap). The largest gap elsewhere is wiki_type=comparison -0.007 (n=137; intervals overlap).

Where retrieval itself moves accuracy: PopQA least popular: Always-RAG 0.359 against llm-only 0.102 (n=167); PopQA most popular: Always-RAG 0.377 against llm-only 0.216 (n=167); MuSiQue 4-hop: Always-RAG 0.043 against llm-only 0.000 (n=94).


### gpt-5-nano-2025-08-07

**hop_type.** single vs multi; the only cut defined for every question

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| multi | llm_only | 1495 | 0.201 | 0.181 | 0.221 | 46.2 | 25.7 | 1074 | 0.0000126 |
| multi | always_rag | 1495 | 0.301 | 0.278 | 0.325 | 581.4 | 25.9 | 1079 | 0.0000394 |
| multi | oracle | 1495 | 0.363 | 0.338 | 0.387 | 130.9 | 26.0 | 1052 | 0.0000169 |
| multi | llm_decision_router | 1495 | 0.282 | 0.259 | 0.305 | 532.8 | 44.8 | 1981 | 0.0000446 |
| single | llm_only | 1499 | 0.418 | 0.392 | 0.443 | 39.8 | 24.8 | 1024 | 0.0000119 |
| single | always_rag | 1499 | 0.506 | 0.480 | 0.531 | 758.1 | 23.4 | 1120 | 0.0000473 |
| single | oracle | 1499 | 0.592 | 0.568 | 0.617 | 168.2 | 24.8 | 1077 | 0.0000183 |
| single | llm_decision_router | 1499 | 0.502 | 0.477 | 0.527 | 711.7 | 42.6 | 2005 | 0.0000526 |

**pop_tertile.** thirds of log10(s_pop) on the frozen PopQA sample; low is least popular. Not a difficulty ranking.

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| high | llm_only | 167 | 0.443 | 0.365 | 0.521 | 35.2 | 24.8 | 981 | 0.0000117 |
| high | always_rag | 167 | 0.449 | 0.371 | 0.527 | 746.0 | 22.9 | 1496 | 0.0000465 |
| high | oracle | 167 | 0.581 | 0.503 | 0.653 | 136.6 | 24.6 | 1189 | 0.0000167 |
| high | llm_decision_router | 167 | 0.449 | 0.371 | 0.527 | 732.9 | 41.9 | 2325 | 0.0000534 |
| low | llm_only | 167 | 0.210 | 0.150 | 0.275 | 36.2 | 23.7 | 1075 | 0.0000113 |
| low | always_rag | 167 | 0.431 | 0.359 | 0.509 | 772.4 | 22.1 | 1167 | 0.0000475 |
| low | oracle | 167 | 0.467 | 0.389 | 0.545 | 233.0 | 23.8 | 1161 | 0.0000212 |
| low | llm_decision_router | 167 | 0.431 | 0.359 | 0.509 | 803.3 | 41.1 | 2047 | 0.0000566 |
| mid | llm_only | 166 | 0.229 | 0.169 | 0.295 | 35.7 | 23.6 | 1021 | 0.0000112 |
| mid | always_rag | 166 | 0.380 | 0.307 | 0.452 | 753.1 | 23.5 | 1569 | 0.0000470 |
| mid | oracle | 166 | 0.446 | 0.373 | 0.524 | 198.7 | 23.4 | 1269 | 0.0000193 |
| mid | llm_decision_router | 166 | 0.373 | 0.301 | 0.446 | 753.7 | 42.4 | 2438 | 0.0000547 |

**musique_hops.** hop count from the MuSiQue id; subtypes such as 3hop1 and 4hop2 collapse to 3 and 4

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| 2 | llm_only | 250 | 0.096 | 0.060 | 0.136 | 43.1 | 27.9 | 982 | 0.0000133 |
| 2 | always_rag | 250 | 0.164 | 0.120 | 0.212 | 621.4 | 26.2 | 1019 | 0.0000415 |
| 2 | oracle | 250 | 0.224 | 0.172 | 0.276 | 110.2 | 27.5 | 968 | 0.0000165 |
| 2 | llm_decision_router | 250 | 0.160 | 0.116 | 0.208 | 583.3 | 45.6 | 1924 | 0.0000474 |
| 3 | llm_only | 155 | 0.065 | 0.026 | 0.103 | 51.7 | 25.3 | 966 | 0.0000127 |
| 3 | always_rag | 155 | 0.097 | 0.052 | 0.148 | 670.0 | 25.4 | 1110 | 0.0000437 |
| 3 | oracle | 155 | 0.129 | 0.077 | 0.187 | 88.1 | 25.4 | 977 | 0.0000146 |
| 3 | llm_decision_router | 155 | 0.077 | 0.039 | 0.123 | 603.5 | 44.2 | 2035 | 0.0000479 |
| 4 | llm_only | 94 | 0.064 | 0.021 | 0.117 | 55.8 | 22.8 | 937 | 0.0000119 |
| 4 | always_rag | 94 | 0.011 | 0.000 | 0.032 | 650.6 | 30.3 | 1106 | 0.0000446 |
| 4 | oracle | 94 | 0.074 | 0.021 | 0.128 | 61.0 | 22.8 | 937 | 0.0000122 |
| 4 | llm_decision_router | 94 | 0.032 | 0.000 | 0.074 | 570.9 | 49.0 | 2025 | 0.0000481 |

**hotpot_type.** HotpotQA level is hard for every question in this sample; type is not a difficulty rank

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| bridge | llm_only | 391 | 0.136 | 0.102 | 0.169 | 48.3 | 28.1 | 1245 | 0.0000137 |
| bridge | always_rag | 391 | 0.299 | 0.253 | 0.345 | 442.9 | 26.3 | 1034 | 0.0000327 |
| bridge | oracle | 391 | 0.335 | 0.289 | 0.381 | 126.7 | 28.7 | 1174 | 0.0000178 |
| bridge | llm_decision_router | 391 | 0.263 | 0.220 | 0.307 | 396.6 | 45.2 | 1988 | 0.0000379 |
| comparison | llm_only | 105 | 0.667 | 0.571 | 0.752 | 42.4 | 22.6 | 1184 | 0.0000111 |
| comparison | always_rag | 105 | 0.705 | 0.619 | 0.790 | 416.5 | 22.2 | 957 | 0.0000297 |
| comparison | oracle | 105 | 0.771 | 0.686 | 0.848 | 79.6 | 22.4 | 1101 | 0.0000130 |
| comparison | llm_decision_router | 105 | 0.686 | 0.600 | 0.771 | 349.4 | 41.2 | 1840 | 0.0000340 |

**wiki_type.** 2Wiki reasoning type, not a difficulty rank

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| bridge_comparison | llm_only | 96 | 0.490 | 0.385 | 0.594 | 47.8 | 22.5 | 968 | 0.0000114 |
| bridge_comparison | always_rag | 96 | 0.531 | 0.427 | 0.635 | 516.6 | 23.7 | 1095 | 0.0000353 |
| bridge_comparison | oracle | 96 | 0.750 | 0.656 | 0.833 | 186.6 | 23.2 | 990 | 0.0000186 |
| bridge_comparison | llm_decision_router | 96 | 0.500 | 0.396 | 0.604 | 414.5 | 42.5 | 1966 | 0.0000377 |
| comparison | llm_only | 137 | 0.496 | 0.409 | 0.577 | 44.3 | 23.5 | 1020 | 0.0000116 |
| comparison | always_rag | 137 | 0.723 | 0.642 | 0.796 | 553.6 | 24.2 | 1098 | 0.0000374 |
| comparison | oracle | 137 | 0.847 | 0.781 | 0.905 | 229.2 | 23.9 | 1016 | 0.0000210 |
| comparison | llm_decision_router | 137 | 0.672 | 0.591 | 0.752 | 476.8 | 43.1 | 2040 | 0.0000411 |
| compositional | llm_only | 205 | 0.093 | 0.054 | 0.137 | 41.8 | 23.3 | 1032 | 0.0000114 |
| compositional | always_rag | 205 | 0.185 | 0.132 | 0.239 | 755.5 | 24.7 | 1240 | 0.0000477 |
| compositional | oracle | 205 | 0.210 | 0.156 | 0.268 | 139.1 | 23.3 | 1036 | 0.0000163 |
| compositional | llm_decision_router | 205 | 0.180 | 0.127 | 0.234 | 750.3 | 43.7 | 2011 | 0.0000550 |
| inference | llm_only | 62 | 0.065 | 0.016 | 0.129 | 41.0 | 30.5 | 1079 | 0.0000143 |
| inference | always_rag | 62 | 0.226 | 0.129 | 0.339 | 832.2 | 33.5 | 1090 | 0.0000550 |
| inference | oracle | 62 | 0.258 | 0.161 | 0.371 | 210.2 | 32.8 | 1127 | 0.0000236 |
| inference | llm_decision_router | 62 | 0.226 | 0.129 | 0.339 | 852.0 | 52.5 | 1994 | 0.0000636 |

**Taken into account.** These cuts stay separate. No easy/medium/hard label is assigned: HotpotQA's official level is hard on every question in this sample, NQ and TriviaQA publish none, PopQA's tertiles are popularity, and 2Wiki's type is a reasoning type. Outcome labels are not treated as difficulty.

On the point estimate, the decision router is above Always-RAG only on: musique_hops=4 +0.021 (n=94; intervals overlap). The largest gap elsewhere is wiki_type=comparison -0.051 (n=137; intervals overlap).

Where retrieval itself moves accuracy: PopQA least popular: Always-RAG 0.431 against llm-only 0.210 (n=167); PopQA most popular: Always-RAG 0.449 against llm-only 0.443 (n=167); MuSiQue 4-hop: Always-RAG 0.011 against llm-only 0.064 (n=94).


### llama3.2-3b

**hop_type.** single vs multi; the only cut defined for every question

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| multi | llm_only | 1500 | 0.155 | 0.138 | 0.174 | 65.5 | 6.4 | 365 | 0.0000000 |
| multi | always_rag | 1500 | 0.237 | 0.215 | 0.259 | 614.1 | 4.8 | 2477 | 0.0000000 |
| multi | oracle | 1500 | 0.287 | 0.265 | 0.311 | 131.1 | 6.1 | 617 | 0.0000000 |
| multi | llm_decision_router | 1500 | 0.227 | 0.206 | 0.248 | 639.3 | 8.7 | 2589 | 0.0000000 |
| single | llm_only | 1500 | 0.288 | 0.265 | 0.311 | 58.9 | 5.1 | 310 | 0.0000000 |
| single | always_rag | 1500 | 0.437 | 0.411 | 0.461 | 792.0 | 4.5 | 3267 | 0.0000000 |
| single | oracle | 1500 | 0.502 | 0.476 | 0.527 | 218.8 | 5.0 | 962 | 0.0000000 |
| single | llm_decision_router | 1500 | 0.421 | 0.396 | 0.445 | 636.0 | 6.8 | 2584 | 0.0000000 |

**pop_tertile.** thirds of log10(s_pop) on the frozen PopQA sample; low is least popular. Not a difficulty ranking.

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| high | llm_only | 167 | 0.317 | 0.246 | 0.389 | 54.3 | 4.8 | 293 | 0.0000000 |
| high | always_rag | 167 | 0.419 | 0.341 | 0.497 | 780.0 | 4.3 | 3153 | 0.0000000 |
| high | oracle | 167 | 0.467 | 0.389 | 0.545 | 166.3 | 4.6 | 733 | 0.0000000 |
| high | llm_decision_router | 167 | 0.413 | 0.335 | 0.491 | 685.6 | 6.4 | 2743 | 0.0000000 |
| low | llm_only | 167 | 0.108 | 0.060 | 0.156 | 55.4 | 5.5 | 319 | 0.0000000 |
| low | always_rag | 167 | 0.383 | 0.311 | 0.455 | 809.0 | 4.8 | 3285 | 0.0000000 |
| low | oracle | 167 | 0.401 | 0.329 | 0.473 | 285.3 | 5.1 | 1252 | 0.0000000 |
| low | llm_decision_router | 167 | 0.383 | 0.311 | 0.455 | 850.1 | 7.5 | 3439 | 0.0000000 |
| mid | llm_only | 166 | 0.145 | 0.090 | 0.199 | 54.8 | 4.8 | 294 | 0.0000000 |
| mid | always_rag | 166 | 0.331 | 0.259 | 0.404 | 789.2 | 4.3 | 3216 | 0.0000000 |
| mid | oracle | 166 | 0.367 | 0.295 | 0.440 | 225.2 | 4.7 | 990 | 0.0000000 |
| mid | llm_decision_router | 166 | 0.319 | 0.247 | 0.392 | 811.1 | 6.5 | 3272 | 0.0000000 |

**musique_hops.** hop count from the MuSiQue id; subtypes such as 3hop1 and 4hop2 collapse to 3 and 4

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| 2 | llm_only | 251 | 0.048 | 0.024 | 0.076 | 62.4 | 5.8 | 330 | 0.0000000 |
| 2 | always_rag | 251 | 0.084 | 0.052 | 0.120 | 652.7 | 4.9 | 2652 | 0.0000000 |
| 2 | oracle | 251 | 0.120 | 0.080 | 0.159 | 100.3 | 5.6 | 472 | 0.0000000 |
| 2 | llm_decision_router | 251 | 0.088 | 0.056 | 0.124 | 670.3 | 7.8 | 2697 | 0.0000000 |
| 3 | llm_only | 155 | 0.019 | 0.000 | 0.045 | 70.8 | 6.9 | 401 | 0.0000000 |
| 3 | always_rag | 155 | 0.058 | 0.026 | 0.097 | 699.8 | 4.1 | 2777 | 0.0000000 |
| 3 | oracle | 155 | 0.077 | 0.039 | 0.123 | 107.1 | 6.8 | 543 | 0.0000000 |
| 3 | llm_decision_router | 155 | 0.058 | 0.026 | 0.097 | 769.6 | 7.9 | 3059 | 0.0000000 |
| 4 | llm_only | 94 | 0.000 | 0.000 | 0.000 | 75.1 | 7.1 | 444 | 0.0000000 |
| 4 | always_rag | 94 | 0.011 | 0.000 | 0.032 | 681.5 | 4.3 | 2682 | 0.0000000 |
| 4 | oracle | 94 | 0.011 | 0.000 | 0.032 | 79.8 | 7.1 | 461 | 0.0000000 |
| 4 | llm_decision_router | 94 | 0.011 | 0.000 | 0.032 | 755.6 | 7.1 | 2956 | 0.0000000 |

**hotpot_type.** HotpotQA level is hard for every question in this sample; type is not a difficulty rank

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| bridge | llm_only | 395 | 0.086 | 0.058 | 0.114 | 67.5 | 6.1 | 362 | 0.0000000 |
| bridge | always_rag | 395 | 0.225 | 0.185 | 0.266 | 472.4 | 4.8 | 1916 | 0.0000000 |
| bridge | oracle | 395 | 0.263 | 0.220 | 0.306 | 139.5 | 5.4 | 622 | 0.0000000 |
| bridge | llm_decision_router | 395 | 0.192 | 0.154 | 0.230 | 470.5 | 7.2 | 1858 | 0.0000000 |
| comparison | llm_only | 105 | 0.505 | 0.410 | 0.600 | 61.6 | 5.4 | 310 | 0.0000000 |
| comparison | always_rag | 105 | 0.629 | 0.533 | 0.724 | 447.2 | 4.1 | 1757 | 0.0000000 |
| comparison | oracle | 105 | 0.705 | 0.619 | 0.790 | 129.4 | 5.3 | 569 | 0.0000000 |
| comparison | llm_decision_router | 105 | 0.581 | 0.486 | 0.676 | 397.7 | 6.7 | 1537 | 0.0000000 |

**wiki_type.** 2Wiki reasoning type, not a difficulty rank

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| bridge_comparison | llm_only | 96 | 0.583 | 0.490 | 0.677 | 67.0 | 6.1 | 344 | 0.0000000 |
| bridge_comparison | always_rag | 96 | 0.490 | 0.385 | 0.594 | 549.4 | 5.4 | 2245 | 0.0000000 |
| bridge_comparison | oracle | 96 | 0.740 | 0.646 | 0.823 | 147.8 | 6.1 | 667 | 0.0000000 |
| bridge_comparison | llm_decision_router | 96 | 0.521 | 0.417 | 0.615 | 581.6 | 8.4 | 2329 | 0.0000000 |
| comparison | llm_only | 137 | 0.467 | 0.380 | 0.547 | 63.8 | 6.0 | 330 | 0.0000000 |
| comparison | always_rag | 137 | 0.664 | 0.584 | 0.745 | 588.9 | 5.2 | 2408 | 0.0000000 |
| comparison | oracle | 137 | 0.737 | 0.664 | 0.810 | 201.6 | 5.9 | 889 | 0.0000000 |
| comparison | llm_decision_router | 137 | 0.657 | 0.577 | 0.737 | 606.2 | 11.7 | 2584 | 0.0000000 |
| compositional | llm_only | 205 | 0.054 | 0.024 | 0.088 | 61.1 | 6.7 | 359 | 0.0000000 |
| compositional | always_rag | 205 | 0.127 | 0.083 | 0.176 | 796.3 | 4.8 | 3185 | 0.0000000 |
| compositional | oracle | 205 | 0.161 | 0.112 | 0.215 | 145.9 | 6.4 | 694 | 0.0000000 |
| compositional | llm_decision_router | 205 | 0.127 | 0.083 | 0.176 | 856.4 | 13.0 | 3610 | 0.0000000 |
| inference | llm_only | 62 | 0.000 | 0.000 | 0.000 | 60.6 | 10.9 | 532 | 0.0000000 |
| inference | always_rag | 62 | 0.081 | 0.016 | 0.161 | 880.4 | 7.4 | 3674 | 0.0000000 |
| inference | oracle | 62 | 0.081 | 0.016 | 0.161 | 111.5 | 11.0 | 739 | 0.0000000 |
| inference | llm_decision_router | 62 | 0.081 | 0.016 | 0.161 | 940.0 | 10.1 | 3887 | 0.0000000 |

**Taken into account.** These cuts stay separate. No easy/medium/hard label is assigned: HotpotQA's official level is hard on every question in this sample, NQ and TriviaQA publish none, PopQA's tertiles are popularity, and 2Wiki's type is a reasoning type. Outcome labels are not treated as difficulty.

On the point estimate, the decision router is above Always-RAG only on: musique_hops=2 +0.004 (n=251; intervals overlap), wiki_type=bridge_comparison +0.031 (n=96; intervals overlap). The largest gap elsewhere is hotpot_type=comparison -0.048 (n=105; intervals overlap).

Where retrieval itself moves accuracy: PopQA least popular: Always-RAG 0.383 against llm-only 0.108 (n=167); PopQA most popular: Always-RAG 0.419 against llm-only 0.317 (n=167); MuSiQue 4-hop: Always-RAG 0.011 against llm-only 0.000 (n=94).


### qwen3.5-4b

**hop_type.** single vs multi; the only cut defined for every question

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| multi | llm_only | 1500 | 0.153 | 0.135 | 0.171 | 54.6 | 3.8 | 717 | 0.0000000 |
| multi | always_rag | 1500 | 0.283 | 0.261 | 0.306 | 630.7 | 3.7 | 4332 | 0.0000000 |
| multi | oracle | 1500 | 0.325 | 0.302 | 0.349 | 145.6 | 3.9 | 1299 | 0.0000000 |
| multi | llm_decision_router | 1500 | 0.285 | 0.263 | 0.308 | 676.1 | 4.7 | 4771 | 0.0000000 |
| single | llm_only | 1500 | 0.263 | 0.241 | 0.286 | 47.8 | 3.6 | 932 | 0.0000000 |
| single | always_rag | 1500 | 0.469 | 0.443 | 0.493 | 804.8 | 3.7 | 5141 | 0.0000000 |
| single | oracle | 1500 | 0.519 | 0.494 | 0.545 | 245.8 | 3.7 | 2042 | 0.0000000 |
| single | llm_decision_router | 1500 | 0.467 | 0.441 | 0.492 | 802.3 | 4.7 | 5421 | 0.0000000 |

**pop_tertile.** thirds of log10(s_pop) on the frozen PopQA sample; low is least popular. Not a difficulty ranking.

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| high | llm_only | 167 | 0.293 | 0.228 | 0.359 | 43.3 | 3.4 | 763 | 0.0000000 |
| high | always_rag | 167 | 0.443 | 0.365 | 0.521 | 790.5 | 3.8 | 4955 | 0.0000000 |
| high | oracle | 167 | 0.479 | 0.401 | 0.557 | 187.0 | 3.5 | 1596 | 0.0000000 |
| high | llm_decision_router | 167 | 0.443 | 0.365 | 0.521 | 817.8 | 4.7 | 5406 | 0.0000000 |
| low | llm_only | 167 | 0.180 | 0.126 | 0.240 | 44.3 | 3.2 | 766 | 0.0000000 |
| low | always_rag | 167 | 0.413 | 0.335 | 0.491 | 822.1 | 3.4 | 5106 | 0.0000000 |
| low | oracle | 167 | 0.473 | 0.395 | 0.551 | 280.9 | 3.2 | 2145 | 0.0000000 |
| low | llm_decision_router | 167 | 0.413 | 0.335 | 0.491 | 864.4 | 4.4 | 5649 | 0.0000000 |
| mid | llm_only | 166 | 0.151 | 0.096 | 0.205 | 43.7 | 3.5 | 778 | 0.0000000 |
| mid | always_rag | 166 | 0.373 | 0.301 | 0.446 | 797.3 | 3.4 | 5059 | 0.0000000 |
| mid | oracle | 166 | 0.404 | 0.325 | 0.482 | 244.9 | 3.5 | 1942 | 0.0000000 |
| mid | llm_decision_router | 166 | 0.373 | 0.301 | 0.446 | 825.0 | 4.4 | 5512 | 0.0000000 |

**musique_hops.** hop count from the MuSiQue id; subtypes such as 3hop1 and 4hop2 collapse to 3 and 4

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| 2 | llm_only | 251 | 0.040 | 0.016 | 0.064 | 51.4 | 3.9 | 650 | 0.0000000 |
| 2 | always_rag | 251 | 0.120 | 0.080 | 0.163 | 670.7 | 3.4 | 4456 | 0.0000000 |
| 2 | oracle | 251 | 0.139 | 0.100 | 0.183 | 104.1 | 4.0 | 989 | 0.0000000 |
| 2 | llm_decision_router | 251 | 0.120 | 0.080 | 0.163 | 716.3 | 4.4 | 4905 | 0.0000000 |
| 3 | llm_only | 155 | 0.013 | 0.000 | 0.032 | 59.9 | 3.5 | 689 | 0.0000000 |
| 3 | always_rag | 155 | 0.103 | 0.058 | 0.155 | 723.0 | 3.6 | 4723 | 0.0000000 |
| 3 | oracle | 155 | 0.110 | 0.065 | 0.161 | 125.4 | 3.6 | 1080 | 0.0000000 |
| 3 | llm_decision_router | 155 | 0.103 | 0.058 | 0.155 | 781.0 | 4.6 | 5245 | 0.0000000 |
| 4 | llm_only | 94 | 0.011 | 0.000 | 0.032 | 64.2 | 3.7 | 753 | 0.0000000 |
| 4 | always_rag | 94 | 0.053 | 0.011 | 0.106 | 706.1 | 3.7 | 4734 | 0.0000000 |
| 4 | oracle | 94 | 0.053 | 0.011 | 0.106 | 92.4 | 3.7 | 919 | 0.0000000 |
| 4 | llm_decision_router | 94 | 0.053 | 0.011 | 0.106 | 768.3 | 4.7 | 5296 | 0.0000000 |

**hotpot_type.** HotpotQA level is hard for every question in this sample; type is not a difficulty rank

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| bridge | llm_only | 395 | 0.073 | 0.048 | 0.101 | 57.0 | 3.8 | 772 | 0.0000000 |
| bridge | always_rag | 395 | 0.271 | 0.228 | 0.316 | 483.5 | 3.6 | 3358 | 0.0000000 |
| bridge | oracle | 395 | 0.299 | 0.253 | 0.344 | 156.8 | 3.9 | 1391 | 0.0000000 |
| bridge | llm_decision_router | 395 | 0.271 | 0.228 | 0.316 | 537.1 | 4.6 | 3841 | 0.0000000 |
| comparison | llm_only | 105 | 0.505 | 0.410 | 0.600 | 50.4 | 3.8 | 704 | 0.0000000 |
| comparison | always_rag | 105 | 0.657 | 0.562 | 0.743 | 456.9 | 3.0 | 3154 | 0.0000000 |
| comparison | oracle | 105 | 0.714 | 0.629 | 0.800 | 132.7 | 3.6 | 1203 | 0.0000000 |
| comparison | llm_decision_router | 105 | 0.667 | 0.571 | 0.752 | 450.4 | 4.3 | 3278 | 0.0000000 |

**wiki_type.** 2Wiki reasoning type, not a difficulty rank

| value | system | n | Acc | CI lo | CI hi | in tok | out tok | resp ms | $/q |
|---|---|---|---|---|---|---|---|---|---|
| bridge_comparison | llm_only | 96 | 0.448 | 0.344 | 0.542 | 56.1 | 4.0 | 752 | 0.0000000 |
| bridge_comparison | always_rag | 96 | 0.552 | 0.448 | 0.646 | 561.6 | 4.2 | 4119 | 0.0000000 |
| bridge_comparison | oracle | 96 | 0.719 | 0.625 | 0.812 | 177.4 | 4.2 | 1494 | 0.0000000 |
| bridge_comparison | llm_decision_router | 96 | 0.552 | 0.448 | 0.646 | 615.8 | 5.2 | 4601 | 0.0000000 |
| comparison | llm_only | 137 | 0.504 | 0.423 | 0.591 | 52.5 | 4.2 | 734 | 0.0000000 |
| comparison | always_rag | 137 | 0.759 | 0.686 | 0.832 | 605.1 | 4.2 | 4412 | 0.0000000 |
| comparison | oracle | 137 | 0.861 | 0.803 | 0.920 | 238.7 | 4.4 | 1984 | 0.0000000 |
| comparison | llm_decision_router | 137 | 0.774 | 0.701 | 0.839 | 629.2 | 5.3 | 4698 | 0.0000000 |
| compositional | llm_only | 205 | 0.102 | 0.063 | 0.146 | 50.2 | 3.0 | 662 | 0.0000000 |
| compositional | always_rag | 205 | 0.176 | 0.127 | 0.229 | 815.2 | 2.9 | 5570 | 0.0000000 |
| compositional | oracle | 205 | 0.215 | 0.161 | 0.273 | 151.3 | 3.2 | 1327 | 0.0000000 |
| compositional | llm_decision_router | 205 | 0.176 | 0.127 | 0.229 | 863.4 | 3.9 | 6032 | 0.0000000 |
| inference | llm_only | 62 | 0.032 | 0.000 | 0.081 | 49.4 | 5.2 | 771 | 0.0000000 |
| inference | always_rag | 62 | 0.065 | 0.016 | 0.129 | 910.3 | 6.8 | 6505 | 0.0000000 |
| inference | oracle | 62 | 0.097 | 0.032 | 0.177 | 122.8 | 5.1 | 1348 | 0.0000000 |
| inference | llm_decision_router | 62 | 0.065 | 0.016 | 0.129 | 957.7 | 7.8 | 6950 | 0.0000000 |

**Taken into account.** These cuts stay separate. No easy/medium/hard label is assigned: HotpotQA's official level is hard on every question in this sample, NQ and TriviaQA publish none, PopQA's tertiles are popularity, and 2Wiki's type is a reasoning type. Outcome labels are not treated as difficulty.

On the point estimate, the decision router is above Always-RAG only on: hop_type=multi +0.002 (n=1500; intervals overlap), hotpot_type=comparison +0.010 (n=105; intervals overlap), wiki_type=comparison +0.015 (n=137; intervals overlap). The largest gap elsewhere is hop_type=single -0.002 (n=1500; intervals overlap).

Where retrieval itself moves accuracy: PopQA least popular: Always-RAG 0.413 against llm-only 0.180 (n=167); PopQA most popular: Always-RAG 0.443 against llm-only 0.293 (n=167); MuSiQue 4-hop: Always-RAG 0.053 against llm-only 0.011 (n=94).

### Paired model difference (A − B)

Same questions, same route. A positive accuracy difference means A is higher.

| stratum | value | system | n | acc A-B | CI lo | CI hi | in A | in B | out A | out B | ms A | ms B | $/q A-B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hop_type | multi | llm_only | 1495 | -0.040 | -0.064 | -0.017 | 46.2 | 67.7 | 25.7 | 34.4 | 1074 | 954 | -0.0000114 |
| hop_type | multi | always_rag | 1495 | -0.056 | -0.076 | -0.035 | 581.4 | 945.7 | 25.9 | 21.8 | 1079 | 946 | -0.0000660 |
| hop_type | multi | oracle | 1495 | -0.062 | -0.084 | -0.039 | 130.9 | 222.0 | 26.0 | 32.2 | 1052 | 949 | -0.0000214 |
| hop_type | multi | llm_decision_router | 1495 | -0.068 | -0.090 | -0.046 | 532.8 | 927.7 | 44.8 | 61.3 | 1981 | 1899 | -0.0000788 |
| hop_type | single | llm_only | 1499 | -0.115 | -0.138 | -0.092 | 39.8 | 56.8 | 24.8 | 16.7 | 1024 | 913 | -0.0000021 |
| hop_type | single | always_rag | 1499 | -0.054 | -0.073 | -0.036 | 758.1 | 1216.7 | 23.4 | 12.3 | 1120 | 1045 | -0.0000805 |
| hop_type | single | oracle | 1499 | -0.070 | -0.090 | -0.051 | 168.2 | 211.5 | 24.8 | 15.6 | 1077 | 920 | -0.0000106 |
| hop_type | single | llm_decision_router | 1499 | -0.065 | -0.086 | -0.046 | 711.7 | 1119.4 | 42.6 | 46.1 | 2005 | 1960 | -0.0000823 |
| pop_tertile | high | llm_only | 167 | -0.168 | -0.246 | -0.096 | 35.2 | 51.0 | 24.8 | 19.3 | 981 | 892 | -0.0000031 |
| pop_tertile | high | always_rag | 167 | -0.060 | -0.108 | -0.012 | 746.0 | 1206.9 | 22.9 | 10.8 | 1496 | 869 | -0.0000796 |
| pop_tertile | high | oracle | 167 | -0.096 | -0.156 | -0.036 | 136.6 | 128.4 | 24.6 | 18.5 | 1189 | 888 | -0.0000054 |
| pop_tertile | high | llm_decision_router | 167 | -0.084 | -0.132 | -0.036 | 732.9 | 1102.9 | 41.9 | 45.4 | 2325 | 1817 | -0.0000796 |
| pop_tertile | low | llm_only | 167 | -0.006 | -0.066 | 0.054 | 36.2 | 52.1 | 23.7 | 24.5 | 1075 | 916 | -0.0000062 |
| pop_tertile | low | always_rag | 167 | 0.012 | -0.030 | 0.054 | 772.4 | 1230.1 | 22.1 | 13.7 | 1167 | 876 | -0.0000824 |
| pop_tertile | low | oracle | 167 | -0.018 | -0.060 | 0.024 | 233.0 | 381.5 | 23.8 | 21.9 | 1161 | 908 | -0.0000279 |
| pop_tertile | low | llm_decision_router | 167 | 0.018 | -0.018 | 0.060 | 803.3 | 1258.6 | 41.1 | 64.1 | 2047 | 1892 | -0.0001013 |
| pop_tertile | mid | llm_only | 166 | -0.066 | -0.133 | 0.000 | 35.7 | 51.7 | 23.6 | 21.8 | 1021 | 912 | -0.0000049 |
| pop_tertile | mid | always_rag | 166 | -0.006 | -0.042 | 0.030 | 753.1 | 1208.4 | 23.5 | 13.6 | 1569 | 865 | -0.0000806 |
| pop_tertile | mid | oracle | 166 | -0.048 | -0.102 | 0.006 | 198.7 | 289.0 | 23.4 | 20.0 | 1269 | 901 | -0.0000196 |
| pop_tertile | mid | llm_decision_router | 166 | -0.024 | -0.060 | 0.012 | 753.7 | 1205.0 | 42.4 | 59.9 | 2438 | 1855 | -0.0000958 |
| musique_hops | 2.0 | llm_only | 250 | -0.080 | -0.128 | -0.032 | 43.1 | 62.2 | 27.9 | 36.7 | 982 | 964 | -0.0000112 |
| musique_hops | 2.0 | always_rag | 250 | -0.076 | -0.128 | -0.024 | 621.4 | 1016.0 | 26.2 | 22.8 | 1019 | 941 | -0.0000715 |
| musique_hops | 2.0 | oracle | 250 | -0.116 | -0.176 | -0.056 | 110.2 | 206.0 | 27.5 | 35.2 | 968 | 964 | -0.0000217 |
| musique_hops | 2.0 | llm_decision_router | 250 | -0.076 | -0.132 | -0.024 | 583.3 | 998.6 | 45.6 | 65.3 | 1924 | 1900 | -0.0000851 |
| musique_hops | 3.0 | llm_only | 155 | -0.077 | -0.129 | -0.032 | 51.7 | 73.7 | 25.3 | 62.5 | 966 | 1057 | -0.0000259 |
| musique_hops | 3.0 | always_rag | 155 | -0.077 | -0.129 | -0.026 | 670.0 | 1077.9 | 25.4 | 36.3 | 1110 | 1024 | -0.0000823 |
| musique_hops | 3.0 | oracle | 155 | -0.097 | -0.161 | -0.039 | 88.1 | 148.8 | 25.4 | 58.4 | 977 | 1049 | -0.0000295 |
| musique_hops | 3.0 | llm_decision_router | 155 | -0.097 | -0.155 | -0.045 | 603.5 | 1086.8 | 44.2 | 88.1 | 2035 | 2011 | -0.0001048 |
| musique_hops | 4.0 | llm_only | 94 | -0.032 | -0.117 | 0.053 | 55.8 | 79.5 | 22.8 | 89.3 | 937 | 1199 | -0.0000407 |
| musique_hops | 4.0 | always_rag | 94 | -0.106 | -0.170 | -0.053 | 650.6 | 1046.3 | 30.3 | 53.8 | 1106 | 1037 | -0.0000869 |
| musique_hops | 4.0 | oracle | 94 | -0.096 | -0.191 | 0.000 | 61.0 | 157.2 | 22.8 | 86.8 | 937 | 1186 | -0.0000469 |
| musique_hops | 4.0 | llm_decision_router | 94 | -0.085 | -0.160 | -0.021 | 570.9 | 1114.7 | 49.0 | 118.8 | 2025 | 2105 | -0.0001227 |
| hotpot_type | bridge | llm_only | 391 | -0.097 | -0.138 | -0.059 | 48.3 | 70.8 | 28.1 | 29.1 | 1245 | 940 | -0.0000080 |
| hotpot_type | bridge | always_rag | 391 | -0.049 | -0.090 | -0.008 | 442.9 | 729.2 | 26.3 | 15.7 | 1034 | 918 | -0.0000481 |
| hotpot_type | bridge | oracle | 391 | -0.079 | -0.120 | -0.038 | 126.7 | 189.8 | 28.7 | 25.9 | 1174 | 932 | -0.0000141 |
| hotpot_type | bridge | llm_decision_router | 391 | -0.069 | -0.113 | -0.028 | 396.6 | 687.4 | 45.2 | 46.9 | 1988 | 1836 | -0.0000543 |
| hotpot_type | comparison | llm_only | 105 | -0.019 | -0.105 | 0.067 | 42.4 | 64.3 | 22.6 | 11.7 | 1184 | 836 | -0.0000011 |
| hotpot_type | comparison | always_rag | 105 | 0.029 | -0.029 | 0.086 | 416.5 | 685.2 | 22.2 | 10.6 | 957 | 925 | -0.0000441 |
| hotpot_type | comparison | oracle | 105 | 0.000 | -0.048 | 0.048 | 79.6 | 119.8 | 22.4 | 11.4 | 1101 | 841 | -0.0000048 |
| hotpot_type | comparison | llm_decision_router | 105 | 0.000 | -0.048 | 0.057 | 349.4 | 561.2 | 41.2 | 42.7 | 1840 | 1837 | -0.0000435 |
| wiki_type | bridge_comparison | llm_only | 96 | 0.219 | 0.083 | 0.354 | 47.8 | 70.2 | 22.5 | 23.5 | 968 | 898 | -0.0000074 |
| wiki_type | bridge_comparison | always_rag | 96 | 0.000 | -0.135 | 0.125 | 516.6 | 852.2 | 23.7 | 20.7 | 1095 | 916 | -0.0000603 |
| wiki_type | bridge_comparison | oracle | 96 | 0.167 | 0.031 | 0.302 | 186.6 | 310.6 | 23.2 | 22.5 | 990 | 900 | -0.0000237 |
| wiki_type | bridge_comparison | llm_decision_router | 96 | -0.021 | -0.156 | 0.115 | 414.5 | 828.6 | 42.5 | 78.3 | 1966 | 1948 | -0.0000843 |
| wiki_type | comparison | llm_only | 137 | 0.015 | -0.109 | 0.139 | 44.3 | 66.9 | 23.5 | 17.2 | 1020 | 884 | -0.0000037 |
| wiki_type | comparison | always_rag | 137 | -0.139 | -0.212 | -0.066 | 553.6 | 903.6 | 24.2 | 11.2 | 1098 | 872 | -0.0000586 |
| wiki_type | comparison | oracle | 137 | -0.080 | -0.153 | -0.007 | 229.2 | 433.2 | 23.9 | 14.7 | 1016 | 877 | -0.0000296 |
| wiki_type | comparison | llm_decision_router | 137 | -0.175 | -0.263 | -0.095 | 476.8 | 868.2 | 43.1 | 56.6 | 2040 | 1834 | -0.0000740 |
| wiki_type | compositional | llm_only | 205 | -0.029 | -0.078 | 0.020 | 41.8 | 60.7 | 23.3 | 25.6 | 1032 | 925 | -0.0000074 |
| wiki_type | compositional | always_rag | 205 | -0.029 | -0.088 | 0.029 | 755.5 | 1212.1 | 24.7 | 17.3 | 1240 | 971 | -0.0000822 |
| wiki_type | compositional | oracle | 205 | -0.059 | -0.122 | 0.005 | 139.1 | 241.5 | 23.3 | 24.2 | 1036 | 911 | -0.0000200 |
| wiki_type | compositional | llm_decision_router | 205 | -0.029 | -0.083 | 0.024 | 750.3 | 1227.4 | 43.7 | 39.1 | 2011 | 1872 | -0.0000873 |
| wiki_type | inference | llm_only | 62 | -0.032 | -0.129 | 0.048 | 41.0 | 65.4 | 30.5 | 28.4 | 1079 | 917 | -0.0000065 |
| wiki_type | inference | always_rag | 62 | -0.016 | -0.113 | 0.097 | 832.2 | 1343.0 | 33.5 | 30.1 | 1090 | 966 | -0.0000944 |
| wiki_type | inference | oracle | 62 | -0.016 | -0.145 | 0.113 | 210.2 | 276.3 | 32.8 | 27.8 | 1127 | 931 | -0.0000179 |
| wiki_type | inference | llm_decision_router | 62 | -0.016 | -0.113 | 0.097 | 852.0 | 1391.5 | 52.5 | 70.6 | 1994 | 1952 | -0.0001108 |
| hop_type | multi | llm_only | 1495 | -0.092 | -0.114 | -0.071 | 46.2 | 44.5 | 25.7 | 3.6 | 1074 | 907 | 0.0000038 |
| hop_type | multi | always_rag | 1495 | -0.074 | -0.094 | -0.052 | 581.4 | 585.0 | 25.9 | 3.9 | 1079 | 843 | -0.0000498 |
| hop_type | multi | oracle | 1495 | -0.079 | -0.101 | -0.057 | 130.9 | 123.5 | 26.0 | 3.7 | 1052 | 899 | -0.0000038 |
| hop_type | multi | llm_decision_router | 1495 | -0.082 | -0.104 | -0.060 | 532.8 | 554.3 | 44.8 | 4.9 | 1981 | 1691 | -0.0000406 |
| hop_type | single | llm_only | 1499 | -0.162 | -0.185 | -0.139 | 39.8 | 38.0 | 24.8 | 3.2 | 1024 | 865 | 0.0000043 |
| hop_type | single | always_rag | 1499 | -0.063 | -0.082 | -0.044 | 758.1 | 763.2 | 23.4 | 3.5 | 1120 | 917 | -0.0000678 |
| hop_type | single | oracle | 1499 | -0.087 | -0.107 | -0.067 | 168.2 | 111.3 | 24.8 | 3.2 | 1077 | 867 | -0.0000003 |
| hop_type | single | llm_decision_router | 1499 | -0.073 | -0.093 | -0.053 | 711.7 | 595.9 | 42.6 | 4.4 | 2005 | 1725 | -0.0000380 |
| pop_tertile | high | llm_only | 167 | -0.204 | -0.275 | -0.132 | 35.2 | 33.3 | 24.8 | 3.0 | 981 | 858 | 0.0000049 |
| pop_tertile | high | always_rag | 167 | -0.042 | -0.090 | 0.006 | 746.0 | 752.1 | 22.9 | 3.5 | 1496 | 883 | -0.0000638 |
| pop_tertile | high | oracle | 167 | -0.120 | -0.186 | -0.054 | 136.6 | 73.6 | 24.6 | 3.0 | 1189 | 863 | 0.0000038 |
| pop_tertile | high | llm_decision_router | 167 | -0.054 | -0.108 | 0.000 | 732.9 | 643.2 | 41.9 | 4.5 | 2325 | 1699 | -0.0000411 |
| pop_tertile | low | llm_only | 167 | -0.162 | -0.234 | -0.090 | 36.2 | 34.3 | 23.7 | 3.4 | 1075 | 874 | 0.0000041 |
| pop_tertile | low | always_rag | 167 | -0.030 | -0.072 | 0.006 | 772.4 | 777.3 | 22.1 | 3.4 | 1167 | 901 | -0.0000652 |
| pop_tertile | low | oracle | 167 | -0.078 | -0.132 | -0.024 | 233.0 | 167.0 | 23.8 | 3.4 | 1161 | 866 | -0.0000059 |
| pop_tertile | low | llm_decision_router | 167 | -0.030 | -0.072 | 0.006 | 803.3 | 755.6 | 41.1 | 4.4 | 2047 | 1730 | -0.0000540 |
| pop_tertile | mid | llm_only | 166 | -0.163 | -0.229 | -0.096 | 35.7 | 33.8 | 23.6 | 3.2 | 1021 | 877 | 0.0000043 |
| pop_tertile | mid | always_rag | 166 | -0.006 | -0.030 | 0.018 | 753.1 | 759.6 | 23.5 | 3.8 | 1569 | 887 | -0.0000667 |
| pop_tertile | mid | oracle | 166 | -0.066 | -0.114 | -0.018 | 198.7 | 124.0 | 23.4 | 3.3 | 1269 | 883 | -0.0000013 |
| pop_tertile | mid | llm_decision_router | 166 | -0.018 | -0.054 | 0.018 | 753.7 | 706.8 | 42.4 | 4.7 | 2438 | 1715 | -0.0000517 |
| musique_hops | 2.0 | llm_only | 250 | -0.056 | -0.104 | -0.012 | 43.1 | 41.3 | 27.9 | 3.5 | 982 | 914 | 0.0000050 |
| musique_hops | 2.0 | always_rag | 250 | -0.064 | -0.116 | -0.012 | 621.4 | 624.2 | 26.2 | 3.6 | 1019 | 840 | -0.0000536 |
| musique_hops | 2.0 | oracle | 250 | -0.076 | -0.132 | -0.020 | 110.2 | 125.9 | 27.5 | 3.5 | 968 | 900 | -0.0000044 |
| musique_hops | 2.0 | llm_decision_router | 250 | -0.056 | -0.108 | -0.004 | 583.3 | 623.1 | 45.6 | 4.6 | 1924 | 1697 | -0.0000482 |
| musique_hops | 3.0 | llm_only | 155 | -0.045 | -0.097 | 0.000 | 51.7 | 49.8 | 25.3 | 3.4 | 966 | 891 | 0.0000032 |
| musique_hops | 3.0 | always_rag | 155 | -0.026 | -0.071 | 0.019 | 670.0 | 672.4 | 25.4 | 4.1 | 1110 | 844 | -0.0000566 |
| musique_hops | 3.0 | oracle | 155 | -0.052 | -0.103 | 0.000 | 88.1 | 90.9 | 25.4 | 3.4 | 977 | 886 | -0.0000011 |
| musique_hops | 3.0 | llm_decision_router | 155 | -0.045 | -0.097 | 0.006 | 603.5 | 713.9 | 44.2 | 5.1 | 2035 | 1697 | -0.0000592 |
| musique_hops | 4.0 | llm_only | 94 | 0.021 | -0.043 | 0.085 | 55.8 | 54.1 | 22.8 | 3.5 | 937 | 905 | 0.0000017 |
| musique_hops | 4.0 | always_rag | 94 | -0.074 | -0.128 | -0.021 | 650.6 | 653.5 | 30.3 | 4.0 | 1106 | 838 | -0.0000534 |
| musique_hops | 4.0 | oracle | 94 | -0.011 | -0.085 | 0.064 | 61.0 | 74.8 | 22.8 | 3.5 | 937 | 909 | -0.0000012 |
| musique_hops | 4.0 | llm_decision_router | 94 | -0.053 | -0.117 | 0.011 | 570.9 | 706.6 | 49.0 | 5.0 | 2025 | 1698 | -0.0000585 |
| hotpot_type | bridge | llm_only | 391 | -0.138 | -0.176 | -0.100 | 48.3 | 46.5 | 28.1 | 3.4 | 1245 | 904 | 0.0000046 |
| hotpot_type | bridge | always_rag | 391 | -0.066 | -0.107 | -0.028 | 442.9 | 445.9 | 26.3 | 3.8 | 1034 | 845 | -0.0000365 |
| hotpot_type | bridge | oracle | 391 | -0.123 | -0.164 | -0.082 | 126.7 | 119.2 | 28.7 | 3.5 | 1174 | 894 | -0.0000022 |
| hotpot_type | bridge | llm_decision_router | 391 | -0.090 | -0.133 | -0.046 | 396.6 | 412.2 | 45.2 | 4.8 | 1988 | 1685 | -0.0000268 |
| hotpot_type | comparison | llm_only | 105 | -0.038 | -0.124 | 0.048 | 42.4 | 40.5 | 22.6 | 2.8 | 1184 | 871 | 0.0000034 |
| hotpot_type | comparison | always_rag | 105 | -0.029 | -0.086 | 0.029 | 416.5 | 419.2 | 22.2 | 2.8 | 957 | 872 | -0.0000348 |
| hotpot_type | comparison | oracle | 105 | 0.019 | -0.038 | 0.076 | 79.6 | 54.5 | 22.4 | 2.8 | 1101 | 870 | 0.0000031 |
| hotpot_type | comparison | llm_decision_router | 105 | -0.019 | -0.076 | 0.038 | 349.4 | 256.9 | 41.2 | 3.9 | 1840 | 1662 | -0.0000069 |
| wiki_type | bridge_comparison | llm_only | 96 | -0.083 | -0.208 | 0.042 | 47.8 | 46.1 | 22.5 | 4.1 | 968 | 942 | 0.0000020 |
| wiki_type | bridge_comparison | always_rag | 96 | -0.146 | -0.271 | -0.031 | 516.6 | 522.0 | 23.7 | 4.5 | 1095 | 851 | -0.0000457 |
| wiki_type | bridge_comparison | oracle | 96 | -0.052 | -0.156 | 0.052 | 186.6 | 161.5 | 23.2 | 4.4 | 990 | 936 | -0.0000082 |
| wiki_type | bridge_comparison | llm_decision_router | 96 | -0.156 | -0.281 | -0.031 | 414.5 | 398.7 | 42.5 | 5.5 | 1966 | 1729 | -0.0000254 |
| wiki_type | comparison | llm_only | 137 | -0.255 | -0.358 | -0.153 | 44.3 | 42.6 | 23.5 | 4.0 | 1020 | 902 | 0.0000028 |
| wiki_type | comparison | always_rag | 137 | -0.161 | -0.248 | -0.073 | 553.6 | 558.8 | 24.2 | 4.1 | 1098 | 833 | -0.0000490 |
| wiki_type | comparison | oracle | 137 | -0.095 | -0.168 | -0.022 | 229.2 | 146.5 | 23.9 | 4.2 | 1016 | 896 | -0.0000035 |
| wiki_type | comparison | llm_decision_router | 137 | -0.182 | -0.270 | -0.095 | 476.8 | 427.6 | 43.1 | 5.0 | 2040 | 1726 | -0.0000261 |
| wiki_type | compositional | llm_only | 205 | -0.054 | -0.098 | -0.010 | 41.8 | 40.0 | 23.3 | 2.9 | 1032 | 916 | 0.0000037 |
| wiki_type | compositional | always_rag | 205 | -0.078 | -0.137 | -0.020 | 755.5 | 761.6 | 24.7 | 3.3 | 1240 | 829 | -0.0000663 |
| wiki_type | compositional | oracle | 205 | -0.093 | -0.156 | -0.029 | 139.1 | 155.8 | 23.3 | 3.0 | 1036 | 905 | -0.0000087 |
| wiki_type | compositional | llm_decision_router | 205 | -0.073 | -0.132 | -0.015 | 750.3 | 784.9 | 43.7 | 4.3 | 2011 | 1667 | -0.0000630 |
| wiki_type | inference | llm_only | 62 | -0.113 | -0.226 | -0.016 | 41.0 | 39.2 | 30.5 | 7.6 | 1079 | 926 | 0.0000038 |
| wiki_type | inference | always_rag | 62 | -0.032 | -0.145 | 0.081 | 832.2 | 834.5 | 33.5 | 7.0 | 1090 | 844 | -0.0000744 |
| wiki_type | inference | oracle | 62 | -0.113 | -0.242 | 0.016 | 210.2 | 196.7 | 32.8 | 8.3 | 1127 | 915 | -0.0000109 |
| wiki_type | inference | llm_decision_router | 62 | -0.065 | -0.177 | 0.048 | 852.0 | 806.5 | 52.5 | 7.6 | 1994 | 1667 | -0.0000619 |
| hop_type | multi | llm_only | 1495 | 0.088 | 0.068 | 0.110 | 46.2 | 51.4 | 25.7 | 2.6 | 1074 | 316 | 0.0000126 |
| hop_type | multi | always_rag | 1495 | 0.095 | 0.075 | 0.116 | 581.4 | 611.3 | 25.9 | 2.9 | 1079 | 2211 | 0.0000394 |
| hop_type | multi | oracle | 1495 | 0.110 | 0.088 | 0.132 | 130.9 | 121.2 | 26.0 | 2.6 | 1052 | 550 | 0.0000169 |
| hop_type | multi | llm_decision_router | 1495 | 0.076 | 0.055 | 0.097 | 532.8 | 659.1 | 44.8 | 3.9 | 1981 | 2565 | 0.0000446 |
| hop_type | single | llm_only | 1499 | 0.251 | 0.227 | 0.275 | 39.8 | 44.5 | 24.8 | 2.4 | 1024 | 208 | 0.0000119 |
| hop_type | single | always_rag | 1499 | 0.129 | 0.109 | 0.150 | 758.1 | 783.4 | 23.4 | 2.9 | 1120 | 2854 | 0.0000473 |
| hop_type | single | oracle | 1499 | 0.163 | 0.141 | 0.185 | 168.2 | 242.1 | 24.8 | 2.6 | 1077 | 922 | 0.0000183 |
| hop_type | single | llm_decision_router | 1499 | 0.127 | 0.107 | 0.149 | 711.7 | 817.4 | 42.6 | 4.0 | 2005 | 3159 | 0.0000526 |
| pop_tertile | high | llm_only | 167 | 0.228 | 0.168 | 0.293 | 35.2 | 40.0 | 24.8 | 2.2 | 981 | 185 | 0.0000117 |
| pop_tertile | high | always_rag | 167 | 0.072 | 0.024 | 0.120 | 746.0 | 768.6 | 22.9 | 2.6 | 1496 | 2547 | 0.0000465 |
| pop_tertile | high | oracle | 167 | 0.162 | 0.102 | 0.222 | 136.6 | 193.5 | 24.6 | 2.3 | 1189 | 703 | 0.0000167 |
| pop_tertile | high | llm_decision_router | 167 | 0.066 | 0.018 | 0.120 | 732.9 | 781.3 | 41.9 | 3.6 | 2325 | 2788 | 0.0000534 |
| pop_tertile | low | llm_only | 167 | 0.108 | 0.054 | 0.168 | 36.2 | 41.1 | 23.7 | 2.1 | 1075 | 181 | 0.0000113 |
| pop_tertile | low | always_rag | 167 | 0.072 | 0.024 | 0.120 | 772.4 | 798.4 | 22.1 | 2.6 | 1167 | 2630 | 0.0000475 |
| pop_tertile | low | oracle | 167 | 0.078 | 0.030 | 0.132 | 233.0 | 267.5 | 23.8 | 2.3 | 1161 | 945 | 0.0000212 |
| pop_tertile | low | llm_decision_router | 167 | 0.072 | 0.024 | 0.120 | 803.3 | 837.4 | 41.1 | 3.7 | 2047 | 2964 | 0.0000566 |
| pop_tertile | mid | llm_only | 166 | 0.127 | 0.060 | 0.193 | 35.7 | 40.5 | 23.6 | 2.4 | 1021 | 189 | 0.0000112 |
| pop_tertile | mid | always_rag | 166 | 0.078 | 0.030 | 0.133 | 753.1 | 776.0 | 23.5 | 2.9 | 1569 | 2644 | 0.0000470 |
| pop_tertile | mid | oracle | 166 | 0.102 | 0.036 | 0.169 | 198.7 | 226.4 | 23.4 | 2.5 | 1269 | 832 | 0.0000193 |
| pop_tertile | mid | llm_decision_router | 166 | 0.072 | 0.018 | 0.127 | 753.7 | 814.5 | 42.4 | 4.0 | 2438 | 2975 | 0.0000547 |
| musique_hops | 2.0 | llm_only | 250 | 0.056 | 0.016 | 0.100 | 43.1 | 48.1 | 27.9 | 2.3 | 982 | 347 | 0.0000133 |
| musique_hops | 2.0 | always_rag | 250 | 0.096 | 0.056 | 0.136 | 621.4 | 651.2 | 26.2 | 2.8 | 1019 | 2387 | 0.0000415 |
| musique_hops | 2.0 | oracle | 250 | 0.124 | 0.080 | 0.172 | 110.2 | 77.4 | 27.5 | 2.4 | 968 | 443 | 0.0000165 |
| musique_hops | 2.0 | llm_decision_router | 250 | 0.092 | 0.056 | 0.132 | 583.3 | 697.3 | 45.6 | 3.9 | 1924 | 2742 | 0.0000474 |
| musique_hops | 3.0 | llm_only | 155 | 0.045 | 0.006 | 0.090 | 51.7 | 56.8 | 25.3 | 2.5 | 966 | 364 | 0.0000127 |
| musique_hops | 3.0 | always_rag | 155 | 0.058 | 0.013 | 0.110 | 670.0 | 705.1 | 25.4 | 2.4 | 1110 | 2505 | 0.0000437 |
| musique_hops | 3.0 | oracle | 155 | 0.071 | 0.013 | 0.129 | 88.1 | 88.1 | 25.4 | 2.5 | 977 | 463 | 0.0000146 |
| musique_hops | 3.0 | llm_decision_router | 155 | 0.039 | -0.006 | 0.084 | 603.5 | 759.8 | 44.2 | 3.4 | 2035 | 2880 | 0.0000479 |
| musique_hops | 4.0 | llm_only | 94 | 0.064 | 0.021 | 0.117 | 55.8 | 61.1 | 22.8 | 2.3 | 937 | 381 | 0.0000119 |
| musique_hops | 4.0 | always_rag | 94 | -0.032 | -0.074 | 0.000 | 650.6 | 686.0 | 30.3 | 2.7 | 1106 | 2464 | 0.0000446 |
| musique_hops | 4.0 | oracle | 94 | 0.032 | -0.032 | 0.096 | 61.0 | 94.0 | 22.8 | 2.3 | 937 | 496 | 0.0000122 |
| musique_hops | 4.0 | llm_decision_router | 94 | -0.011 | -0.064 | 0.043 | 570.9 | 745.1 | 49.0 | 3.8 | 2025 | 2855 | 0.0000481 |
| hotpot_type | bridge | llm_only | 391 | 0.087 | 0.054 | 0.120 | 48.3 | 53.7 | 28.1 | 2.7 | 1245 | 284 | 0.0000137 |
| hotpot_type | bridge | always_rag | 391 | 0.097 | 0.061 | 0.133 | 442.9 | 467.7 | 26.3 | 3.0 | 1034 | 1672 | 0.0000327 |
| hotpot_type | bridge | oracle | 391 | 0.115 | 0.077 | 0.153 | 126.7 | 124.8 | 28.7 | 2.7 | 1174 | 517 | 0.0000178 |
| hotpot_type | bridge | llm_decision_router | 391 | 0.061 | 0.023 | 0.100 | 396.6 | 519.4 | 45.2 | 4.0 | 1988 | 2039 | 0.0000379 |
| hotpot_type | comparison | llm_only | 105 | 0.276 | 0.171 | 0.381 | 42.4 | 47.0 | 22.6 | 2.3 | 1184 | 229 | 0.0000111 |
| hotpot_type | comparison | always_rag | 105 | 0.162 | 0.076 | 0.248 | 416.5 | 440.8 | 22.2 | 2.4 | 957 | 1536 | 0.0000297 |
| hotpot_type | comparison | oracle | 105 | 0.124 | 0.048 | 0.200 | 79.6 | 149.7 | 22.4 | 2.4 | 1101 | 565 | 0.0000130 |
| hotpot_type | comparison | llm_decision_router | 105 | 0.133 | 0.048 | 0.219 | 349.4 | 467.5 | 41.2 | 3.4 | 1840 | 1821 | 0.0000340 |
| wiki_type | bridge_comparison | llm_only | 96 | 0.156 | 0.010 | 0.302 | 47.8 | 52.9 | 22.5 | 3.5 | 968 | 321 | 0.0000114 |
| wiki_type | bridge_comparison | always_rag | 96 | 0.062 | -0.052 | 0.177 | 516.6 | 541.6 | 23.7 | 3.8 | 1095 | 1999 | 0.0000353 |
| wiki_type | bridge_comparison | oracle | 96 | 0.094 | -0.042 | 0.229 | 186.6 | 198.3 | 23.2 | 3.7 | 990 | 814 | 0.0000186 |
| wiki_type | bridge_comparison | llm_decision_router | 96 | 0.031 | -0.094 | 0.156 | 414.5 | 592.5 | 42.5 | 4.8 | 1966 | 2351 | 0.0000377 |
| wiki_type | comparison | llm_only | 137 | 0.117 | 0.007 | 0.226 | 44.3 | 49.0 | 23.5 | 3.5 | 1020 | 320 | 0.0000116 |
| wiki_type | comparison | always_rag | 137 | 0.109 | 0.015 | 0.212 | 553.6 | 582.9 | 24.2 | 3.7 | 1098 | 2151 | 0.0000374 |
| wiki_type | comparison | oracle | 137 | 0.131 | 0.044 | 0.219 | 229.2 | 236.5 | 23.9 | 3.6 | 1016 | 958 | 0.0000210 |
| wiki_type | comparison | llm_decision_router | 137 | 0.066 | -0.036 | 0.175 | 476.8 | 627.0 | 43.1 | 4.7 | 2040 | 2489 | 0.0000411 |
| wiki_type | compositional | llm_only | 205 | 0.034 | -0.010 | 0.078 | 41.8 | 47.2 | 23.3 | 1.8 | 1032 | 299 | 0.0000114 |
| wiki_type | compositional | always_rag | 205 | 0.117 | 0.063 | 0.171 | 755.5 | 790.5 | 24.7 | 2.2 | 1240 | 2847 | 0.0000477 |
| wiki_type | compositional | oracle | 205 | 0.098 | 0.039 | 0.156 | 139.1 | 91.2 | 23.3 | 1.8 | 1036 | 459 | 0.0000163 |
| wiki_type | compositional | llm_decision_router | 205 | 0.112 | 0.059 | 0.166 | 750.3 | 835.7 | 43.7 | 3.2 | 2011 | 3195 | 0.0000550 |
| wiki_type | inference | llm_only | 62 | 0.065 | 0.016 | 0.129 | 41.0 | 46.7 | 30.5 | 3.2 | 1079 | 352 | 0.0000143 |
| wiki_type | inference | always_rag | 62 | 0.194 | 0.081 | 0.306 | 832.2 | 874.4 | 33.5 | 3.9 | 1090 | 3275 | 0.0000550 |
| wiki_type | inference | oracle | 62 | 0.226 | 0.113 | 0.355 | 210.2 | 74.7 | 32.8 | 3.3 | 1127 | 452 | 0.0000236 |
| wiki_type | inference | llm_decision_router | 62 | 0.194 | 0.081 | 0.306 | 852.0 | 919.1 | 52.5 | 4.9 | 1994 | 3624 | 0.0000636 |
| hop_type | multi | llm_only | 1495 | 0.045 | 0.025 | 0.066 | 46.2 | 65.5 | 25.7 | 6.4 | 1074 | 365 | 0.0000126 |
| hop_type | multi | always_rag | 1495 | 0.064 | 0.043 | 0.084 | 581.4 | 614.5 | 25.9 | 4.8 | 1079 | 2479 | 0.0000394 |
| hop_type | multi | oracle | 1495 | 0.074 | 0.053 | 0.096 | 130.9 | 131.3 | 26.0 | 6.1 | 1052 | 618 | 0.0000169 |
| hop_type | multi | llm_decision_router | 1495 | 0.054 | 0.033 | 0.075 | 532.8 | 639.5 | 44.8 | 8.7 | 1981 | 2590 | 0.0000446 |
| hop_type | single | llm_only | 1499 | 0.129 | 0.107 | 0.151 | 39.8 | 58.9 | 24.8 | 5.1 | 1024 | 310 | 0.0000119 |
| hop_type | single | always_rag | 1499 | 0.069 | 0.050 | 0.087 | 758.1 | 792.0 | 23.4 | 4.5 | 1120 | 3266 | 0.0000473 |
| hop_type | single | oracle | 1499 | 0.090 | 0.070 | 0.109 | 168.2 | 218.9 | 24.8 | 5.0 | 1077 | 962 | 0.0000183 |
| hop_type | single | llm_decision_router | 1499 | 0.081 | 0.061 | 0.103 | 711.7 | 635.9 | 42.6 | 6.8 | 2005 | 2583 | 0.0000526 |
| pop_tertile | high | llm_only | 167 | 0.126 | 0.060 | 0.192 | 35.2 | 54.3 | 24.8 | 4.8 | 981 | 293 | 0.0000117 |
| pop_tertile | high | always_rag | 167 | 0.030 | -0.012 | 0.072 | 746.0 | 780.0 | 22.9 | 4.3 | 1496 | 3153 | 0.0000465 |
| pop_tertile | high | oracle | 167 | 0.114 | 0.054 | 0.174 | 136.6 | 166.3 | 24.6 | 4.6 | 1189 | 733 | 0.0000167 |
| pop_tertile | high | llm_decision_router | 167 | 0.036 | 0.000 | 0.078 | 732.9 | 685.6 | 41.9 | 6.4 | 2325 | 2743 | 0.0000534 |
| pop_tertile | low | llm_only | 167 | 0.102 | 0.042 | 0.162 | 36.2 | 55.4 | 23.7 | 5.5 | 1075 | 319 | 0.0000113 |
| pop_tertile | low | always_rag | 167 | 0.048 | 0.012 | 0.090 | 772.4 | 809.0 | 22.1 | 4.8 | 1167 | 3285 | 0.0000475 |
| pop_tertile | low | oracle | 167 | 0.066 | 0.024 | 0.114 | 233.0 | 285.3 | 23.8 | 5.1 | 1161 | 1252 | 0.0000212 |
| pop_tertile | low | llm_decision_router | 167 | 0.048 | 0.012 | 0.090 | 803.3 | 850.1 | 41.1 | 7.5 | 2047 | 3439 | 0.0000566 |
| pop_tertile | mid | llm_only | 166 | 0.084 | 0.036 | 0.139 | 35.7 | 54.8 | 23.6 | 4.8 | 1021 | 294 | 0.0000112 |
| pop_tertile | mid | always_rag | 166 | 0.048 | 0.012 | 0.090 | 753.1 | 789.2 | 23.5 | 4.3 | 1569 | 3216 | 0.0000470 |
| pop_tertile | mid | oracle | 166 | 0.078 | 0.024 | 0.133 | 198.7 | 225.2 | 23.4 | 4.7 | 1269 | 990 | 0.0000193 |
| pop_tertile | mid | llm_decision_router | 166 | 0.054 | 0.012 | 0.096 | 753.7 | 811.1 | 42.4 | 6.5 | 2438 | 3272 | 0.0000547 |
| musique_hops | 2.0 | llm_only | 250 | 0.048 | 0.004 | 0.092 | 43.1 | 62.3 | 27.9 | 5.8 | 982 | 330 | 0.0000133 |
| musique_hops | 2.0 | always_rag | 250 | 0.080 | 0.040 | 0.124 | 621.4 | 652.3 | 26.2 | 4.9 | 1019 | 2651 | 0.0000415 |
| musique_hops | 2.0 | oracle | 250 | 0.104 | 0.052 | 0.156 | 110.2 | 100.4 | 27.5 | 5.6 | 968 | 472 | 0.0000165 |
| musique_hops | 2.0 | llm_decision_router | 250 | 0.072 | 0.032 | 0.116 | 583.3 | 669.7 | 45.6 | 7.8 | 1924 | 2696 | 0.0000474 |
| musique_hops | 3.0 | llm_only | 155 | 0.045 | 0.000 | 0.090 | 51.7 | 70.8 | 25.3 | 6.9 | 966 | 401 | 0.0000127 |
| musique_hops | 3.0 | always_rag | 155 | 0.039 | -0.006 | 0.084 | 670.0 | 699.8 | 25.4 | 4.1 | 1110 | 2777 | 0.0000437 |
| musique_hops | 3.0 | oracle | 155 | 0.052 | -0.006 | 0.110 | 88.1 | 107.1 | 25.4 | 6.8 | 977 | 543 | 0.0000146 |
| musique_hops | 3.0 | llm_decision_router | 155 | 0.019 | -0.026 | 0.065 | 603.5 | 769.6 | 44.2 | 7.9 | 2035 | 3059 | 0.0000479 |
| musique_hops | 4.0 | llm_only | 94 | 0.064 | 0.021 | 0.117 | 55.8 | 75.1 | 22.8 | 7.1 | 937 | 444 | 0.0000119 |
| musique_hops | 4.0 | always_rag | 94 | 0.000 | -0.032 | 0.032 | 650.6 | 681.5 | 30.3 | 4.3 | 1106 | 2682 | 0.0000446 |
| musique_hops | 4.0 | oracle | 94 | 0.064 | 0.011 | 0.128 | 61.0 | 79.8 | 22.8 | 7.1 | 937 | 461 | 0.0000122 |
| musique_hops | 4.0 | llm_decision_router | 94 | 0.021 | -0.021 | 0.064 | 570.9 | 755.6 | 49.0 | 7.1 | 2025 | 2956 | 0.0000481 |
| hotpot_type | bridge | llm_only | 391 | 0.049 | 0.018 | 0.082 | 48.3 | 67.5 | 28.1 | 6.1 | 1245 | 363 | 0.0000137 |
| hotpot_type | bridge | always_rag | 391 | 0.072 | 0.033 | 0.110 | 442.9 | 472.7 | 26.3 | 4.8 | 1034 | 1918 | 0.0000327 |
| hotpot_type | bridge | oracle | 391 | 0.069 | 0.031 | 0.110 | 126.7 | 140.3 | 28.7 | 5.4 | 1174 | 625 | 0.0000178 |
| hotpot_type | bridge | llm_decision_router | 391 | 0.069 | 0.028 | 0.110 | 396.6 | 470.1 | 45.2 | 7.2 | 1988 | 1858 | 0.0000379 |
| hotpot_type | comparison | llm_only | 105 | 0.162 | 0.057 | 0.267 | 42.4 | 61.6 | 22.6 | 5.4 | 1184 | 310 | 0.0000111 |
| hotpot_type | comparison | always_rag | 105 | 0.076 | 0.000 | 0.152 | 416.5 | 447.2 | 22.2 | 4.1 | 957 | 1757 | 0.0000297 |
| hotpot_type | comparison | oracle | 105 | 0.067 | 0.000 | 0.133 | 79.6 | 129.4 | 22.4 | 5.3 | 1101 | 569 | 0.0000130 |
| hotpot_type | comparison | llm_decision_router | 105 | 0.105 | 0.019 | 0.190 | 349.4 | 397.7 | 41.2 | 6.7 | 1840 | 1537 | 0.0000340 |
| wiki_type | bridge_comparison | llm_only | 96 | -0.094 | -0.240 | 0.052 | 47.8 | 67.0 | 22.5 | 6.1 | 968 | 344 | 0.0000114 |
| wiki_type | bridge_comparison | always_rag | 96 | 0.042 | -0.083 | 0.167 | 516.6 | 549.4 | 23.7 | 5.4 | 1095 | 2245 | 0.0000353 |
| wiki_type | bridge_comparison | oracle | 96 | 0.010 | -0.104 | 0.125 | 186.6 | 147.8 | 23.2 | 6.1 | 990 | 667 | 0.0000186 |
| wiki_type | bridge_comparison | llm_decision_router | 96 | -0.021 | -0.146 | 0.104 | 414.5 | 581.6 | 42.5 | 8.4 | 1966 | 2329 | 0.0000377 |
| wiki_type | comparison | llm_only | 137 | 0.029 | -0.080 | 0.139 | 44.3 | 63.8 | 23.5 | 6.0 | 1020 | 330 | 0.0000116 |
| wiki_type | comparison | always_rag | 137 | 0.058 | -0.044 | 0.161 | 553.6 | 588.9 | 24.2 | 5.2 | 1098 | 2408 | 0.0000374 |
| wiki_type | comparison | oracle | 137 | 0.109 | 0.022 | 0.197 | 229.2 | 201.6 | 23.9 | 5.9 | 1016 | 889 | 0.0000210 |
| wiki_type | comparison | llm_decision_router | 137 | 0.015 | -0.088 | 0.117 | 476.8 | 606.2 | 43.1 | 11.7 | 2040 | 2584 | 0.0000411 |
| wiki_type | compositional | llm_only | 205 | 0.039 | 0.000 | 0.078 | 41.8 | 61.1 | 23.3 | 6.7 | 1032 | 359 | 0.0000114 |
| wiki_type | compositional | always_rag | 205 | 0.059 | 0.015 | 0.107 | 755.5 | 796.3 | 24.7 | 4.8 | 1240 | 3185 | 0.0000477 |
| wiki_type | compositional | oracle | 205 | 0.049 | 0.000 | 0.098 | 139.1 | 145.9 | 23.3 | 6.4 | 1036 | 694 | 0.0000163 |
| wiki_type | compositional | llm_decision_router | 205 | 0.054 | 0.010 | 0.102 | 750.3 | 856.4 | 43.7 | 13.0 | 2011 | 3610 | 0.0000550 |
| wiki_type | inference | llm_only | 62 | 0.065 | 0.016 | 0.129 | 41.0 | 60.6 | 30.5 | 10.9 | 1079 | 532 | 0.0000143 |
| wiki_type | inference | always_rag | 62 | 0.145 | 0.032 | 0.258 | 832.2 | 880.4 | 33.5 | 7.4 | 1090 | 3674 | 0.0000550 |
| wiki_type | inference | oracle | 62 | 0.177 | 0.065 | 0.290 | 210.2 | 111.5 | 32.8 | 11.0 | 1127 | 739 | 0.0000236 |
| wiki_type | inference | llm_decision_router | 62 | 0.145 | 0.032 | 0.258 | 852.0 | 940.0 | 52.5 | 10.1 | 1994 | 3887 | 0.0000636 |
| hop_type | multi | llm_only | 1495 | 0.048 | 0.027 | 0.070 | 46.2 | 54.6 | 25.7 | 3.8 | 1074 | 717 | 0.0000126 |
| hop_type | multi | always_rag | 1495 | 0.017 | -0.003 | 0.038 | 581.4 | 631.1 | 25.9 | 3.7 | 1079 | 4335 | 0.0000394 |
| hop_type | multi | oracle | 1495 | 0.037 | 0.017 | 0.059 | 130.9 | 145.9 | 26.0 | 3.9 | 1052 | 1301 | 0.0000169 |
| hop_type | multi | llm_decision_router | 1495 | -0.004 | -0.026 | 0.017 | 532.8 | 676.5 | 44.8 | 4.7 | 1981 | 4774 | 0.0000446 |
| hop_type | single | llm_only | 1499 | 0.154 | 0.131 | 0.177 | 39.8 | 47.8 | 24.8 | 3.6 | 1024 | 931 | 0.0000119 |
| hop_type | single | always_rag | 1499 | 0.037 | 0.019 | 0.055 | 758.1 | 804.8 | 23.4 | 3.7 | 1120 | 5141 | 0.0000473 |
| hop_type | single | oracle | 1499 | 0.073 | 0.053 | 0.092 | 168.2 | 246.0 | 24.8 | 3.7 | 1077 | 2042 | 0.0000183 |
| hop_type | single | llm_decision_router | 1499 | 0.035 | 0.017 | 0.055 | 711.7 | 802.3 | 42.6 | 4.7 | 2005 | 5420 | 0.0000526 |
| pop_tertile | high | llm_only | 167 | 0.150 | 0.084 | 0.216 | 35.2 | 43.3 | 24.8 | 3.4 | 981 | 763 | 0.0000117 |
| pop_tertile | high | always_rag | 167 | 0.006 | -0.030 | 0.042 | 746.0 | 790.5 | 22.9 | 3.8 | 1496 | 4955 | 0.0000465 |
| pop_tertile | high | oracle | 167 | 0.102 | 0.054 | 0.156 | 136.6 | 187.0 | 24.6 | 3.5 | 1189 | 1596 | 0.0000167 |
| pop_tertile | high | llm_decision_router | 167 | 0.006 | -0.030 | 0.042 | 732.9 | 817.8 | 41.9 | 4.7 | 2325 | 5406 | 0.0000534 |
| pop_tertile | low | llm_only | 167 | 0.030 | -0.036 | 0.096 | 36.2 | 44.3 | 23.7 | 3.2 | 1075 | 766 | 0.0000113 |
| pop_tertile | low | always_rag | 167 | 0.018 | -0.024 | 0.060 | 772.4 | 822.1 | 22.1 | 3.4 | 1167 | 5106 | 0.0000475 |
| pop_tertile | low | oracle | 167 | -0.006 | -0.054 | 0.042 | 233.0 | 280.9 | 23.8 | 3.2 | 1161 | 2145 | 0.0000212 |
| pop_tertile | low | llm_decision_router | 167 | 0.018 | -0.024 | 0.060 | 803.3 | 864.4 | 41.1 | 4.4 | 2047 | 5649 | 0.0000566 |
| pop_tertile | mid | llm_only | 166 | 0.078 | 0.024 | 0.139 | 35.7 | 43.7 | 23.6 | 3.5 | 1021 | 778 | 0.0000112 |
| pop_tertile | mid | always_rag | 166 | 0.006 | -0.024 | 0.036 | 753.1 | 797.3 | 23.5 | 3.4 | 1569 | 5059 | 0.0000470 |
| pop_tertile | mid | oracle | 166 | 0.042 | 0.000 | 0.090 | 198.7 | 244.9 | 23.4 | 3.5 | 1269 | 1942 | 0.0000193 |
| pop_tertile | mid | llm_decision_router | 166 | 0.000 | -0.036 | 0.030 | 753.7 | 825.0 | 42.4 | 4.4 | 2438 | 5512 | 0.0000547 |
| musique_hops | 2.0 | llm_only | 250 | 0.056 | 0.020 | 0.096 | 43.1 | 51.4 | 27.9 | 3.9 | 982 | 649 | 0.0000133 |
| musique_hops | 2.0 | always_rag | 250 | 0.044 | 0.000 | 0.088 | 621.4 | 670.4 | 26.2 | 3.4 | 1019 | 4454 | 0.0000415 |
| musique_hops | 2.0 | oracle | 250 | 0.084 | 0.036 | 0.132 | 110.2 | 104.2 | 27.5 | 4.0 | 968 | 990 | 0.0000165 |
| musique_hops | 2.0 | llm_decision_router | 250 | 0.040 | -0.004 | 0.084 | 583.3 | 715.9 | 45.6 | 4.4 | 1924 | 4902 | 0.0000474 |
| musique_hops | 3.0 | llm_only | 155 | 0.052 | 0.019 | 0.090 | 51.7 | 59.9 | 25.3 | 3.5 | 966 | 689 | 0.0000127 |
| musique_hops | 3.0 | always_rag | 155 | -0.006 | -0.058 | 0.045 | 670.0 | 723.0 | 25.4 | 3.6 | 1110 | 4723 | 0.0000437 |
| musique_hops | 3.0 | oracle | 155 | 0.019 | -0.039 | 0.077 | 88.1 | 125.4 | 25.4 | 3.6 | 977 | 1080 | 0.0000146 |
| musique_hops | 3.0 | llm_decision_router | 155 | -0.026 | -0.084 | 0.032 | 603.5 | 781.0 | 44.2 | 4.6 | 2035 | 5245 | 0.0000479 |
| musique_hops | 4.0 | llm_only | 94 | 0.053 | 0.000 | 0.106 | 55.8 | 64.2 | 22.8 | 3.7 | 937 | 753 | 0.0000119 |
| musique_hops | 4.0 | always_rag | 94 | -0.043 | -0.085 | -0.011 | 650.6 | 706.1 | 30.3 | 3.7 | 1106 | 4734 | 0.0000446 |
| musique_hops | 4.0 | oracle | 94 | 0.021 | -0.043 | 0.085 | 61.0 | 92.4 | 22.8 | 3.7 | 937 | 919 | 0.0000122 |
| musique_hops | 4.0 | llm_decision_router | 94 | -0.021 | -0.074 | 0.032 | 570.9 | 768.3 | 49.0 | 4.7 | 2025 | 5296 | 0.0000481 |
| hotpot_type | bridge | llm_only | 391 | 0.064 | 0.036 | 0.095 | 48.3 | 57.0 | 28.1 | 3.8 | 1245 | 774 | 0.0000137 |
| hotpot_type | bridge | always_rag | 391 | 0.026 | -0.013 | 0.064 | 442.9 | 483.7 | 26.3 | 3.6 | 1034 | 3362 | 0.0000327 |
| hotpot_type | bridge | oracle | 391 | 0.036 | -0.003 | 0.074 | 126.7 | 157.8 | 28.7 | 3.9 | 1174 | 1400 | 0.0000178 |
| hotpot_type | bridge | llm_decision_router | 391 | -0.010 | -0.051 | 0.031 | 396.6 | 537.4 | 45.2 | 4.6 | 1988 | 3845 | 0.0000379 |
| hotpot_type | comparison | llm_only | 105 | 0.162 | 0.057 | 0.276 | 42.4 | 50.4 | 22.6 | 3.8 | 1184 | 704 | 0.0000111 |
| hotpot_type | comparison | always_rag | 105 | 0.048 | -0.029 | 0.124 | 416.5 | 456.9 | 22.2 | 3.0 | 957 | 3154 | 0.0000297 |
| hotpot_type | comparison | oracle | 105 | 0.057 | -0.019 | 0.133 | 79.6 | 132.7 | 22.4 | 3.6 | 1101 | 1203 | 0.0000130 |
| hotpot_type | comparison | llm_decision_router | 105 | 0.019 | -0.057 | 0.105 | 349.4 | 450.4 | 41.2 | 4.3 | 1840 | 3278 | 0.0000340 |
| wiki_type | bridge_comparison | llm_only | 96 | 0.042 | -0.104 | 0.188 | 47.8 | 56.1 | 22.5 | 4.0 | 968 | 752 | 0.0000114 |
| wiki_type | bridge_comparison | always_rag | 96 | -0.021 | -0.156 | 0.115 | 516.6 | 561.6 | 23.7 | 4.2 | 1095 | 4119 | 0.0000353 |
| wiki_type | bridge_comparison | oracle | 96 | 0.031 | -0.104 | 0.156 | 186.6 | 177.4 | 23.2 | 4.2 | 990 | 1494 | 0.0000186 |
| wiki_type | bridge_comparison | llm_decision_router | 96 | -0.052 | -0.198 | 0.094 | 414.5 | 615.8 | 42.5 | 5.2 | 1966 | 4601 | 0.0000377 |
| wiki_type | comparison | llm_only | 137 | -0.007 | -0.124 | 0.109 | 44.3 | 52.5 | 23.5 | 4.2 | 1020 | 734 | 0.0000116 |
| wiki_type | comparison | always_rag | 137 | -0.036 | -0.117 | 0.044 | 553.6 | 605.1 | 24.2 | 4.2 | 1098 | 4412 | 0.0000374 |
| wiki_type | comparison | oracle | 137 | -0.015 | -0.088 | 0.058 | 229.2 | 238.7 | 23.9 | 4.4 | 1016 | 1984 | 0.0000210 |
| wiki_type | comparison | llm_decision_router | 137 | -0.102 | -0.190 | -0.007 | 476.8 | 629.2 | 43.1 | 5.3 | 2040 | 4698 | 0.0000411 |
| wiki_type | compositional | llm_only | 205 | -0.010 | -0.049 | 0.029 | 41.8 | 50.2 | 23.3 | 3.0 | 1032 | 662 | 0.0000114 |
| wiki_type | compositional | always_rag | 205 | 0.010 | -0.039 | 0.059 | 755.5 | 815.2 | 24.7 | 2.9 | 1240 | 5570 | 0.0000477 |
| wiki_type | compositional | oracle | 205 | -0.005 | -0.054 | 0.044 | 139.1 | 151.3 | 23.3 | 3.2 | 1036 | 1327 | 0.0000163 |
| wiki_type | compositional | llm_decision_router | 205 | 0.005 | -0.044 | 0.054 | 750.3 | 863.4 | 43.7 | 3.9 | 2011 | 6032 | 0.0000550 |
| wiki_type | inference | llm_only | 62 | 0.032 | -0.032 | 0.097 | 41.0 | 49.4 | 30.5 | 5.2 | 1079 | 771 | 0.0000143 |
| wiki_type | inference | always_rag | 62 | 0.161 | 0.065 | 0.258 | 832.2 | 910.3 | 33.5 | 6.8 | 1090 | 6505 | 0.0000550 |
| wiki_type | inference | oracle | 62 | 0.161 | 0.048 | 0.274 | 210.2 | 122.8 | 32.8 | 5.1 | 1127 | 1348 | 0.0000236 |
| wiki_type | inference | llm_decision_router | 62 | 0.161 | 0.065 | 0.258 | 852.0 | 957.7 | 52.5 | 7.8 | 1994 | 6950 | 0.0000636 |
| hop_type | multi | llm_only | 1500 | -0.052 | -0.074 | -0.029 | 67.7 | 44.5 | 34.4 | 3.6 | 954 | 906 | 0.0000152 |
| hop_type | multi | always_rag | 1500 | -0.019 | -0.038 | 0.001 | 945.1 | 584.7 | 21.8 | 3.9 | 946 | 843 | 0.0000163 |
| hop_type | multi | oracle | 1500 | -0.018 | -0.039 | 0.003 | 221.5 | 123.4 | 32.2 | 3.7 | 949 | 898 | 0.0000176 |
| hop_type | multi | llm_decision_router | 1500 | -0.014 | -0.035 | 0.007 | 927.4 | 554.2 | 61.2 | 4.9 | 1898 | 1691 | 0.0000382 |
| hop_type | single | llm_only | 1500 | -0.048 | -0.069 | -0.027 | 56.8 | 38.0 | 16.7 | 3.2 | 913 | 865 | 0.0000064 |
| hop_type | single | always_rag | 1500 | -0.009 | -0.025 | 0.008 | 1216.7 | 763.2 | 12.4 | 3.5 | 1045 | 917 | 0.0000128 |
| hop_type | single | oracle | 1500 | -0.017 | -0.034 | -0.001 | 211.4 | 111.3 | 15.6 | 3.2 | 920 | 867 | 0.0000103 |
| hop_type | single | llm_decision_router | 1500 | -0.008 | -0.026 | 0.010 | 1118.7 | 595.6 | 46.0 | 4.4 | 1960 | 1725 | 0.0000443 |
| pop_tertile | high | llm_only | 167 | -0.036 | -0.096 | 0.024 | 51.0 | 33.3 | 19.3 | 3.0 | 892 | 858 | 0.0000080 |
| pop_tertile | high | always_rag | 167 | 0.018 | -0.030 | 0.066 | 1206.9 | 752.1 | 10.8 | 3.5 | 869 | 883 | 0.0000158 |
| pop_tertile | high | oracle | 167 | -0.024 | -0.078 | 0.030 | 128.4 | 73.6 | 18.5 | 3.0 | 888 | 863 | 0.0000092 |
| pop_tertile | high | llm_decision_router | 167 | 0.030 | -0.024 | 0.084 | 1102.9 | 643.2 | 45.4 | 4.5 | 1817 | 1699 | 0.0000384 |
| pop_tertile | low | llm_only | 167 | -0.156 | -0.222 | -0.096 | 52.1 | 34.3 | 24.5 | 3.4 | 916 | 874 | 0.0000102 |
| pop_tertile | low | always_rag | 167 | -0.042 | -0.078 | -0.006 | 1230.1 | 777.3 | 13.7 | 3.4 | 876 | 901 | 0.0000172 |
| pop_tertile | low | oracle | 167 | -0.060 | -0.108 | -0.018 | 381.5 | 167.0 | 21.9 | 3.4 | 908 | 866 | 0.0000220 |
| pop_tertile | low | llm_decision_router | 167 | -0.048 | -0.084 | -0.012 | 1258.6 | 755.6 | 64.1 | 4.4 | 1892 | 1730 | 0.0000473 |
| pop_tertile | mid | llm_only | 166 | -0.096 | -0.175 | -0.018 | 51.7 | 33.8 | 21.8 | 3.2 | 912 | 877 | 0.0000091 |
| pop_tertile | mid | always_rag | 166 | 0.000 | -0.030 | 0.030 | 1208.4 | 759.6 | 13.6 | 3.8 | 865 | 887 | 0.0000139 |
| pop_tertile | mid | oracle | 166 | -0.018 | -0.072 | 0.036 | 289.0 | 124.0 | 20.0 | 3.3 | 901 | 883 | 0.0000183 |
| pop_tertile | mid | llm_decision_router | 166 | 0.006 | -0.030 | 0.042 | 1205.0 | 706.8 | 59.9 | 4.7 | 1855 | 1715 | 0.0000441 |
| musique_hops | 2.0 | llm_only | 251 | 0.024 | -0.028 | 0.080 | 62.2 | 41.3 | 36.6 | 3.5 | 964 | 913 | 0.0000162 |
| musique_hops | 2.0 | always_rag | 251 | 0.012 | -0.036 | 0.064 | 1016.4 | 624.6 | 22.8 | 3.6 | 941 | 840 | 0.0000178 |
| musique_hops | 2.0 | oracle | 251 | 0.040 | -0.020 | 0.100 | 205.5 | 125.7 | 35.2 | 3.5 | 964 | 900 | 0.0000173 |
| musique_hops | 2.0 | llm_decision_router | 251 | 0.020 | -0.032 | 0.076 | 999.3 | 623.7 | 65.6 | 4.6 | 1901 | 1697 | 0.0000371 |
| musique_hops | 3.0 | llm_only | 155 | 0.032 | -0.019 | 0.090 | 73.7 | 49.8 | 62.5 | 3.4 | 1057 | 891 | 0.0000291 |
| musique_hops | 3.0 | always_rag | 155 | 0.052 | 0.013 | 0.097 | 1077.9 | 672.4 | 36.3 | 4.1 | 1024 | 844 | 0.0000257 |
| musique_hops | 3.0 | oracle | 155 | 0.045 | -0.006 | 0.097 | 148.8 | 90.9 | 58.4 | 3.4 | 1049 | 886 | 0.0000284 |
| musique_hops | 3.0 | llm_decision_router | 155 | 0.052 | 0.013 | 0.097 | 1086.8 | 713.9 | 88.1 | 5.1 | 2011 | 1697 | 0.0000456 |
| musique_hops | 4.0 | llm_only | 94 | 0.053 | 0.000 | 0.106 | 79.5 | 54.1 | 89.3 | 3.5 | 1199 | 905 | 0.0000424 |
| musique_hops | 4.0 | always_rag | 94 | 0.032 | -0.032 | 0.106 | 1046.3 | 653.5 | 53.8 | 4.0 | 1037 | 838 | 0.0000335 |
| musique_hops | 4.0 | oracle | 94 | 0.085 | 0.021 | 0.149 | 157.2 | 74.8 | 86.8 | 3.5 | 1186 | 909 | 0.0000458 |
| musique_hops | 4.0 | llm_decision_router | 94 | 0.032 | -0.032 | 0.106 | 1114.7 | 706.6 | 118.8 | 5.0 | 2105 | 1698 | 0.0000642 |
| hotpot_type | bridge | llm_only | 395 | -0.041 | -0.081 | 0.000 | 70.8 | 46.5 | 29.2 | 3.4 | 940 | 903 | 0.0000126 |
| hotpot_type | bridge | always_rag | 395 | -0.020 | -0.058 | 0.018 | 728.7 | 445.6 | 15.8 | 3.8 | 918 | 845 | 0.0000116 |
| hotpot_type | bridge | oracle | 395 | -0.046 | -0.086 | -0.005 | 188.6 | 119.1 | 25.9 | 3.5 | 932 | 893 | 0.0000118 |
| hotpot_type | bridge | llm_decision_router | 395 | -0.023 | -0.066 | 0.020 | 688.0 | 412.7 | 46.7 | 4.8 | 1835 | 1685 | 0.0000274 |
| hotpot_type | comparison | llm_only | 105 | -0.019 | -0.095 | 0.057 | 64.3 | 40.5 | 11.7 | 2.8 | 836 | 871 | 0.0000045 |
| hotpot_type | comparison | always_rag | 105 | -0.057 | -0.114 | -0.010 | 685.2 | 419.2 | 10.6 | 2.8 | 925 | 872 | 0.0000093 |
| hotpot_type | comparison | oracle | 105 | 0.019 | -0.029 | 0.067 | 119.8 | 54.5 | 11.4 | 2.8 | 841 | 870 | 0.0000079 |
| hotpot_type | comparison | llm_decision_router | 105 | -0.019 | -0.076 | 0.029 | 561.2 | 256.9 | 42.7 | 3.9 | 1837 | 1662 | 0.0000366 |
| wiki_type | bridge_comparison | llm_only | 96 | -0.302 | -0.427 | -0.177 | 70.2 | 46.1 | 23.5 | 4.1 | 898 | 942 | 0.0000094 |
| wiki_type | bridge_comparison | always_rag | 96 | -0.146 | -0.271 | -0.021 | 852.2 | 522.0 | 20.7 | 4.5 | 916 | 851 | 0.0000146 |
| wiki_type | bridge_comparison | oracle | 96 | -0.219 | -0.333 | -0.094 | 310.6 | 161.5 | 22.5 | 4.4 | 900 | 936 | 0.0000155 |
| wiki_type | bridge_comparison | llm_decision_router | 96 | -0.135 | -0.260 | -0.010 | 828.6 | 398.7 | 78.3 | 5.5 | 1948 | 1729 | 0.0000589 |
| wiki_type | comparison | llm_only | 137 | -0.270 | -0.372 | -0.168 | 66.9 | 42.6 | 17.2 | 4.0 | 884 | 902 | 0.0000065 |
| wiki_type | comparison | always_rag | 137 | -0.022 | -0.095 | 0.051 | 903.6 | 558.8 | 11.2 | 4.1 | 872 | 833 | 0.0000097 |
| wiki_type | comparison | oracle | 137 | -0.015 | -0.073 | 0.044 | 433.2 | 146.5 | 14.7 | 4.2 | 877 | 896 | 0.0000261 |
| wiki_type | comparison | llm_decision_router | 137 | -0.007 | -0.080 | 0.066 | 868.2 | 427.6 | 56.6 | 5.0 | 1834 | 1726 | 0.0000479 |
| wiki_type | compositional | llm_only | 205 | -0.024 | -0.073 | 0.024 | 60.7 | 40.0 | 25.6 | 2.9 | 925 | 916 | 0.0000111 |
| wiki_type | compositional | always_rag | 205 | -0.049 | -0.098 | -0.005 | 1212.1 | 761.6 | 17.3 | 3.3 | 971 | 829 | 0.0000159 |
| wiki_type | compositional | oracle | 205 | -0.034 | -0.088 | 0.020 | 241.5 | 155.8 | 24.2 | 3.0 | 911 | 905 | 0.0000113 |
| wiki_type | compositional | llm_decision_router | 205 | -0.044 | -0.093 | 0.005 | 1227.4 | 784.9 | 39.1 | 4.3 | 1872 | 1667 | 0.0000243 |
| wiki_type | inference | llm_only | 62 | -0.081 | -0.161 | 0.000 | 65.4 | 39.2 | 28.4 | 7.6 | 917 | 926 | 0.0000103 |
| wiki_type | inference | always_rag | 62 | -0.016 | -0.113 | 0.081 | 1343.0 | 834.5 | 30.1 | 7.0 | 966 | 844 | 0.0000200 |
| wiki_type | inference | oracle | 62 | -0.097 | -0.178 | -0.016 | 276.3 | 196.7 | 27.8 | 8.3 | 931 | 915 | 0.0000071 |
| wiki_type | inference | llm_decision_router | 62 | -0.048 | -0.129 | 0.032 | 1391.5 | 806.5 | 70.6 | 7.6 | 1952 | 1667 | 0.0000489 |
| hop_type | multi | llm_only | 1500 | 0.127 | 0.105 | 0.151 | 67.7 | 51.4 | 34.4 | 2.6 | 954 | 315 | 0.0000240 |
| hop_type | multi | always_rag | 1500 | 0.150 | 0.128 | 0.172 | 945.1 | 610.9 | 21.8 | 2.9 | 946 | 2209 | 0.0001054 |
| hop_type | multi | oracle | 1500 | 0.170 | 0.146 | 0.193 | 221.5 | 120.9 | 32.2 | 2.6 | 949 | 549 | 0.0000383 |
| hop_type | multi | llm_decision_router | 1500 | 0.143 | 0.121 | 0.165 | 927.4 | 658.8 | 61.2 | 3.9 | 1898 | 2564 | 0.0001234 |
| hop_type | single | llm_only | 1500 | 0.365 | 0.341 | 0.390 | 56.8 | 44.5 | 16.7 | 2.4 | 913 | 208 | 0.0000140 |
| hop_type | single | always_rag | 1500 | 0.183 | 0.162 | 0.205 | 1216.7 | 783.4 | 12.4 | 2.9 | 1045 | 2854 | 0.0001279 |
| hop_type | single | oracle | 1500 | 0.233 | 0.211 | 0.255 | 211.4 | 242.0 | 15.6 | 2.6 | 920 | 922 | 0.0000290 |
| hop_type | single | llm_decision_router | 1500 | 0.193 | 0.171 | 0.215 | 1118.7 | 817.4 | 46.0 | 4.0 | 1960 | 3159 | 0.0001349 |
| pop_tertile | high | llm_only | 167 | 0.395 | 0.317 | 0.467 | 51.0 | 40.0 | 19.3 | 2.2 | 892 | 185 | 0.0000148 |
| pop_tertile | high | always_rag | 167 | 0.132 | 0.078 | 0.186 | 1206.9 | 768.6 | 10.8 | 2.6 | 869 | 2547 | 0.0001261 |
| pop_tertile | high | oracle | 167 | 0.257 | 0.192 | 0.329 | 128.4 | 193.5 | 18.5 | 2.3 | 888 | 703 | 0.0000221 |
| pop_tertile | high | llm_decision_router | 167 | 0.150 | 0.096 | 0.210 | 1102.9 | 781.3 | 45.4 | 3.6 | 1817 | 2788 | 0.0001330 |
| pop_tertile | low | llm_only | 167 | 0.114 | 0.054 | 0.180 | 52.1 | 41.1 | 24.5 | 2.1 | 916 | 181 | 0.0000174 |
| pop_tertile | low | always_rag | 167 | 0.060 | 0.012 | 0.108 | 1230.1 | 798.4 | 13.7 | 2.6 | 876 | 2630 | 0.0001299 |
| pop_tertile | low | oracle | 167 | 0.096 | 0.048 | 0.144 | 381.5 | 267.5 | 21.9 | 2.3 | 908 | 945 | 0.0000491 |
| pop_tertile | low | llm_decision_router | 167 | 0.054 | 0.006 | 0.102 | 1258.6 | 837.4 | 64.1 | 3.7 | 1892 | 2964 | 0.0001579 |
| pop_tertile | mid | llm_only | 166 | 0.193 | 0.127 | 0.259 | 51.7 | 40.5 | 21.8 | 2.4 | 912 | 189 | 0.0000161 |
| pop_tertile | mid | always_rag | 166 | 0.084 | 0.036 | 0.139 | 1208.4 | 776.0 | 13.6 | 2.9 | 865 | 2644 | 0.0001276 |
| pop_tertile | mid | oracle | 166 | 0.151 | 0.084 | 0.217 | 289.0 | 226.4 | 20.0 | 2.5 | 901 | 832 | 0.0000389 |
| pop_tertile | mid | llm_decision_router | 166 | 0.096 | 0.042 | 0.151 | 1205.0 | 814.5 | 59.9 | 4.0 | 1855 | 2975 | 0.0001505 |
| musique_hops | 2.0 | llm_only | 251 | 0.135 | 0.084 | 0.187 | 62.2 | 48.2 | 36.6 | 2.3 | 964 | 347 | 0.0000245 |
| musique_hops | 2.0 | always_rag | 251 | 0.171 | 0.127 | 0.219 | 1016.4 | 651.6 | 22.8 | 2.8 | 941 | 2388 | 0.0001130 |
| musique_hops | 2.0 | oracle | 251 | 0.239 | 0.183 | 0.299 | 205.5 | 77.4 | 35.2 | 2.4 | 964 | 443 | 0.0000381 |
| musique_hops | 2.0 | llm_decision_router | 251 | 0.167 | 0.124 | 0.215 | 999.3 | 697.8 | 65.6 | 3.9 | 1901 | 2744 | 0.0001327 |
| musique_hops | 3.0 | llm_only | 155 | 0.123 | 0.071 | 0.181 | 73.7 | 56.8 | 62.5 | 2.5 | 1057 | 364 | 0.0000386 |
| musique_hops | 3.0 | always_rag | 155 | 0.135 | 0.077 | 0.194 | 1077.9 | 705.1 | 36.3 | 2.4 | 1024 | 2505 | 0.0001260 |
| musique_hops | 3.0 | oracle | 155 | 0.168 | 0.103 | 0.232 | 148.8 | 88.1 | 58.4 | 2.5 | 1049 | 463 | 0.0000441 |
| musique_hops | 3.0 | llm_decision_router | 155 | 0.135 | 0.077 | 0.194 | 1086.8 | 759.8 | 88.1 | 3.4 | 2011 | 2880 | 0.0001527 |
| musique_hops | 4.0 | llm_only | 94 | 0.096 | 0.043 | 0.160 | 79.5 | 61.1 | 89.3 | 2.3 | 1199 | 381 | 0.0000526 |
| musique_hops | 4.0 | always_rag | 94 | 0.074 | 0.011 | 0.138 | 1046.3 | 686.0 | 53.8 | 2.7 | 1037 | 2464 | 0.0001315 |
| musique_hops | 4.0 | oracle | 94 | 0.128 | 0.053 | 0.213 | 157.2 | 94.0 | 86.8 | 2.3 | 1186 | 496 | 0.0000591 |
| musique_hops | 4.0 | llm_decision_router | 94 | 0.074 | 0.011 | 0.138 | 1114.7 | 745.1 | 118.8 | 3.8 | 2105 | 2855 | 0.0001709 |
| hotpot_type | bridge | llm_only | 395 | 0.180 | 0.137 | 0.223 | 70.8 | 53.6 | 29.2 | 2.7 | 940 | 283 | 0.0000217 |
| hotpot_type | bridge | always_rag | 395 | 0.144 | 0.104 | 0.187 | 728.7 | 467.4 | 15.8 | 3.0 | 918 | 1671 | 0.0000808 |
| hotpot_type | bridge | oracle | 395 | 0.190 | 0.147 | 0.235 | 188.6 | 124.0 | 25.9 | 2.7 | 932 | 514 | 0.0000318 |
| hotpot_type | bridge | llm_decision_router | 395 | 0.129 | 0.089 | 0.172 | 688.0 | 519.1 | 46.7 | 4.0 | 1835 | 2037 | 0.0000921 |
| hotpot_type | comparison | llm_only | 105 | 0.295 | 0.181 | 0.410 | 64.3 | 47.0 | 11.7 | 2.3 | 836 | 229 | 0.0000123 |
| hotpot_type | comparison | always_rag | 105 | 0.133 | 0.048 | 0.219 | 685.2 | 440.8 | 10.6 | 2.4 | 925 | 1536 | 0.0000738 |
| hotpot_type | comparison | oracle | 105 | 0.124 | 0.048 | 0.200 | 119.8 | 149.7 | 11.4 | 2.4 | 841 | 565 | 0.0000177 |
| hotpot_type | comparison | llm_decision_router | 105 | 0.133 | 0.038 | 0.229 | 561.2 | 467.5 | 42.7 | 3.4 | 1837 | 1821 | 0.0000775 |
| wiki_type | bridge_comparison | llm_only | 96 | -0.062 | -0.188 | 0.062 | 70.2 | 52.9 | 23.5 | 3.5 | 898 | 321 | 0.0000188 |
| wiki_type | bridge_comparison | always_rag | 96 | 0.062 | -0.062 | 0.188 | 852.2 | 541.6 | 20.7 | 3.8 | 916 | 1999 | 0.0000956 |
| wiki_type | bridge_comparison | oracle | 96 | -0.073 | -0.198 | 0.052 | 310.6 | 198.3 | 22.5 | 3.7 | 900 | 814 | 0.0000423 |
| wiki_type | bridge_comparison | llm_decision_router | 96 | 0.052 | -0.073 | 0.177 | 828.6 | 592.5 | 78.3 | 4.8 | 1948 | 2351 | 0.0001220 |
| wiki_type | comparison | llm_only | 137 | 0.102 | -0.022 | 0.226 | 66.9 | 49.0 | 17.2 | 3.5 | 884 | 320 | 0.0000153 |
| wiki_type | comparison | always_rag | 137 | 0.248 | 0.161 | 0.336 | 903.6 | 582.9 | 11.2 | 3.7 | 872 | 2151 | 0.0000960 |
| wiki_type | comparison | oracle | 137 | 0.212 | 0.131 | 0.292 | 433.2 | 236.5 | 14.7 | 3.6 | 877 | 958 | 0.0000506 |
| wiki_type | comparison | llm_decision_router | 137 | 0.241 | 0.153 | 0.328 | 868.2 | 627.0 | 56.6 | 4.7 | 1834 | 2489 | 0.0001151 |
| wiki_type | compositional | llm_only | 205 | 0.063 | 0.010 | 0.117 | 60.7 | 47.2 | 25.6 | 1.8 | 925 | 299 | 0.0000189 |
| wiki_type | compositional | always_rag | 205 | 0.146 | 0.093 | 0.200 | 1212.1 | 790.5 | 17.3 | 2.2 | 971 | 2847 | 0.0001298 |
| wiki_type | compositional | oracle | 205 | 0.156 | 0.093 | 0.220 | 241.5 | 91.2 | 24.2 | 1.8 | 911 | 459 | 0.0000363 |
| wiki_type | compositional | llm_decision_router | 205 | 0.141 | 0.088 | 0.195 | 1227.4 | 835.7 | 39.1 | 3.2 | 1872 | 3195 | 0.0001423 |
| wiki_type | inference | llm_only | 62 | 0.097 | 0.032 | 0.177 | 65.4 | 46.7 | 28.4 | 3.2 | 917 | 352 | 0.0000208 |
| wiki_type | inference | always_rag | 62 | 0.210 | 0.097 | 0.323 | 1343.0 | 874.4 | 30.1 | 3.9 | 966 | 3275 | 0.0001494 |
| wiki_type | inference | oracle | 62 | 0.242 | 0.145 | 0.355 | 276.3 | 74.7 | 27.8 | 3.3 | 931 | 452 | 0.0000415 |
| wiki_type | inference | llm_decision_router | 62 | 0.210 | 0.097 | 0.323 | 1391.5 | 919.1 | 70.6 | 4.9 | 1952 | 3624 | 0.0001744 |
| hop_type | multi | llm_only | 1500 | 0.085 | 0.063 | 0.109 | 67.7 | 65.5 | 34.4 | 6.4 | 954 | 365 | 0.0000240 |
| hop_type | multi | always_rag | 1500 | 0.119 | 0.098 | 0.140 | 945.1 | 614.1 | 21.8 | 4.8 | 946 | 2477 | 0.0001054 |
| hop_type | multi | oracle | 1500 | 0.135 | 0.113 | 0.157 | 221.5 | 131.1 | 32.2 | 6.1 | 949 | 617 | 0.0000383 |
| hop_type | multi | llm_decision_router | 1500 | 0.122 | 0.100 | 0.144 | 927.4 | 639.3 | 61.2 | 8.7 | 1898 | 2589 | 0.0001234 |
| hop_type | single | llm_only | 1500 | 0.244 | 0.220 | 0.268 | 56.8 | 58.9 | 16.7 | 5.1 | 913 | 310 | 0.0000140 |
| hop_type | single | always_rag | 1500 | 0.123 | 0.104 | 0.142 | 1216.7 | 792.0 | 12.4 | 4.5 | 1045 | 3267 | 0.0001279 |
| hop_type | single | oracle | 1500 | 0.160 | 0.140 | 0.180 | 211.4 | 218.8 | 15.6 | 5.0 | 920 | 962 | 0.0000290 |
| hop_type | single | llm_decision_router | 1500 | 0.147 | 0.126 | 0.168 | 1118.7 | 636.0 | 46.0 | 6.8 | 1960 | 2584 | 0.0001349 |
| pop_tertile | high | llm_only | 167 | 0.293 | 0.228 | 0.365 | 51.0 | 54.3 | 19.3 | 4.8 | 892 | 293 | 0.0000148 |
| pop_tertile | high | always_rag | 167 | 0.090 | 0.036 | 0.144 | 1206.9 | 780.0 | 10.8 | 4.3 | 869 | 3153 | 0.0001261 |
| pop_tertile | high | oracle | 167 | 0.210 | 0.144 | 0.275 | 128.4 | 166.3 | 18.5 | 4.6 | 888 | 733 | 0.0000221 |
| pop_tertile | high | llm_decision_router | 167 | 0.120 | 0.066 | 0.180 | 1102.9 | 685.6 | 45.4 | 6.4 | 1817 | 2743 | 0.0001330 |
| pop_tertile | low | llm_only | 167 | 0.108 | 0.060 | 0.162 | 52.1 | 55.4 | 24.5 | 5.5 | 916 | 319 | 0.0000174 |
| pop_tertile | low | always_rag | 167 | 0.036 | -0.006 | 0.078 | 1230.1 | 809.0 | 13.7 | 4.8 | 876 | 3285 | 0.0001299 |
| pop_tertile | low | oracle | 167 | 0.084 | 0.042 | 0.132 | 381.5 | 285.3 | 21.9 | 5.1 | 908 | 1252 | 0.0000491 |
| pop_tertile | low | llm_decision_router | 167 | 0.030 | -0.006 | 0.072 | 1258.6 | 850.1 | 64.1 | 7.5 | 1892 | 3439 | 0.0001579 |
| pop_tertile | mid | llm_only | 166 | 0.151 | 0.090 | 0.211 | 51.7 | 54.8 | 21.8 | 4.8 | 912 | 294 | 0.0000161 |
| pop_tertile | mid | always_rag | 166 | 0.054 | 0.024 | 0.090 | 1208.4 | 789.2 | 13.6 | 4.3 | 865 | 3216 | 0.0001276 |
| pop_tertile | mid | oracle | 166 | 0.127 | 0.078 | 0.181 | 289.0 | 225.2 | 20.0 | 4.7 | 901 | 990 | 0.0000389 |
| pop_tertile | mid | llm_decision_router | 166 | 0.078 | 0.042 | 0.120 | 1205.0 | 811.1 | 59.9 | 6.5 | 1855 | 3272 | 0.0001505 |
| musique_hops | 2.0 | llm_only | 251 | 0.127 | 0.080 | 0.175 | 62.2 | 62.4 | 36.6 | 5.8 | 964 | 330 | 0.0000245 |
| musique_hops | 2.0 | always_rag | 251 | 0.155 | 0.108 | 0.207 | 1016.4 | 652.7 | 22.8 | 4.9 | 941 | 2652 | 0.0001130 |
| musique_hops | 2.0 | oracle | 251 | 0.219 | 0.167 | 0.275 | 205.5 | 100.3 | 35.2 | 5.6 | 964 | 472 | 0.0000381 |
| musique_hops | 2.0 | llm_decision_router | 251 | 0.147 | 0.100 | 0.199 | 999.3 | 670.3 | 65.6 | 7.8 | 1901 | 2697 | 0.0001327 |
| musique_hops | 3.0 | llm_only | 155 | 0.123 | 0.071 | 0.181 | 73.7 | 70.8 | 62.5 | 6.9 | 1057 | 401 | 0.0000386 |
| musique_hops | 3.0 | always_rag | 155 | 0.116 | 0.065 | 0.174 | 1077.9 | 699.8 | 36.3 | 4.1 | 1024 | 2777 | 0.0001260 |
| musique_hops | 3.0 | oracle | 155 | 0.148 | 0.090 | 0.206 | 148.8 | 107.1 | 58.4 | 6.8 | 1049 | 543 | 0.0000441 |
| musique_hops | 3.0 | llm_decision_router | 155 | 0.116 | 0.065 | 0.174 | 1086.8 | 769.6 | 88.1 | 7.9 | 2011 | 3059 | 0.0001527 |
| musique_hops | 4.0 | llm_only | 94 | 0.096 | 0.043 | 0.160 | 79.5 | 75.1 | 89.3 | 7.1 | 1199 | 444 | 0.0000526 |
| musique_hops | 4.0 | always_rag | 94 | 0.106 | 0.043 | 0.181 | 1046.3 | 681.5 | 53.8 | 4.3 | 1037 | 2682 | 0.0001315 |
| musique_hops | 4.0 | oracle | 94 | 0.160 | 0.085 | 0.234 | 157.2 | 79.8 | 86.8 | 7.1 | 1186 | 461 | 0.0000591 |
| musique_hops | 4.0 | llm_decision_router | 94 | 0.106 | 0.043 | 0.181 | 1114.7 | 755.6 | 118.8 | 7.1 | 2105 | 2956 | 0.0001709 |
| hotpot_type | bridge | llm_only | 395 | 0.144 | 0.101 | 0.190 | 70.8 | 67.5 | 29.2 | 6.1 | 940 | 362 | 0.0000217 |
| hotpot_type | bridge | always_rag | 395 | 0.119 | 0.081 | 0.159 | 728.7 | 472.4 | 15.8 | 4.8 | 918 | 1916 | 0.0000808 |
| hotpot_type | bridge | oracle | 395 | 0.147 | 0.101 | 0.192 | 188.6 | 139.5 | 25.9 | 5.4 | 932 | 622 | 0.0000318 |
| hotpot_type | bridge | llm_decision_router | 395 | 0.137 | 0.094 | 0.180 | 688.0 | 470.5 | 46.7 | 7.2 | 1835 | 1858 | 0.0000921 |
| hotpot_type | comparison | llm_only | 105 | 0.181 | 0.095 | 0.276 | 64.3 | 61.6 | 11.7 | 5.4 | 836 | 310 | 0.0000123 |
| hotpot_type | comparison | always_rag | 105 | 0.048 | -0.038 | 0.133 | 685.2 | 447.2 | 10.6 | 4.1 | 925 | 1757 | 0.0000738 |
| hotpot_type | comparison | oracle | 105 | 0.067 | 0.010 | 0.133 | 119.8 | 129.4 | 11.4 | 5.3 | 841 | 569 | 0.0000177 |
| hotpot_type | comparison | llm_decision_router | 105 | 0.105 | 0.019 | 0.190 | 561.2 | 397.7 | 42.7 | 6.7 | 1837 | 1537 | 0.0000775 |
| wiki_type | bridge_comparison | llm_only | 96 | -0.312 | -0.448 | -0.177 | 70.2 | 67.0 | 23.5 | 6.1 | 898 | 344 | 0.0000188 |
| wiki_type | bridge_comparison | always_rag | 96 | 0.042 | -0.083 | 0.167 | 852.2 | 549.4 | 20.7 | 5.4 | 916 | 2245 | 0.0000956 |
| wiki_type | bridge_comparison | oracle | 96 | -0.156 | -0.281 | -0.031 | 310.6 | 147.8 | 22.5 | 6.1 | 900 | 667 | 0.0000423 |
| wiki_type | bridge_comparison | llm_decision_router | 96 | 0.000 | -0.125 | 0.125 | 828.6 | 581.6 | 78.3 | 8.4 | 1948 | 2329 | 0.0001220 |
| wiki_type | comparison | llm_only | 137 | 0.015 | -0.109 | 0.131 | 66.9 | 63.8 | 17.2 | 6.0 | 884 | 330 | 0.0000153 |
| wiki_type | comparison | always_rag | 137 | 0.197 | 0.109 | 0.285 | 903.6 | 588.9 | 11.2 | 5.2 | 872 | 2408 | 0.0000960 |
| wiki_type | comparison | oracle | 137 | 0.190 | 0.109 | 0.270 | 433.2 | 201.6 | 14.7 | 5.9 | 877 | 889 | 0.0000506 |
| wiki_type | comparison | llm_decision_router | 137 | 0.190 | 0.102 | 0.277 | 868.2 | 606.2 | 56.6 | 11.7 | 1834 | 2584 | 0.0001151 |
| wiki_type | compositional | llm_only | 205 | 0.068 | 0.020 | 0.117 | 60.7 | 61.1 | 25.6 | 6.7 | 925 | 359 | 0.0000189 |
| wiki_type | compositional | always_rag | 205 | 0.088 | 0.044 | 0.132 | 1212.1 | 796.3 | 17.3 | 4.8 | 971 | 3185 | 0.0001298 |
| wiki_type | compositional | oracle | 205 | 0.107 | 0.054 | 0.161 | 241.5 | 145.9 | 24.2 | 6.4 | 911 | 694 | 0.0000363 |
| wiki_type | compositional | llm_decision_router | 205 | 0.083 | 0.044 | 0.127 | 1227.4 | 856.4 | 39.1 | 13.0 | 1872 | 3610 | 0.0001423 |
| wiki_type | inference | llm_only | 62 | 0.097 | 0.032 | 0.177 | 65.4 | 60.6 | 28.4 | 10.9 | 917 | 532 | 0.0000208 |
| wiki_type | inference | always_rag | 62 | 0.161 | 0.065 | 0.258 | 1343.0 | 880.4 | 30.1 | 7.4 | 966 | 3674 | 0.0001494 |
| wiki_type | inference | oracle | 62 | 0.194 | 0.097 | 0.306 | 276.3 | 111.5 | 27.8 | 11.0 | 931 | 739 | 0.0000415 |
| wiki_type | inference | llm_decision_router | 62 | 0.161 | 0.065 | 0.258 | 1391.5 | 940.0 | 70.6 | 10.1 | 1952 | 3887 | 0.0001744 |
| hop_type | multi | llm_only | 1500 | 0.087 | 0.065 | 0.110 | 67.7 | 54.6 | 34.4 | 3.8 | 954 | 717 | 0.0000240 |
| hop_type | multi | always_rag | 1500 | 0.073 | 0.053 | 0.093 | 945.1 | 630.7 | 21.8 | 3.7 | 946 | 4332 | 0.0001054 |
| hop_type | multi | oracle | 1500 | 0.098 | 0.077 | 0.119 | 221.5 | 145.6 | 32.2 | 3.9 | 949 | 1299 | 0.0000383 |
| hop_type | multi | llm_decision_router | 1500 | 0.064 | 0.044 | 0.085 | 927.4 | 676.1 | 61.2 | 4.7 | 1898 | 4771 | 0.0001234 |
| hop_type | single | llm_only | 1500 | 0.269 | 0.245 | 0.293 | 56.8 | 47.8 | 16.7 | 3.6 | 913 | 932 | 0.0000140 |
| hop_type | single | always_rag | 1500 | 0.091 | 0.073 | 0.109 | 1216.7 | 804.8 | 12.4 | 3.7 | 1045 | 5141 | 0.0001279 |
| hop_type | single | oracle | 1500 | 0.143 | 0.123 | 0.163 | 211.4 | 245.8 | 15.6 | 3.7 | 920 | 2042 | 0.0000290 |
| hop_type | single | llm_decision_router | 1500 | 0.101 | 0.081 | 0.120 | 1118.7 | 802.3 | 46.0 | 4.7 | 1960 | 5421 | 0.0001349 |
| pop_tertile | high | llm_only | 167 | 0.317 | 0.246 | 0.395 | 51.0 | 43.3 | 19.3 | 3.4 | 892 | 763 | 0.0000148 |
| pop_tertile | high | always_rag | 167 | 0.066 | 0.024 | 0.114 | 1206.9 | 790.5 | 10.8 | 3.8 | 869 | 4955 | 0.0001261 |
| pop_tertile | high | oracle | 167 | 0.198 | 0.132 | 0.263 | 128.4 | 187.0 | 18.5 | 3.5 | 888 | 1596 | 0.0000221 |
| pop_tertile | high | llm_decision_router | 167 | 0.090 | 0.042 | 0.138 | 1102.9 | 817.8 | 45.4 | 4.7 | 1817 | 5406 | 0.0001330 |
| pop_tertile | low | llm_only | 167 | 0.036 | -0.024 | 0.096 | 52.1 | 44.3 | 24.5 | 3.2 | 916 | 766 | 0.0000174 |
| pop_tertile | low | always_rag | 167 | 0.006 | -0.036 | 0.048 | 1230.1 | 822.1 | 13.7 | 3.4 | 876 | 5106 | 0.0001299 |
| pop_tertile | low | oracle | 167 | 0.012 | -0.030 | 0.054 | 381.5 | 280.9 | 21.9 | 3.2 | 908 | 2145 | 0.0000491 |
| pop_tertile | low | llm_decision_router | 167 | 0.000 | -0.042 | 0.042 | 1258.6 | 864.4 | 64.1 | 4.4 | 1892 | 5649 | 0.0001579 |
| pop_tertile | mid | llm_only | 166 | 0.145 | 0.078 | 0.211 | 51.7 | 43.7 | 21.8 | 3.5 | 912 | 778 | 0.0000161 |
| pop_tertile | mid | always_rag | 166 | 0.012 | -0.018 | 0.042 | 1208.4 | 797.3 | 13.6 | 3.4 | 865 | 5059 | 0.0001276 |
| pop_tertile | mid | oracle | 166 | 0.090 | 0.048 | 0.139 | 289.0 | 244.9 | 20.0 | 3.5 | 901 | 1942 | 0.0000389 |
| pop_tertile | mid | llm_decision_router | 166 | 0.024 | -0.006 | 0.060 | 1205.0 | 825.0 | 59.9 | 4.4 | 1855 | 5512 | 0.0001505 |
| musique_hops | 2.0 | llm_only | 251 | 0.135 | 0.088 | 0.183 | 62.2 | 51.4 | 36.6 | 3.9 | 964 | 650 | 0.0000245 |
| musique_hops | 2.0 | always_rag | 251 | 0.120 | 0.076 | 0.167 | 1016.4 | 670.7 | 22.8 | 3.4 | 941 | 4456 | 0.0001130 |
| musique_hops | 2.0 | oracle | 251 | 0.199 | 0.143 | 0.255 | 205.5 | 104.1 | 35.2 | 4.0 | 964 | 989 | 0.0000381 |
| musique_hops | 2.0 | llm_decision_router | 251 | 0.116 | 0.072 | 0.163 | 999.3 | 716.3 | 65.6 | 4.4 | 1901 | 4905 | 0.0001327 |
| musique_hops | 3.0 | llm_only | 155 | 0.129 | 0.077 | 0.181 | 73.7 | 59.9 | 62.5 | 3.5 | 1057 | 689 | 0.0000386 |
| musique_hops | 3.0 | always_rag | 155 | 0.071 | 0.019 | 0.129 | 1077.9 | 723.0 | 36.3 | 3.6 | 1024 | 4723 | 0.0001260 |
| musique_hops | 3.0 | oracle | 155 | 0.116 | 0.058 | 0.174 | 148.8 | 125.4 | 58.4 | 3.6 | 1049 | 1080 | 0.0000441 |
| musique_hops | 3.0 | llm_decision_router | 155 | 0.071 | 0.019 | 0.129 | 1086.8 | 781.0 | 88.1 | 4.6 | 2011 | 5245 | 0.0001527 |
| musique_hops | 4.0 | llm_only | 94 | 0.085 | 0.032 | 0.149 | 79.5 | 64.2 | 89.3 | 3.7 | 1199 | 753 | 0.0000526 |
| musique_hops | 4.0 | always_rag | 94 | 0.064 | 0.011 | 0.128 | 1046.3 | 706.1 | 53.8 | 3.7 | 1037 | 4734 | 0.0001315 |
| musique_hops | 4.0 | oracle | 94 | 0.117 | 0.053 | 0.191 | 157.2 | 92.4 | 86.8 | 3.7 | 1186 | 919 | 0.0000591 |
| musique_hops | 4.0 | llm_decision_router | 94 | 0.064 | 0.011 | 0.128 | 1114.7 | 768.3 | 118.8 | 4.7 | 2105 | 5296 | 0.0001709 |
| hotpot_type | bridge | llm_only | 395 | 0.157 | 0.116 | 0.197 | 70.8 | 57.0 | 29.2 | 3.8 | 940 | 772 | 0.0000217 |
| hotpot_type | bridge | always_rag | 395 | 0.073 | 0.038 | 0.111 | 728.7 | 483.5 | 15.8 | 3.6 | 918 | 3358 | 0.0000808 |
| hotpot_type | bridge | oracle | 395 | 0.111 | 0.073 | 0.152 | 188.6 | 156.8 | 25.9 | 3.9 | 932 | 1391 | 0.0000318 |
| hotpot_type | bridge | llm_decision_router | 395 | 0.058 | 0.020 | 0.096 | 688.0 | 537.1 | 46.7 | 4.6 | 1835 | 3841 | 0.0000921 |
| hotpot_type | comparison | llm_only | 105 | 0.181 | 0.086 | 0.276 | 64.3 | 50.4 | 11.7 | 3.8 | 836 | 704 | 0.0000123 |
| hotpot_type | comparison | always_rag | 105 | 0.019 | -0.067 | 0.105 | 685.2 | 456.9 | 10.6 | 3.0 | 925 | 3154 | 0.0000738 |
| hotpot_type | comparison | oracle | 105 | 0.057 | -0.010 | 0.133 | 119.8 | 132.7 | 11.4 | 3.6 | 841 | 1203 | 0.0000177 |
| hotpot_type | comparison | llm_decision_router | 105 | 0.019 | -0.067 | 0.105 | 561.2 | 450.4 | 42.7 | 4.3 | 1837 | 3278 | 0.0000775 |
| wiki_type | bridge_comparison | llm_only | 96 | -0.177 | -0.312 | -0.042 | 70.2 | 56.1 | 23.5 | 4.0 | 898 | 752 | 0.0000188 |
| wiki_type | bridge_comparison | always_rag | 96 | -0.021 | -0.135 | 0.104 | 852.2 | 561.6 | 20.7 | 4.2 | 916 | 4119 | 0.0000956 |
| wiki_type | bridge_comparison | oracle | 96 | -0.135 | -0.250 | -0.010 | 310.6 | 177.4 | 22.5 | 4.2 | 900 | 1494 | 0.0000423 |
| wiki_type | bridge_comparison | llm_decision_router | 96 | -0.031 | -0.146 | 0.083 | 828.6 | 615.8 | 78.3 | 5.2 | 1948 | 4601 | 0.0001220 |
| wiki_type | comparison | llm_only | 137 | -0.022 | -0.139 | 0.088 | 66.9 | 52.5 | 17.2 | 4.2 | 884 | 734 | 0.0000153 |
| wiki_type | comparison | always_rag | 137 | 0.102 | 0.029 | 0.182 | 903.6 | 605.1 | 11.2 | 4.2 | 872 | 4412 | 0.0000960 |
| wiki_type | comparison | oracle | 137 | 0.066 | -0.007 | 0.139 | 433.2 | 238.7 | 14.7 | 4.4 | 877 | 1984 | 0.0000506 |
| wiki_type | comparison | llm_decision_router | 137 | 0.073 | -0.007 | 0.153 | 868.2 | 629.2 | 56.6 | 5.3 | 1834 | 4698 | 0.0001151 |
| wiki_type | compositional | llm_only | 205 | 0.020 | -0.029 | 0.068 | 60.7 | 50.2 | 25.6 | 3.0 | 925 | 662 | 0.0000189 |
| wiki_type | compositional | always_rag | 205 | 0.039 | -0.010 | 0.088 | 1212.1 | 815.2 | 17.3 | 2.9 | 971 | 5570 | 0.0001298 |
| wiki_type | compositional | oracle | 205 | 0.054 | -0.005 | 0.112 | 241.5 | 151.3 | 24.2 | 3.2 | 911 | 1327 | 0.0000363 |
| wiki_type | compositional | llm_decision_router | 205 | 0.034 | -0.015 | 0.083 | 1227.4 | 863.4 | 39.1 | 3.9 | 1872 | 6032 | 0.0001423 |
| wiki_type | inference | llm_only | 62 | 0.065 | 0.000 | 0.145 | 65.4 | 49.4 | 28.4 | 5.2 | 917 | 771 | 0.0000208 |
| wiki_type | inference | always_rag | 62 | 0.177 | 0.081 | 0.274 | 1343.0 | 910.3 | 30.1 | 6.8 | 966 | 6505 | 0.0001494 |
| wiki_type | inference | oracle | 62 | 0.177 | 0.081 | 0.274 | 276.3 | 122.8 | 27.8 | 5.1 | 931 | 1348 | 0.0000415 |
| wiki_type | inference | llm_decision_router | 62 | 0.177 | 0.081 | 0.274 | 1391.5 | 957.7 | 70.6 | 7.8 | 1952 | 6950 | 0.0001744 |
| hop_type | multi | llm_only | 1500 | 0.179 | 0.156 | 0.203 | 44.5 | 51.4 | 3.6 | 2.6 | 906 | 315 | 0.0000088 |
| hop_type | multi | always_rag | 1500 | 0.169 | 0.147 | 0.191 | 584.7 | 610.9 | 3.9 | 2.9 | 843 | 2209 | 0.0000891 |
| hop_type | multi | oracle | 1500 | 0.188 | 0.165 | 0.211 | 123.4 | 120.9 | 3.7 | 2.6 | 898 | 549 | 0.0000207 |
| hop_type | multi | llm_decision_router | 1500 | 0.157 | 0.135 | 0.179 | 554.2 | 658.8 | 4.9 | 3.9 | 1691 | 2564 | 0.0000852 |
| hop_type | single | llm_only | 1500 | 0.413 | 0.388 | 0.439 | 38.0 | 44.5 | 3.2 | 2.4 | 865 | 208 | 0.0000076 |
| hop_type | single | always_rag | 1500 | 0.192 | 0.171 | 0.213 | 763.2 | 783.4 | 3.5 | 2.9 | 917 | 2854 | 0.0001151 |
| hop_type | single | oracle | 1500 | 0.251 | 0.228 | 0.274 | 111.3 | 242.0 | 3.2 | 2.6 | 867 | 922 | 0.0000186 |
| hop_type | single | llm_decision_router | 1500 | 0.201 | 0.179 | 0.223 | 595.6 | 817.4 | 4.4 | 4.0 | 1725 | 3159 | 0.0000906 |
| pop_tertile | high | llm_only | 167 | 0.431 | 0.359 | 0.509 | 33.3 | 40.0 | 3.0 | 2.2 | 858 | 185 | 0.0000068 |
| pop_tertile | high | always_rag | 167 | 0.114 | 0.060 | 0.174 | 752.1 | 768.6 | 3.5 | 2.6 | 883 | 2547 | 0.0001103 |
| pop_tertile | high | oracle | 167 | 0.281 | 0.216 | 0.347 | 73.6 | 193.5 | 3.0 | 2.3 | 863 | 703 | 0.0000129 |
| pop_tertile | high | llm_decision_router | 167 | 0.120 | 0.066 | 0.180 | 643.2 | 781.3 | 4.5 | 3.6 | 1699 | 2788 | 0.0000945 |
| pop_tertile | low | llm_only | 167 | 0.269 | 0.198 | 0.341 | 34.3 | 41.1 | 3.4 | 2.1 | 874 | 181 | 0.0000072 |
| pop_tertile | low | always_rag | 167 | 0.102 | 0.054 | 0.150 | 777.3 | 798.4 | 3.4 | 2.6 | 901 | 2630 | 0.0001127 |
| pop_tertile | low | oracle | 167 | 0.156 | 0.096 | 0.216 | 167.0 | 267.5 | 3.4 | 2.3 | 866 | 945 | 0.0000271 |
| pop_tertile | low | llm_decision_router | 167 | 0.102 | 0.054 | 0.150 | 755.6 | 837.4 | 4.4 | 3.7 | 1730 | 2964 | 0.0001106 |
| pop_tertile | mid | llm_only | 166 | 0.289 | 0.211 | 0.367 | 33.8 | 40.5 | 3.2 | 2.4 | 877 | 189 | 0.0000070 |
| pop_tertile | mid | always_rag | 166 | 0.084 | 0.036 | 0.133 | 759.6 | 776.0 | 3.8 | 2.9 | 887 | 2644 | 0.0001137 |
| pop_tertile | mid | oracle | 166 | 0.169 | 0.090 | 0.241 | 124.0 | 226.4 | 3.3 | 2.5 | 883 | 832 | 0.0000206 |
| pop_tertile | mid | llm_decision_router | 166 | 0.090 | 0.036 | 0.151 | 706.8 | 814.5 | 4.7 | 4.0 | 1715 | 2975 | 0.0001064 |
| musique_hops | 2.0 | llm_only | 251 | 0.112 | 0.064 | 0.163 | 41.3 | 48.2 | 3.5 | 2.3 | 913 | 347 | 0.0000083 |
| musique_hops | 2.0 | always_rag | 251 | 0.159 | 0.112 | 0.211 | 624.6 | 651.6 | 3.6 | 2.8 | 840 | 2388 | 0.0000952 |
| musique_hops | 2.0 | oracle | 251 | 0.199 | 0.143 | 0.255 | 125.7 | 77.4 | 3.5 | 2.4 | 900 | 443 | 0.0000208 |
| musique_hops | 2.0 | llm_decision_router | 251 | 0.147 | 0.100 | 0.195 | 623.7 | 697.8 | 4.6 | 3.9 | 1697 | 2744 | 0.0000956 |
| musique_hops | 3.0 | llm_only | 155 | 0.090 | 0.039 | 0.142 | 49.8 | 56.8 | 3.4 | 2.5 | 891 | 364 | 0.0000095 |
| musique_hops | 3.0 | always_rag | 155 | 0.084 | 0.032 | 0.142 | 672.4 | 705.1 | 4.1 | 2.4 | 844 | 2505 | 0.0001003 |
| musique_hops | 3.0 | oracle | 155 | 0.123 | 0.058 | 0.187 | 90.9 | 88.1 | 3.4 | 2.5 | 886 | 463 | 0.0000157 |
| musique_hops | 3.0 | llm_decision_router | 155 | 0.084 | 0.032 | 0.142 | 713.9 | 759.8 | 5.1 | 3.4 | 1697 | 2880 | 0.0001071 |
| musique_hops | 4.0 | llm_only | 94 | 0.043 | 0.011 | 0.085 | 54.1 | 61.1 | 3.5 | 2.3 | 905 | 381 | 0.0000102 |
| musique_hops | 4.0 | always_rag | 94 | 0.043 | -0.011 | 0.106 | 653.5 | 686.0 | 4.0 | 2.7 | 838 | 2464 | 0.0000980 |
| musique_hops | 4.0 | oracle | 94 | 0.043 | -0.011 | 0.106 | 74.8 | 94.0 | 3.5 | 2.3 | 909 | 496 | 0.0000133 |
| musique_hops | 4.0 | llm_decision_router | 94 | 0.043 | -0.011 | 0.106 | 706.6 | 745.1 | 5.0 | 3.8 | 1698 | 2855 | 0.0001066 |
| hotpot_type | bridge | llm_only | 395 | 0.220 | 0.175 | 0.266 | 46.5 | 53.6 | 3.4 | 2.7 | 903 | 283 | 0.0000090 |
| hotpot_type | bridge | always_rag | 395 | 0.165 | 0.127 | 0.205 | 445.6 | 467.4 | 3.8 | 3.0 | 845 | 1671 | 0.0000691 |
| hotpot_type | bridge | oracle | 395 | 0.235 | 0.190 | 0.281 | 119.1 | 124.0 | 3.5 | 2.7 | 893 | 514 | 0.0000200 |
| hotpot_type | bridge | llm_decision_router | 395 | 0.152 | 0.111 | 0.195 | 412.7 | 519.1 | 4.8 | 4.0 | 1685 | 2037 | 0.0000648 |
| hotpot_type | comparison | llm_only | 105 | 0.314 | 0.200 | 0.419 | 40.5 | 47.0 | 2.8 | 2.3 | 871 | 229 | 0.0000077 |
| hotpot_type | comparison | always_rag | 105 | 0.190 | 0.114 | 0.276 | 419.2 | 440.8 | 2.8 | 2.4 | 872 | 1536 | 0.0000645 |
| hotpot_type | comparison | oracle | 105 | 0.105 | 0.029 | 0.181 | 54.5 | 149.7 | 2.8 | 2.4 | 870 | 565 | 0.0000098 |
| hotpot_type | comparison | llm_decision_router | 105 | 0.152 | 0.067 | 0.238 | 256.9 | 467.5 | 3.9 | 3.4 | 1662 | 1821 | 0.0000409 |
| wiki_type | bridge_comparison | llm_only | 96 | 0.240 | 0.115 | 0.365 | 46.1 | 52.9 | 4.1 | 3.5 | 942 | 321 | 0.0000094 |
| wiki_type | bridge_comparison | always_rag | 96 | 0.208 | 0.094 | 0.323 | 522.0 | 541.6 | 4.5 | 3.8 | 851 | 1999 | 0.0000810 |
| wiki_type | bridge_comparison | oracle | 96 | 0.146 | 0.031 | 0.260 | 161.5 | 198.3 | 4.4 | 3.7 | 936 | 814 | 0.0000268 |
| wiki_type | bridge_comparison | llm_decision_router | 96 | 0.188 | 0.073 | 0.302 | 398.7 | 592.5 | 5.5 | 4.8 | 1729 | 2351 | 0.0000631 |
| wiki_type | comparison | llm_only | 137 | 0.372 | 0.255 | 0.482 | 42.6 | 49.0 | 4.0 | 3.5 | 902 | 320 | 0.0000088 |
| wiki_type | comparison | always_rag | 137 | 0.270 | 0.182 | 0.365 | 558.8 | 582.9 | 4.1 | 3.7 | 833 | 2151 | 0.0000863 |
| wiki_type | comparison | oracle | 137 | 0.226 | 0.146 | 0.307 | 146.5 | 236.5 | 4.2 | 3.6 | 896 | 958 | 0.0000245 |
| wiki_type | comparison | llm_decision_router | 137 | 0.248 | 0.161 | 0.343 | 427.6 | 627.0 | 5.0 | 4.7 | 1726 | 2489 | 0.0000672 |
| wiki_type | compositional | llm_only | 205 | 0.088 | 0.039 | 0.137 | 40.0 | 47.2 | 2.9 | 1.8 | 916 | 299 | 0.0000077 |
| wiki_type | compositional | always_rag | 205 | 0.195 | 0.141 | 0.254 | 761.6 | 790.5 | 3.3 | 2.2 | 829 | 2847 | 0.0001139 |
| wiki_type | compositional | oracle | 205 | 0.190 | 0.132 | 0.249 | 155.8 | 91.2 | 3.0 | 1.8 | 905 | 459 | 0.0000250 |
| wiki_type | compositional | llm_decision_router | 205 | 0.185 | 0.132 | 0.239 | 784.9 | 835.7 | 4.3 | 3.2 | 1667 | 3195 | 0.0001180 |
| wiki_type | inference | llm_only | 62 | 0.177 | 0.081 | 0.274 | 39.2 | 46.7 | 7.6 | 3.2 | 926 | 352 | 0.0000104 |
| wiki_type | inference | always_rag | 62 | 0.226 | 0.113 | 0.355 | 834.5 | 874.4 | 7.0 | 3.9 | 844 | 3275 | 0.0001294 |
| wiki_type | inference | oracle | 62 | 0.339 | 0.226 | 0.468 | 196.7 | 74.7 | 8.3 | 3.3 | 915 | 452 | 0.0000345 |
| wiki_type | inference | llm_decision_router | 62 | 0.258 | 0.145 | 0.387 | 806.5 | 919.1 | 7.6 | 4.9 | 1667 | 3624 | 0.0001256 |
| hop_type | multi | llm_only | 1500 | 0.137 | 0.115 | 0.160 | 44.5 | 65.5 | 3.6 | 6.4 | 906 | 365 | 0.0000088 |
| hop_type | multi | always_rag | 1500 | 0.137 | 0.117 | 0.159 | 584.7 | 614.1 | 3.9 | 4.8 | 843 | 2477 | 0.0000891 |
| hop_type | multi | oracle | 1500 | 0.153 | 0.131 | 0.175 | 123.4 | 131.1 | 3.7 | 6.1 | 898 | 617 | 0.0000207 |
| hop_type | multi | llm_decision_router | 1500 | 0.136 | 0.115 | 0.157 | 554.2 | 639.3 | 4.9 | 8.7 | 1691 | 2589 | 0.0000852 |
| hop_type | single | llm_only | 1500 | 0.292 | 0.267 | 0.316 | 38.0 | 58.9 | 3.2 | 5.1 | 865 | 310 | 0.0000076 |
| hop_type | single | always_rag | 1500 | 0.131 | 0.113 | 0.151 | 763.2 | 792.0 | 3.5 | 4.5 | 917 | 3267 | 0.0001151 |
| hop_type | single | oracle | 1500 | 0.177 | 0.157 | 0.198 | 111.3 | 218.8 | 3.2 | 5.0 | 867 | 962 | 0.0000186 |
| hop_type | single | llm_decision_router | 1500 | 0.155 | 0.135 | 0.175 | 595.6 | 636.0 | 4.4 | 6.8 | 1725 | 2584 | 0.0000906 |
| pop_tertile | high | llm_only | 167 | 0.329 | 0.257 | 0.407 | 33.3 | 54.3 | 3.0 | 4.8 | 858 | 293 | 0.0000068 |
| pop_tertile | high | always_rag | 167 | 0.072 | 0.030 | 0.120 | 752.1 | 780.0 | 3.5 | 4.3 | 883 | 3153 | 0.0001103 |
| pop_tertile | high | oracle | 167 | 0.234 | 0.168 | 0.305 | 73.6 | 166.3 | 3.0 | 4.6 | 863 | 733 | 0.0000129 |
| pop_tertile | high | llm_decision_router | 167 | 0.090 | 0.042 | 0.144 | 643.2 | 685.6 | 4.5 | 6.4 | 1699 | 2743 | 0.0000945 |
| pop_tertile | low | llm_only | 167 | 0.263 | 0.192 | 0.335 | 34.3 | 55.4 | 3.4 | 5.5 | 874 | 319 | 0.0000072 |
| pop_tertile | low | always_rag | 167 | 0.078 | 0.036 | 0.126 | 777.3 | 809.0 | 3.4 | 4.8 | 901 | 3285 | 0.0001127 |
| pop_tertile | low | oracle | 167 | 0.144 | 0.090 | 0.204 | 167.0 | 285.3 | 3.4 | 5.1 | 866 | 1252 | 0.0000271 |
| pop_tertile | low | llm_decision_router | 167 | 0.078 | 0.036 | 0.126 | 755.6 | 850.1 | 4.4 | 7.5 | 1730 | 3439 | 0.0001106 |
| pop_tertile | mid | llm_only | 166 | 0.247 | 0.175 | 0.319 | 33.8 | 54.8 | 3.2 | 4.8 | 877 | 294 | 0.0000070 |
| pop_tertile | mid | always_rag | 166 | 0.054 | 0.018 | 0.096 | 759.6 | 789.2 | 3.8 | 4.3 | 887 | 3216 | 0.0001137 |
| pop_tertile | mid | oracle | 166 | 0.145 | 0.084 | 0.205 | 124.0 | 225.2 | 3.3 | 4.7 | 883 | 990 | 0.0000206 |
| pop_tertile | mid | llm_decision_router | 166 | 0.072 | 0.030 | 0.120 | 706.8 | 811.1 | 4.7 | 6.5 | 1715 | 3272 | 0.0001064 |
| musique_hops | 2.0 | llm_only | 251 | 0.104 | 0.056 | 0.151 | 41.3 | 62.4 | 3.5 | 5.8 | 913 | 330 | 0.0000083 |
| musique_hops | 2.0 | always_rag | 251 | 0.143 | 0.096 | 0.195 | 624.6 | 652.7 | 3.6 | 4.9 | 840 | 2652 | 0.0000952 |
| musique_hops | 2.0 | oracle | 251 | 0.179 | 0.127 | 0.235 | 125.7 | 100.3 | 3.5 | 5.6 | 900 | 472 | 0.0000208 |
| musique_hops | 2.0 | llm_decision_router | 251 | 0.127 | 0.080 | 0.179 | 623.7 | 670.3 | 4.6 | 7.8 | 1697 | 2697 | 0.0000956 |
| musique_hops | 3.0 | llm_only | 155 | 0.090 | 0.039 | 0.148 | 49.8 | 70.8 | 3.4 | 6.9 | 891 | 401 | 0.0000095 |
| musique_hops | 3.0 | always_rag | 155 | 0.065 | 0.032 | 0.110 | 672.4 | 699.8 | 4.1 | 4.1 | 844 | 2777 | 0.0001003 |
| musique_hops | 3.0 | oracle | 155 | 0.103 | 0.045 | 0.161 | 90.9 | 107.1 | 3.4 | 6.8 | 886 | 543 | 0.0000157 |
| musique_hops | 3.0 | llm_decision_router | 155 | 0.065 | 0.032 | 0.110 | 713.9 | 769.6 | 5.1 | 7.9 | 1697 | 3059 | 0.0001071 |
| musique_hops | 4.0 | llm_only | 94 | 0.043 | 0.011 | 0.085 | 54.1 | 75.1 | 3.5 | 7.1 | 905 | 444 | 0.0000102 |
| musique_hops | 4.0 | always_rag | 94 | 0.074 | 0.032 | 0.128 | 653.5 | 681.5 | 4.0 | 4.3 | 838 | 2682 | 0.0000980 |
| musique_hops | 4.0 | oracle | 94 | 0.074 | 0.032 | 0.128 | 74.8 | 79.8 | 3.5 | 7.1 | 909 | 461 | 0.0000133 |
| musique_hops | 4.0 | llm_decision_router | 94 | 0.074 | 0.032 | 0.128 | 706.6 | 755.6 | 5.0 | 7.1 | 1698 | 2956 | 0.0001066 |
| hotpot_type | bridge | llm_only | 395 | 0.185 | 0.142 | 0.228 | 46.5 | 67.5 | 3.4 | 6.1 | 903 | 362 | 0.0000090 |
| hotpot_type | bridge | always_rag | 395 | 0.139 | 0.099 | 0.180 | 445.6 | 472.4 | 3.8 | 4.8 | 845 | 1916 | 0.0000691 |
| hotpot_type | bridge | oracle | 395 | 0.192 | 0.147 | 0.238 | 119.1 | 139.5 | 3.5 | 5.4 | 893 | 622 | 0.0000200 |
| hotpot_type | bridge | llm_decision_router | 395 | 0.159 | 0.116 | 0.203 | 412.7 | 470.5 | 4.8 | 7.2 | 1685 | 1858 | 0.0000648 |
| hotpot_type | comparison | llm_only | 105 | 0.200 | 0.114 | 0.286 | 40.5 | 61.6 | 2.8 | 5.4 | 871 | 310 | 0.0000077 |
| hotpot_type | comparison | always_rag | 105 | 0.105 | 0.029 | 0.181 | 419.2 | 447.2 | 2.8 | 4.1 | 872 | 1757 | 0.0000645 |
| hotpot_type | comparison | oracle | 105 | 0.048 | -0.010 | 0.114 | 54.5 | 129.4 | 2.8 | 5.3 | 870 | 569 | 0.0000098 |
| hotpot_type | comparison | llm_decision_router | 105 | 0.124 | 0.048 | 0.210 | 256.9 | 397.7 | 3.9 | 6.7 | 1662 | 1537 | 0.0000409 |
| wiki_type | bridge_comparison | llm_only | 96 | -0.010 | -0.167 | 0.146 | 46.1 | 67.0 | 4.1 | 6.1 | 942 | 344 | 0.0000094 |
| wiki_type | bridge_comparison | always_rag | 96 | 0.188 | 0.062 | 0.312 | 522.0 | 549.4 | 4.5 | 5.4 | 851 | 2245 | 0.0000810 |
| wiki_type | bridge_comparison | oracle | 96 | 0.062 | -0.052 | 0.177 | 161.5 | 147.8 | 4.4 | 6.1 | 936 | 667 | 0.0000268 |
| wiki_type | bridge_comparison | llm_decision_router | 96 | 0.135 | 0.010 | 0.260 | 398.7 | 581.6 | 5.5 | 8.4 | 1729 | 2329 | 0.0000631 |
| wiki_type | comparison | llm_only | 137 | 0.285 | 0.182 | 0.387 | 42.6 | 63.8 | 4.0 | 6.0 | 902 | 330 | 0.0000088 |
| wiki_type | comparison | always_rag | 137 | 0.219 | 0.124 | 0.314 | 558.8 | 588.9 | 4.1 | 5.2 | 833 | 2408 | 0.0000863 |
| wiki_type | comparison | oracle | 137 | 0.204 | 0.124 | 0.292 | 146.5 | 201.6 | 4.2 | 5.9 | 896 | 889 | 0.0000245 |
| wiki_type | comparison | llm_decision_router | 137 | 0.197 | 0.102 | 0.292 | 427.6 | 606.2 | 5.0 | 11.7 | 1726 | 2584 | 0.0000672 |
| wiki_type | compositional | llm_only | 205 | 0.093 | 0.044 | 0.141 | 40.0 | 61.1 | 2.9 | 6.7 | 916 | 359 | 0.0000077 |
| wiki_type | compositional | always_rag | 205 | 0.137 | 0.088 | 0.190 | 761.6 | 796.3 | 3.3 | 4.8 | 829 | 3185 | 0.0001139 |
| wiki_type | compositional | oracle | 205 | 0.141 | 0.083 | 0.200 | 155.8 | 145.9 | 3.0 | 6.4 | 905 | 694 | 0.0000250 |
| wiki_type | compositional | llm_decision_router | 205 | 0.127 | 0.078 | 0.180 | 784.9 | 856.4 | 4.3 | 13.0 | 1667 | 3610 | 0.0001180 |
| wiki_type | inference | llm_only | 62 | 0.177 | 0.081 | 0.274 | 39.2 | 60.6 | 7.6 | 10.9 | 926 | 532 | 0.0000104 |
| wiki_type | inference | always_rag | 62 | 0.177 | 0.081 | 0.274 | 834.5 | 880.4 | 7.0 | 7.4 | 844 | 3674 | 0.0001294 |
| wiki_type | inference | oracle | 62 | 0.290 | 0.177 | 0.403 | 196.7 | 111.5 | 8.3 | 11.0 | 915 | 739 | 0.0000345 |
| wiki_type | inference | llm_decision_router | 62 | 0.210 | 0.113 | 0.323 | 806.5 | 940.0 | 7.6 | 10.1 | 1667 | 3887 | 0.0001256 |
| hop_type | multi | llm_only | 1500 | 0.139 | 0.117 | 0.162 | 44.5 | 54.6 | 3.6 | 3.8 | 906 | 717 | 0.0000088 |
| hop_type | multi | always_rag | 1500 | 0.091 | 0.072 | 0.111 | 584.7 | 630.7 | 3.9 | 3.7 | 843 | 4332 | 0.0000891 |
| hop_type | multi | oracle | 1500 | 0.116 | 0.095 | 0.137 | 123.4 | 145.6 | 3.7 | 3.9 | 898 | 1299 | 0.0000207 |
| hop_type | multi | llm_decision_router | 1500 | 0.078 | 0.058 | 0.099 | 554.2 | 676.1 | 4.9 | 4.7 | 1691 | 4771 | 0.0000852 |
| hop_type | single | llm_only | 1500 | 0.317 | 0.291 | 0.342 | 38.0 | 47.8 | 3.2 | 3.6 | 865 | 932 | 0.0000076 |
| hop_type | single | always_rag | 1500 | 0.099 | 0.081 | 0.118 | 763.2 | 804.8 | 3.5 | 3.7 | 917 | 5141 | 0.0001151 |
| hop_type | single | oracle | 1500 | 0.160 | 0.139 | 0.181 | 111.3 | 245.8 | 3.2 | 3.7 | 867 | 2042 | 0.0000186 |
| hop_type | single | llm_decision_router | 1500 | 0.109 | 0.089 | 0.129 | 595.6 | 802.3 | 4.4 | 4.7 | 1725 | 5421 | 0.0000906 |
| pop_tertile | high | llm_only | 167 | 0.353 | 0.275 | 0.431 | 33.3 | 43.3 | 3.0 | 3.4 | 858 | 763 | 0.0000068 |
| pop_tertile | high | always_rag | 167 | 0.048 | 0.000 | 0.096 | 752.1 | 790.5 | 3.5 | 3.8 | 883 | 4955 | 0.0001103 |
| pop_tertile | high | oracle | 167 | 0.222 | 0.150 | 0.293 | 73.6 | 187.0 | 3.0 | 3.5 | 863 | 1596 | 0.0000129 |
| pop_tertile | high | llm_decision_router | 167 | 0.060 | 0.006 | 0.114 | 643.2 | 817.8 | 4.5 | 4.7 | 1699 | 5406 | 0.0000945 |
| pop_tertile | low | llm_only | 167 | 0.192 | 0.114 | 0.269 | 34.3 | 44.3 | 3.4 | 3.2 | 874 | 766 | 0.0000072 |
| pop_tertile | low | always_rag | 167 | 0.048 | 0.000 | 0.096 | 777.3 | 822.1 | 3.4 | 3.4 | 901 | 5106 | 0.0001127 |
| pop_tertile | low | oracle | 167 | 0.072 | 0.018 | 0.126 | 167.0 | 280.9 | 3.4 | 3.2 | 866 | 2145 | 0.0000271 |
| pop_tertile | low | llm_decision_router | 167 | 0.048 | 0.000 | 0.096 | 755.6 | 864.4 | 4.4 | 4.4 | 1730 | 5649 | 0.0001106 |
| pop_tertile | mid | llm_only | 166 | 0.241 | 0.169 | 0.313 | 33.8 | 43.7 | 3.2 | 3.5 | 877 | 778 | 0.0000070 |
| pop_tertile | mid | always_rag | 166 | 0.012 | -0.012 | 0.036 | 759.6 | 797.3 | 3.8 | 3.4 | 887 | 5059 | 0.0001137 |
| pop_tertile | mid | oracle | 166 | 0.108 | 0.054 | 0.163 | 124.0 | 244.9 | 3.3 | 3.5 | 883 | 1942 | 0.0000206 |
| pop_tertile | mid | llm_decision_router | 166 | 0.018 | -0.018 | 0.054 | 706.8 | 825.0 | 4.7 | 4.4 | 1715 | 5512 | 0.0001064 |
| musique_hops | 2.0 | llm_only | 251 | 0.112 | 0.068 | 0.159 | 41.3 | 51.4 | 3.5 | 3.9 | 913 | 650 | 0.0000083 |
| musique_hops | 2.0 | always_rag | 251 | 0.108 | 0.064 | 0.155 | 624.6 | 670.7 | 3.6 | 3.4 | 840 | 4456 | 0.0000952 |
| musique_hops | 2.0 | oracle | 251 | 0.159 | 0.108 | 0.211 | 125.7 | 104.1 | 3.5 | 4.0 | 900 | 989 | 0.0000208 |
| musique_hops | 2.0 | llm_decision_router | 251 | 0.096 | 0.048 | 0.143 | 623.7 | 716.3 | 4.6 | 4.4 | 1697 | 4905 | 0.0000956 |
| musique_hops | 3.0 | llm_only | 155 | 0.097 | 0.052 | 0.148 | 49.8 | 59.9 | 3.4 | 3.5 | 891 | 689 | 0.0000095 |
| musique_hops | 3.0 | always_rag | 155 | 0.019 | -0.019 | 0.065 | 672.4 | 723.0 | 4.1 | 3.6 | 844 | 4723 | 0.0001003 |
| musique_hops | 3.0 | oracle | 155 | 0.071 | 0.026 | 0.123 | 90.9 | 125.4 | 3.4 | 3.6 | 886 | 1080 | 0.0000157 |
| musique_hops | 3.0 | llm_decision_router | 155 | 0.019 | -0.019 | 0.065 | 713.9 | 781.0 | 5.1 | 4.6 | 1697 | 5245 | 0.0001071 |
| musique_hops | 4.0 | llm_only | 94 | 0.032 | 0.000 | 0.074 | 54.1 | 64.2 | 3.5 | 3.7 | 905 | 753 | 0.0000102 |
| musique_hops | 4.0 | always_rag | 94 | 0.032 | -0.011 | 0.085 | 653.5 | 706.1 | 4.0 | 3.7 | 838 | 4734 | 0.0000980 |
| musique_hops | 4.0 | oracle | 94 | 0.032 | -0.011 | 0.085 | 74.8 | 92.4 | 3.5 | 3.7 | 909 | 919 | 0.0000133 |
| musique_hops | 4.0 | llm_decision_router | 94 | 0.032 | -0.011 | 0.085 | 706.6 | 768.3 | 5.0 | 4.7 | 1698 | 5296 | 0.0001066 |
| hotpot_type | bridge | llm_only | 395 | 0.197 | 0.154 | 0.241 | 46.5 | 57.0 | 3.4 | 3.8 | 903 | 772 | 0.0000090 |
| hotpot_type | bridge | always_rag | 395 | 0.094 | 0.058 | 0.132 | 445.6 | 483.5 | 3.8 | 3.6 | 845 | 3358 | 0.0000691 |
| hotpot_type | bridge | oracle | 395 | 0.157 | 0.116 | 0.200 | 119.1 | 156.8 | 3.5 | 3.9 | 893 | 1391 | 0.0000200 |
| hotpot_type | bridge | llm_decision_router | 395 | 0.081 | 0.043 | 0.119 | 412.7 | 537.1 | 4.8 | 4.6 | 1685 | 3841 | 0.0000648 |
| hotpot_type | comparison | llm_only | 105 | 0.200 | 0.114 | 0.295 | 40.5 | 50.4 | 2.8 | 3.8 | 871 | 704 | 0.0000077 |
| hotpot_type | comparison | always_rag | 105 | 0.076 | 0.000 | 0.162 | 419.2 | 456.9 | 2.8 | 3.0 | 872 | 3154 | 0.0000645 |
| hotpot_type | comparison | oracle | 105 | 0.038 | -0.029 | 0.114 | 54.5 | 132.7 | 2.8 | 3.6 | 870 | 1203 | 0.0000098 |
| hotpot_type | comparison | llm_decision_router | 105 | 0.038 | -0.048 | 0.124 | 256.9 | 450.4 | 3.9 | 4.3 | 1662 | 3278 | 0.0000409 |
| wiki_type | bridge_comparison | llm_only | 96 | 0.125 | -0.021 | 0.281 | 46.1 | 56.1 | 4.1 | 4.0 | 942 | 752 | 0.0000094 |
| wiki_type | bridge_comparison | always_rag | 96 | 0.125 | -0.010 | 0.260 | 522.0 | 561.6 | 4.5 | 4.2 | 851 | 4119 | 0.0000810 |
| wiki_type | bridge_comparison | oracle | 96 | 0.083 | -0.042 | 0.208 | 161.5 | 177.4 | 4.4 | 4.2 | 936 | 1494 | 0.0000268 |
| wiki_type | bridge_comparison | llm_decision_router | 96 | 0.104 | -0.031 | 0.240 | 398.7 | 615.8 | 5.5 | 5.2 | 1729 | 4601 | 0.0000631 |
| wiki_type | comparison | llm_only | 137 | 0.248 | 0.139 | 0.358 | 42.6 | 52.5 | 4.0 | 4.2 | 902 | 734 | 0.0000088 |
| wiki_type | comparison | always_rag | 137 | 0.124 | 0.051 | 0.204 | 558.8 | 605.1 | 4.1 | 4.2 | 833 | 4412 | 0.0000863 |
| wiki_type | comparison | oracle | 137 | 0.080 | 0.022 | 0.139 | 146.5 | 238.7 | 4.2 | 4.4 | 896 | 1984 | 0.0000245 |
| wiki_type | comparison | llm_decision_router | 137 | 0.080 | 0.000 | 0.161 | 427.6 | 629.2 | 5.0 | 5.3 | 1726 | 4698 | 0.0000672 |
| wiki_type | compositional | llm_only | 205 | 0.044 | -0.005 | 0.093 | 40.0 | 50.2 | 2.9 | 3.0 | 916 | 662 | 0.0000077 |
| wiki_type | compositional | always_rag | 205 | 0.088 | 0.044 | 0.137 | 761.6 | 815.2 | 3.3 | 2.9 | 829 | 5570 | 0.0001139 |
| wiki_type | compositional | oracle | 205 | 0.088 | 0.034 | 0.141 | 155.8 | 151.3 | 3.0 | 3.2 | 905 | 1327 | 0.0000250 |
| wiki_type | compositional | llm_decision_router | 205 | 0.078 | 0.034 | 0.127 | 784.9 | 863.4 | 4.3 | 3.9 | 1667 | 6032 | 0.0001180 |
| wiki_type | inference | llm_only | 62 | 0.145 | 0.065 | 0.242 | 39.2 | 49.4 | 7.6 | 5.2 | 926 | 771 | 0.0000104 |
| wiki_type | inference | always_rag | 62 | 0.194 | 0.097 | 0.290 | 834.5 | 910.3 | 7.0 | 6.8 | 844 | 6505 | 0.0001294 |
| wiki_type | inference | oracle | 62 | 0.274 | 0.161 | 0.387 | 196.7 | 122.8 | 8.3 | 5.1 | 915 | 1348 | 0.0000345 |
| wiki_type | inference | llm_decision_router | 62 | 0.226 | 0.129 | 0.339 | 806.5 | 957.7 | 7.6 | 7.8 | 1667 | 6950 | 0.0001256 |
| hop_type | multi | llm_only | 1500 | -0.042 | -0.061 | -0.023 | 51.4 | 65.5 | 2.6 | 6.4 | 315 | 365 | 0.0000000 |
| hop_type | multi | always_rag | 1500 | -0.031 | -0.049 | -0.013 | 610.9 | 614.1 | 2.9 | 4.8 | 2209 | 2477 | 0.0000000 |
| hop_type | multi | oracle | 1500 | -0.035 | -0.054 | -0.015 | 120.9 | 131.1 | 2.6 | 6.1 | 549 | 617 | 0.0000000 |
| hop_type | multi | llm_decision_router | 1500 | -0.021 | -0.040 | -0.002 | 658.8 | 639.3 | 3.9 | 8.7 | 2564 | 2589 | 0.0000000 |
| hop_type | single | llm_only | 1500 | -0.121 | -0.143 | -0.100 | 44.5 | 58.9 | 2.4 | 5.1 | 208 | 310 | 0.0000000 |
| hop_type | single | always_rag | 1500 | -0.061 | -0.079 | -0.043 | 783.4 | 792.0 | 2.9 | 4.5 | 2854 | 3267 | 0.0000000 |
| hop_type | single | oracle | 1500 | -0.073 | -0.093 | -0.053 | 242.0 | 218.8 | 2.6 | 5.0 | 922 | 962 | 0.0000000 |
| hop_type | single | llm_decision_router | 1500 | -0.046 | -0.067 | -0.025 | 817.4 | 636.0 | 4.0 | 6.8 | 3159 | 2584 | 0.0000000 |
| pop_tertile | high | llm_only | 167 | -0.102 | -0.156 | -0.048 | 40.0 | 54.3 | 2.2 | 4.8 | 185 | 293 | 0.0000000 |
| pop_tertile | high | always_rag | 167 | -0.042 | -0.090 | 0.000 | 768.6 | 780.0 | 2.6 | 4.3 | 2547 | 3153 | 0.0000000 |
| pop_tertile | high | oracle | 167 | -0.048 | -0.102 | 0.000 | 193.5 | 166.3 | 2.3 | 4.6 | 703 | 733 | 0.0000000 |
| pop_tertile | high | llm_decision_router | 167 | -0.030 | -0.078 | 0.012 | 781.3 | 685.6 | 3.6 | 6.4 | 2788 | 2743 | 0.0000000 |
| pop_tertile | low | llm_only | 167 | -0.006 | -0.054 | 0.042 | 41.1 | 55.4 | 2.1 | 5.5 | 181 | 319 | 0.0000000 |
| pop_tertile | low | always_rag | 167 | -0.024 | -0.066 | 0.018 | 798.4 | 809.0 | 2.6 | 4.8 | 2630 | 3285 | 0.0000000 |
| pop_tertile | low | oracle | 167 | -0.012 | -0.054 | 0.030 | 267.5 | 285.3 | 2.3 | 5.1 | 945 | 1252 | 0.0000000 |
| pop_tertile | low | llm_decision_router | 167 | -0.024 | -0.066 | 0.018 | 837.4 | 850.1 | 3.7 | 7.5 | 2964 | 3439 | 0.0000000 |
| pop_tertile | mid | llm_only | 166 | -0.042 | -0.096 | 0.006 | 40.5 | 54.8 | 2.4 | 4.8 | 189 | 294 | 0.0000000 |
| pop_tertile | mid | always_rag | 166 | -0.030 | -0.078 | 0.012 | 776.0 | 789.2 | 2.9 | 4.3 | 2644 | 3216 | 0.0000000 |
| pop_tertile | mid | oracle | 166 | -0.024 | -0.078 | 0.030 | 226.4 | 225.2 | 2.5 | 4.7 | 832 | 990 | 0.0000000 |
| pop_tertile | mid | llm_decision_router | 166 | -0.018 | -0.066 | 0.024 | 814.5 | 811.1 | 4.0 | 6.5 | 2975 | 3272 | 0.0000000 |
| musique_hops | 2.0 | llm_only | 251 | -0.008 | -0.032 | 0.016 | 48.2 | 62.4 | 2.3 | 5.8 | 347 | 330 | 0.0000000 |
| musique_hops | 2.0 | always_rag | 251 | -0.016 | -0.044 | 0.012 | 651.6 | 652.7 | 2.8 | 4.9 | 2388 | 2652 | 0.0000000 |
| musique_hops | 2.0 | oracle | 251 | -0.020 | -0.056 | 0.012 | 77.4 | 100.3 | 2.4 | 5.6 | 443 | 472 | 0.0000000 |
| musique_hops | 2.0 | llm_decision_router | 251 | -0.020 | -0.052 | 0.012 | 697.8 | 670.3 | 3.9 | 7.8 | 2744 | 2697 | 0.0000000 |
| musique_hops | 3.0 | llm_only | 155 | 0.000 | -0.032 | 0.032 | 56.8 | 70.8 | 2.5 | 6.9 | 364 | 401 | 0.0000000 |
| musique_hops | 3.0 | always_rag | 155 | -0.019 | -0.058 | 0.019 | 705.1 | 699.8 | 2.4 | 4.1 | 2505 | 2777 | 0.0000000 |
| musique_hops | 3.0 | oracle | 155 | -0.019 | -0.071 | 0.032 | 88.1 | 107.1 | 2.5 | 6.8 | 463 | 543 | 0.0000000 |
| musique_hops | 3.0 | llm_decision_router | 155 | -0.019 | -0.058 | 0.019 | 759.8 | 769.6 | 3.4 | 7.9 | 2880 | 3059 | 0.0000000 |
| musique_hops | 4.0 | llm_only | 94 | 0.000 | 0.000 | 0.000 | 61.1 | 75.1 | 2.3 | 7.1 | 381 | 444 | 0.0000000 |
| musique_hops | 4.0 | always_rag | 94 | 0.032 | -0.011 | 0.085 | 686.0 | 681.5 | 2.7 | 4.3 | 2464 | 2682 | 0.0000000 |
| musique_hops | 4.0 | oracle | 94 | 0.032 | -0.011 | 0.085 | 94.0 | 79.8 | 2.3 | 7.1 | 496 | 461 | 0.0000000 |
| musique_hops | 4.0 | llm_decision_router | 94 | 0.032 | -0.011 | 0.085 | 745.1 | 755.6 | 3.8 | 7.1 | 2855 | 2956 | 0.0000000 |
| hotpot_type | bridge | llm_only | 395 | -0.035 | -0.066 | -0.005 | 53.6 | 67.5 | 2.7 | 6.1 | 283 | 362 | 0.0000000 |
| hotpot_type | bridge | always_rag | 395 | -0.025 | -0.061 | 0.010 | 467.4 | 472.4 | 3.0 | 4.8 | 1671 | 1916 | 0.0000000 |
| hotpot_type | bridge | oracle | 395 | -0.043 | -0.081 | -0.005 | 124.0 | 139.5 | 2.7 | 5.4 | 514 | 622 | 0.0000000 |
| hotpot_type | bridge | llm_decision_router | 395 | 0.008 | -0.030 | 0.046 | 519.1 | 470.5 | 4.0 | 7.2 | 2037 | 1858 | 0.0000000 |
| hotpot_type | comparison | llm_only | 105 | -0.114 | -0.229 | 0.000 | 47.0 | 61.6 | 2.3 | 5.4 | 229 | 310 | 0.0000000 |
| hotpot_type | comparison | always_rag | 105 | -0.086 | -0.162 | -0.010 | 440.8 | 447.2 | 2.4 | 4.1 | 1536 | 1757 | 0.0000000 |
| hotpot_type | comparison | oracle | 105 | -0.057 | -0.133 | 0.019 | 149.7 | 129.4 | 2.4 | 5.3 | 565 | 569 | 0.0000000 |
| hotpot_type | comparison | llm_decision_router | 105 | -0.029 | -0.124 | 0.067 | 467.5 | 397.7 | 3.4 | 6.7 | 1821 | 1537 | 0.0000000 |
| wiki_type | bridge_comparison | llm_only | 96 | -0.250 | -0.396 | -0.104 | 52.9 | 67.0 | 3.5 | 6.1 | 321 | 344 | 0.0000000 |
| wiki_type | bridge_comparison | always_rag | 96 | -0.021 | -0.104 | 0.062 | 541.6 | 549.4 | 3.8 | 5.4 | 1999 | 2245 | 0.0000000 |
| wiki_type | bridge_comparison | oracle | 96 | -0.083 | -0.198 | 0.031 | 198.3 | 147.8 | 3.7 | 6.1 | 814 | 667 | 0.0000000 |
| wiki_type | bridge_comparison | llm_decision_router | 96 | -0.052 | -0.146 | 0.031 | 592.5 | 581.6 | 4.8 | 8.4 | 2351 | 2329 | 0.0000000 |
| wiki_type | comparison | llm_only | 137 | -0.088 | -0.197 | 0.022 | 49.0 | 63.8 | 3.5 | 6.0 | 320 | 330 | 0.0000000 |
| wiki_type | comparison | always_rag | 137 | -0.051 | -0.153 | 0.044 | 582.9 | 588.9 | 3.7 | 5.2 | 2151 | 2408 | 0.0000000 |
| wiki_type | comparison | oracle | 137 | -0.022 | -0.117 | 0.066 | 236.5 | 201.6 | 3.6 | 5.9 | 958 | 889 | 0.0000000 |
| wiki_type | comparison | llm_decision_router | 137 | -0.051 | -0.153 | 0.051 | 627.0 | 606.2 | 4.7 | 11.7 | 2489 | 2584 | 0.0000000 |
| wiki_type | compositional | llm_only | 205 | 0.005 | -0.034 | 0.044 | 47.2 | 61.1 | 1.8 | 6.7 | 299 | 359 | 0.0000000 |
| wiki_type | compositional | always_rag | 205 | -0.059 | -0.102 | -0.020 | 790.5 | 796.3 | 2.2 | 4.8 | 2847 | 3185 | 0.0000000 |
| wiki_type | compositional | oracle | 205 | -0.049 | -0.102 | 0.005 | 91.2 | 145.9 | 1.8 | 6.4 | 459 | 694 | 0.0000000 |
| wiki_type | compositional | llm_decision_router | 205 | -0.059 | -0.102 | -0.020 | 835.7 | 856.4 | 3.2 | 13.0 | 3195 | 3610 | 0.0000000 |
| wiki_type | inference | llm_only | 62 | 0.000 | 0.000 | 0.000 | 46.7 | 60.6 | 3.2 | 10.9 | 352 | 532 | 0.0000000 |
| wiki_type | inference | always_rag | 62 | -0.048 | -0.129 | 0.032 | 874.4 | 880.4 | 3.9 | 7.4 | 3275 | 3674 | 0.0000000 |
| wiki_type | inference | oracle | 62 | -0.048 | -0.129 | 0.032 | 74.7 | 111.5 | 3.3 | 11.0 | 452 | 739 | 0.0000000 |
| wiki_type | inference | llm_decision_router | 62 | -0.048 | -0.129 | 0.032 | 919.1 | 940.0 | 4.9 | 10.1 | 3624 | 3887 | 0.0000000 |
| hop_type | multi | llm_only | 1500 | -0.040 | -0.058 | -0.021 | 51.4 | 54.6 | 2.6 | 3.8 | 315 | 717 | 0.0000000 |
| hop_type | multi | always_rag | 1500 | -0.077 | -0.096 | -0.059 | 610.9 | 630.7 | 2.9 | 3.7 | 2209 | 4332 | 0.0000000 |
| hop_type | multi | oracle | 1500 | -0.072 | -0.091 | -0.053 | 120.9 | 145.6 | 2.6 | 3.9 | 549 | 1299 | 0.0000000 |
| hop_type | multi | llm_decision_router | 1500 | -0.079 | -0.098 | -0.061 | 658.8 | 676.1 | 3.9 | 4.7 | 2564 | 4771 | 0.0000000 |
| hop_type | single | llm_only | 1500 | -0.097 | -0.117 | -0.077 | 44.5 | 47.8 | 2.4 | 3.6 | 208 | 932 | 0.0000000 |
| hop_type | single | always_rag | 1500 | -0.093 | -0.111 | -0.075 | 783.4 | 804.8 | 2.9 | 3.7 | 2854 | 5141 | 0.0000000 |
| hop_type | single | oracle | 1500 | -0.091 | -0.109 | -0.071 | 242.0 | 245.8 | 2.6 | 3.7 | 922 | 2042 | 0.0000000 |
| hop_type | single | llm_decision_router | 1500 | -0.092 | -0.110 | -0.075 | 817.4 | 802.3 | 4.0 | 4.7 | 3159 | 5421 | 0.0000000 |
| pop_tertile | high | llm_only | 167 | -0.078 | -0.126 | -0.030 | 40.0 | 43.3 | 2.2 | 3.4 | 185 | 763 | 0.0000000 |
| pop_tertile | high | always_rag | 167 | -0.066 | -0.108 | -0.030 | 768.6 | 790.5 | 2.6 | 3.8 | 2547 | 4955 | 0.0000000 |
| pop_tertile | high | oracle | 167 | -0.060 | -0.102 | -0.024 | 193.5 | 187.0 | 2.3 | 3.5 | 703 | 1596 | 0.0000000 |
| pop_tertile | high | llm_decision_router | 167 | -0.060 | -0.102 | -0.024 | 781.3 | 817.8 | 3.6 | 4.7 | 2788 | 5406 | 0.0000000 |
| pop_tertile | low | llm_only | 167 | -0.078 | -0.132 | -0.024 | 41.1 | 44.3 | 2.1 | 3.2 | 181 | 766 | 0.0000000 |
| pop_tertile | low | always_rag | 167 | -0.054 | -0.102 | -0.012 | 798.4 | 822.1 | 2.6 | 3.4 | 2630 | 5106 | 0.0000000 |
| pop_tertile | low | oracle | 167 | -0.084 | -0.132 | -0.036 | 267.5 | 280.9 | 2.3 | 3.2 | 945 | 2145 | 0.0000000 |
| pop_tertile | low | llm_decision_router | 167 | -0.054 | -0.102 | -0.012 | 837.4 | 864.4 | 3.7 | 4.4 | 2964 | 5649 | 0.0000000 |
| pop_tertile | mid | llm_only | 166 | -0.048 | -0.102 | 0.006 | 40.5 | 43.7 | 2.4 | 3.5 | 189 | 778 | 0.0000000 |
| pop_tertile | mid | always_rag | 166 | -0.072 | -0.120 | -0.030 | 776.0 | 797.3 | 2.9 | 3.4 | 2644 | 5059 | 0.0000000 |
| pop_tertile | mid | oracle | 166 | -0.060 | -0.114 | -0.006 | 226.4 | 244.9 | 2.5 | 3.5 | 832 | 1942 | 0.0000000 |
| pop_tertile | mid | llm_decision_router | 166 | -0.072 | -0.120 | -0.030 | 814.5 | 825.0 | 4.0 | 4.4 | 2975 | 5512 | 0.0000000 |
| musique_hops | 2.0 | llm_only | 251 | 0.000 | -0.024 | 0.024 | 48.2 | 51.4 | 2.3 | 3.9 | 347 | 650 | 0.0000000 |
| musique_hops | 2.0 | always_rag | 251 | -0.052 | -0.084 | -0.020 | 651.6 | 670.7 | 2.8 | 3.4 | 2388 | 4456 | 0.0000000 |
| musique_hops | 2.0 | oracle | 251 | -0.040 | -0.076 | -0.008 | 77.4 | 104.1 | 2.4 | 4.0 | 443 | 989 | 0.0000000 |
| musique_hops | 2.0 | llm_decision_router | 251 | -0.052 | -0.084 | -0.020 | 697.8 | 716.3 | 3.9 | 4.4 | 2744 | 4905 | 0.0000000 |
| musique_hops | 3.0 | llm_only | 155 | 0.006 | -0.019 | 0.032 | 56.8 | 59.9 | 2.5 | 3.5 | 364 | 689 | 0.0000000 |
| musique_hops | 3.0 | always_rag | 155 | -0.065 | -0.110 | -0.019 | 705.1 | 723.0 | 2.4 | 3.6 | 2505 | 4723 | 0.0000000 |
| musique_hops | 3.0 | oracle | 155 | -0.052 | -0.103 | 0.000 | 88.1 | 125.4 | 2.5 | 3.6 | 463 | 1080 | 0.0000000 |
| musique_hops | 3.0 | llm_decision_router | 155 | -0.065 | -0.110 | -0.019 | 759.8 | 781.0 | 3.4 | 4.6 | 2880 | 5245 | 0.0000000 |
| musique_hops | 4.0 | llm_only | 94 | -0.011 | -0.032 | 0.000 | 61.1 | 64.2 | 2.3 | 3.7 | 381 | 753 | 0.0000000 |
| musique_hops | 4.0 | always_rag | 94 | -0.011 | -0.043 | 0.021 | 686.0 | 706.1 | 2.7 | 3.7 | 2464 | 4734 | 0.0000000 |
| musique_hops | 4.0 | oracle | 94 | -0.011 | -0.043 | 0.021 | 94.0 | 92.4 | 2.3 | 3.7 | 496 | 919 | 0.0000000 |
| musique_hops | 4.0 | llm_decision_router | 94 | -0.011 | -0.043 | 0.021 | 745.1 | 768.3 | 3.8 | 4.7 | 2855 | 5296 | 0.0000000 |
| hotpot_type | bridge | llm_only | 395 | -0.023 | -0.048 | 0.003 | 53.6 | 57.0 | 2.7 | 3.8 | 283 | 772 | 0.0000000 |
| hotpot_type | bridge | always_rag | 395 | -0.071 | -0.106 | -0.038 | 467.4 | 483.5 | 3.0 | 3.6 | 1671 | 3358 | 0.0000000 |
| hotpot_type | bridge | oracle | 395 | -0.078 | -0.116 | -0.041 | 124.0 | 156.8 | 2.7 | 3.9 | 514 | 1391 | 0.0000000 |
| hotpot_type | bridge | llm_decision_router | 395 | -0.071 | -0.106 | -0.038 | 519.1 | 537.1 | 4.0 | 4.6 | 2037 | 3841 | 0.0000000 |
| hotpot_type | comparison | llm_only | 105 | -0.114 | -0.229 | 0.000 | 47.0 | 50.4 | 2.3 | 3.8 | 229 | 704 | 0.0000000 |
| hotpot_type | comparison | always_rag | 105 | -0.114 | -0.190 | -0.038 | 440.8 | 456.9 | 2.4 | 3.0 | 1536 | 3154 | 0.0000000 |
| hotpot_type | comparison | oracle | 105 | -0.067 | -0.143 | 0.010 | 149.7 | 132.7 | 2.4 | 3.6 | 565 | 1203 | 0.0000000 |
| hotpot_type | comparison | llm_decision_router | 105 | -0.114 | -0.190 | -0.029 | 467.5 | 450.4 | 3.4 | 4.3 | 1821 | 3278 | 0.0000000 |
| wiki_type | bridge_comparison | llm_only | 96 | -0.115 | -0.240 | 0.010 | 52.9 | 56.1 | 3.5 | 4.0 | 321 | 752 | 0.0000000 |
| wiki_type | bridge_comparison | always_rag | 96 | -0.083 | -0.188 | 0.021 | 541.6 | 561.6 | 3.8 | 4.2 | 1999 | 4119 | 0.0000000 |
| wiki_type | bridge_comparison | oracle | 96 | -0.062 | -0.167 | 0.042 | 198.3 | 177.4 | 3.7 | 4.2 | 814 | 1494 | 0.0000000 |
| wiki_type | bridge_comparison | llm_decision_router | 96 | -0.083 | -0.188 | 0.021 | 592.5 | 615.8 | 4.8 | 5.2 | 2351 | 4601 | 0.0000000 |
| wiki_type | comparison | llm_only | 137 | -0.124 | -0.234 | -0.015 | 49.0 | 52.5 | 3.5 | 4.2 | 320 | 734 | 0.0000000 |
| wiki_type | comparison | always_rag | 137 | -0.146 | -0.234 | -0.066 | 582.9 | 605.1 | 3.7 | 4.2 | 2151 | 4412 | 0.0000000 |
| wiki_type | comparison | oracle | 137 | -0.146 | -0.226 | -0.066 | 236.5 | 238.7 | 3.6 | 4.4 | 958 | 1984 | 0.0000000 |
| wiki_type | comparison | llm_decision_router | 137 | -0.168 | -0.255 | -0.088 | 627.0 | 629.2 | 4.7 | 5.3 | 2489 | 4698 | 0.0000000 |
| wiki_type | compositional | llm_only | 205 | -0.044 | -0.088 | -0.005 | 47.2 | 50.2 | 1.8 | 3.0 | 299 | 662 | 0.0000000 |
| wiki_type | compositional | always_rag | 205 | -0.107 | -0.156 | -0.063 | 790.5 | 815.2 | 2.2 | 2.9 | 2847 | 5570 | 0.0000000 |
| wiki_type | compositional | oracle | 205 | -0.102 | -0.156 | -0.054 | 91.2 | 151.3 | 1.8 | 3.2 | 459 | 1327 | 0.0000000 |
| wiki_type | compositional | llm_decision_router | 205 | -0.107 | -0.156 | -0.063 | 835.7 | 863.4 | 3.2 | 3.9 | 3195 | 6032 | 0.0000000 |
| wiki_type | inference | llm_only | 62 | -0.032 | -0.081 | 0.000 | 46.7 | 49.4 | 3.2 | 5.2 | 352 | 771 | 0.0000000 |
| wiki_type | inference | always_rag | 62 | -0.032 | -0.113 | 0.048 | 874.4 | 910.3 | 3.9 | 6.8 | 3275 | 6505 | 0.0000000 |
| wiki_type | inference | oracle | 62 | -0.065 | -0.161 | 0.016 | 74.7 | 122.8 | 3.3 | 5.1 | 452 | 1348 | 0.0000000 |
| wiki_type | inference | llm_decision_router | 62 | -0.032 | -0.113 | 0.048 | 919.1 | 957.7 | 4.9 | 7.8 | 3624 | 6950 | 0.0000000 |
| hop_type | multi | llm_only | 1500 | 0.002 | -0.017 | 0.021 | 65.5 | 54.6 | 6.4 | 3.8 | 365 | 717 | 0.0000000 |
| hop_type | multi | always_rag | 1500 | -0.046 | -0.065 | -0.027 | 614.1 | 630.7 | 4.8 | 3.7 | 2477 | 4332 | 0.0000000 |
| hop_type | multi | oracle | 1500 | -0.037 | -0.056 | -0.018 | 131.1 | 145.6 | 6.1 | 3.9 | 617 | 1299 | 0.0000000 |
| hop_type | multi | llm_decision_router | 1500 | -0.058 | -0.077 | -0.039 | 639.3 | 676.1 | 8.7 | 4.7 | 2589 | 4771 | 0.0000000 |
| hop_type | single | llm_only | 1500 | 0.025 | 0.004 | 0.045 | 58.9 | 47.8 | 5.1 | 3.6 | 310 | 932 | 0.0000000 |
| hop_type | single | always_rag | 1500 | -0.032 | -0.048 | -0.016 | 792.0 | 804.8 | 4.5 | 3.7 | 3267 | 5141 | 0.0000000 |
| hop_type | single | oracle | 1500 | -0.017 | -0.035 | 0.001 | 218.8 | 245.8 | 5.0 | 3.7 | 962 | 2042 | 0.0000000 |
| hop_type | single | llm_decision_router | 1500 | -0.046 | -0.065 | -0.028 | 636.0 | 802.3 | 6.8 | 4.7 | 2584 | 5421 | 0.0000000 |
| pop_tertile | high | llm_only | 167 | 0.024 | -0.030 | 0.078 | 54.3 | 43.3 | 4.8 | 3.4 | 293 | 763 | 0.0000000 |
| pop_tertile | high | always_rag | 167 | -0.024 | -0.060 | 0.012 | 780.0 | 790.5 | 4.3 | 3.8 | 3153 | 4955 | 0.0000000 |
| pop_tertile | high | oracle | 167 | -0.012 | -0.060 | 0.036 | 166.3 | 187.0 | 4.6 | 3.5 | 733 | 1596 | 0.0000000 |
| pop_tertile | high | llm_decision_router | 167 | -0.030 | -0.072 | 0.006 | 685.6 | 817.8 | 6.4 | 4.7 | 2743 | 5406 | 0.0000000 |
| pop_tertile | low | llm_only | 167 | -0.072 | -0.114 | -0.030 | 55.4 | 44.3 | 5.5 | 3.2 | 319 | 766 | 0.0000000 |
| pop_tertile | low | always_rag | 167 | -0.030 | -0.078 | 0.012 | 809.0 | 822.1 | 4.8 | 3.4 | 3285 | 5106 | 0.0000000 |
| pop_tertile | low | oracle | 167 | -0.072 | -0.114 | -0.030 | 285.3 | 280.9 | 5.1 | 3.2 | 1252 | 2145 | 0.0000000 |
| pop_tertile | low | llm_decision_router | 167 | -0.030 | -0.078 | 0.012 | 850.1 | 864.4 | 7.5 | 4.4 | 3439 | 5649 | 0.0000000 |
| pop_tertile | mid | llm_only | 166 | -0.006 | -0.054 | 0.042 | 54.8 | 43.7 | 4.8 | 3.5 | 294 | 778 | 0.0000000 |
| pop_tertile | mid | always_rag | 166 | -0.042 | -0.078 | -0.012 | 789.2 | 797.3 | 4.3 | 3.4 | 3216 | 5059 | 0.0000000 |
| pop_tertile | mid | oracle | 166 | -0.036 | -0.084 | 0.006 | 225.2 | 244.9 | 4.7 | 3.5 | 990 | 1942 | 0.0000000 |
| pop_tertile | mid | llm_decision_router | 166 | -0.054 | -0.096 | -0.018 | 811.1 | 825.0 | 6.5 | 4.4 | 3272 | 5512 | 0.0000000 |
| musique_hops | 2.0 | llm_only | 251 | 0.008 | -0.020 | 0.036 | 62.4 | 51.4 | 5.8 | 3.9 | 330 | 650 | 0.0000000 |
| musique_hops | 2.0 | always_rag | 251 | -0.036 | -0.072 | 0.000 | 652.7 | 670.7 | 4.9 | 3.4 | 2652 | 4456 | 0.0000000 |
| musique_hops | 2.0 | oracle | 251 | -0.020 | -0.060 | 0.020 | 100.3 | 104.1 | 5.6 | 4.0 | 472 | 989 | 0.0000000 |
| musique_hops | 2.0 | llm_decision_router | 251 | -0.032 | -0.072 | 0.008 | 670.3 | 716.3 | 7.8 | 4.4 | 2697 | 4905 | 0.0000000 |
| musique_hops | 3.0 | llm_only | 155 | 0.006 | -0.019 | 0.032 | 70.8 | 59.9 | 6.9 | 3.5 | 401 | 689 | 0.0000000 |
| musique_hops | 3.0 | always_rag | 155 | -0.045 | -0.090 | -0.006 | 699.8 | 723.0 | 4.1 | 3.6 | 2777 | 4723 | 0.0000000 |
| musique_hops | 3.0 | oracle | 155 | -0.032 | -0.077 | 0.013 | 107.1 | 125.4 | 6.8 | 3.6 | 543 | 1080 | 0.0000000 |
| musique_hops | 3.0 | llm_decision_router | 155 | -0.045 | -0.090 | -0.006 | 769.6 | 781.0 | 7.9 | 4.6 | 3059 | 5245 | 0.0000000 |
| musique_hops | 4.0 | llm_only | 94 | -0.011 | -0.032 | 0.000 | 75.1 | 64.2 | 7.1 | 3.7 | 444 | 753 | 0.0000000 |
| musique_hops | 4.0 | always_rag | 94 | -0.043 | -0.096 | 0.000 | 681.5 | 706.1 | 4.3 | 3.7 | 2682 | 4734 | 0.0000000 |
| musique_hops | 4.0 | oracle | 94 | -0.043 | -0.096 | 0.000 | 79.8 | 92.4 | 7.1 | 3.7 | 461 | 919 | 0.0000000 |
| musique_hops | 4.0 | llm_decision_router | 94 | -0.043 | -0.096 | 0.000 | 755.6 | 768.3 | 7.1 | 4.7 | 2956 | 5296 | 0.0000000 |
| hotpot_type | bridge | llm_only | 395 | 0.013 | -0.020 | 0.043 | 67.5 | 57.0 | 6.1 | 3.8 | 362 | 772 | 0.0000000 |
| hotpot_type | bridge | always_rag | 395 | -0.046 | -0.078 | -0.013 | 472.4 | 483.5 | 4.8 | 3.6 | 1916 | 3358 | 0.0000000 |
| hotpot_type | bridge | oracle | 395 | -0.035 | -0.073 | 0.003 | 139.5 | 156.8 | 5.4 | 3.9 | 622 | 1391 | 0.0000000 |
| hotpot_type | bridge | llm_decision_router | 395 | -0.078 | -0.114 | -0.043 | 470.5 | 537.1 | 7.2 | 4.6 | 1858 | 3841 | 0.0000000 |
| hotpot_type | comparison | llm_only | 105 | 0.000 | -0.095 | 0.095 | 61.6 | 50.4 | 5.4 | 3.8 | 310 | 704 | 0.0000000 |
| hotpot_type | comparison | always_rag | 105 | -0.029 | -0.124 | 0.057 | 447.2 | 456.9 | 4.1 | 3.0 | 1757 | 3154 | 0.0000000 |
| hotpot_type | comparison | oracle | 105 | -0.010 | -0.086 | 0.067 | 129.4 | 132.7 | 5.3 | 3.6 | 569 | 1203 | 0.0000000 |
| hotpot_type | comparison | llm_decision_router | 105 | -0.086 | -0.171 | 0.000 | 397.7 | 450.4 | 6.7 | 4.3 | 1537 | 3278 | 0.0000000 |
| wiki_type | bridge_comparison | llm_only | 96 | 0.135 | 0.000 | 0.271 | 67.0 | 56.1 | 6.1 | 4.0 | 344 | 752 | 0.0000000 |
| wiki_type | bridge_comparison | always_rag | 96 | -0.062 | -0.177 | 0.052 | 549.4 | 561.6 | 5.4 | 4.2 | 2245 | 4119 | 0.0000000 |
| wiki_type | bridge_comparison | oracle | 96 | 0.021 | -0.094 | 0.125 | 147.8 | 177.4 | 6.1 | 4.2 | 667 | 1494 | 0.0000000 |
| wiki_type | bridge_comparison | llm_decision_router | 96 | -0.031 | -0.156 | 0.094 | 581.6 | 615.8 | 8.4 | 5.2 | 2329 | 4601 | 0.0000000 |
| wiki_type | comparison | llm_only | 137 | -0.036 | -0.153 | 0.080 | 63.8 | 52.5 | 6.0 | 4.2 | 330 | 734 | 0.0000000 |
| wiki_type | comparison | always_rag | 137 | -0.095 | -0.190 | 0.000 | 588.9 | 605.1 | 5.2 | 4.2 | 2408 | 4412 | 0.0000000 |
| wiki_type | comparison | oracle | 137 | -0.124 | -0.204 | -0.044 | 201.6 | 238.7 | 5.9 | 4.4 | 889 | 1984 | 0.0000000 |
| wiki_type | comparison | llm_decision_router | 137 | -0.117 | -0.204 | -0.022 | 606.2 | 629.2 | 11.7 | 5.3 | 2584 | 4698 | 0.0000000 |
| wiki_type | compositional | llm_only | 205 | -0.049 | -0.093 | -0.010 | 61.1 | 50.2 | 6.7 | 3.0 | 359 | 662 | 0.0000000 |
| wiki_type | compositional | always_rag | 205 | -0.049 | -0.088 | -0.010 | 796.3 | 815.2 | 4.8 | 2.9 | 3185 | 5570 | 0.0000000 |
| wiki_type | compositional | oracle | 205 | -0.054 | -0.098 | -0.010 | 145.9 | 151.3 | 6.4 | 3.2 | 694 | 1327 | 0.0000000 |
| wiki_type | compositional | llm_decision_router | 205 | -0.049 | -0.088 | -0.010 | 856.4 | 863.4 | 13.0 | 3.9 | 3610 | 6032 | 0.0000000 |
| wiki_type | inference | llm_only | 62 | -0.032 | -0.081 | 0.000 | 60.6 | 49.4 | 10.9 | 5.2 | 532 | 771 | 0.0000000 |
| wiki_type | inference | always_rag | 62 | 0.016 | -0.065 | 0.097 | 880.4 | 910.3 | 7.4 | 6.8 | 3674 | 6505 | 0.0000000 |
| wiki_type | inference | oracle | 62 | -0.016 | -0.113 | 0.081 | 111.5 | 122.8 | 11.0 | 5.1 | 739 | 1348 | 0.0000000 |
| wiki_type | inference | llm_decision_router | 62 | 0.016 | -0.065 | 0.097 | 940.0 | 957.7 | 10.1 | 7.8 | 3887 | 6950 | 0.0000000 |

