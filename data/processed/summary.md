# Sample and split summary

| dataset | hop | pool | unscorable dropped | ambiguous dropped | sampled | train | dev | test | words/q | answers/q | multi-answer |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nq | single | 6515 | 1 | 8 | 500 | 300 | 100 | 100 | 9.17 | 1.3 | 12.4% |
| triviaqa | single | 8837 | 0 | 4 | 500 | 300 | 100 | 100 | 13.87 | 13.48 | 88.6% |
| popqa | single | 14267 | 0 | 2354 | 500 | 300 | 100 | 100 | 6.62 | 3.77 | 71.8% |
| hotpotqa | multi | 7405 | 2 | 0 | 500 | 300 | 100 | 100 | 15.61 | 1 | 0.0% |
| 2wikimultihopqa | multi | 12576 | 0 | 0 | 500 | 300 | 100 | 100 | 11.91 | 2.85 | 57.2% |
| musique | multi | 2417 | 0 | 18 | 500 | 300 | 100 | 100 | 18.04 | 1.43 | 28.0% |
| **total** | | | | | 3000 | 1800 | 600 | 600 | | | |

Questions with an alias ignored by accuracy (normalized length < 3):

| dataset | train | dev | test | total |
|---|---|---|---|---|
| nq | 0 | 0 | 0 | 0 |
| triviaqa | 22 | 6 | 4 | 32 |
| popqa | 28 | 12 | 8 | 48 |
| hotpotqa | 0 | 0 | 0 | 0 |
| 2wikimultihopqa | 21 | 6 | 9 | 36 |
| musique | 10 | 5 | 1 | 16 |
| **total** | 81 | 29 | 22 | 132 |
