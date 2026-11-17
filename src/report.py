"""Markdown report for Stage 4. Table text is assembled here; the numbers come from tables.py."""
from __future__ import annotations

import numpy as np
import pandas as pd


def fmt(x, nd=3):
    return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"


def md_table(df: pd.DataFrame, cols: list[tuple[str, str, int | None]]) -> str:
    head = "| " + " | ".join(c[1] for c in cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    lines = [head, sep]
    for _, r in df.iterrows():
        cells = []
        for key, _, nd in cols:
            v = r[key]
            cells.append(fmt(v, nd) if nd is not None and isinstance(v, (float, np.floating)) else str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _dispatch_markdown(df: pd.DataFrame) -> str:
    lines = ["## Calls logged per question", "",
             "Sent means a call was logged. Both paths call the model; `route` on `llm_decision` is "
             "which path that call selected (`llm_only` or `always_rag`). A question rejected by the "
             "filter twice stays sent and leaves `in_comparison`. Source attributes on the same rows "
             "are in `dispatch.csv`.", ""]
    base = df[df.system == "llm_only"]
    for model, g in base.groupby("model", sort=True):
        sent = int(g.sent.sum())
        compared = int(g.in_comparison.sum())
        lines.append(f"- `{model}`: {sent}/{len(g)} questions have an `llm_only` call; "
                     f"{compared} are in the comparison set.")
    return "\n".join(lines) + "\n"


def report(cfg, dry_run, all_q, questions, excl_df, metrics, labels, decision, breakeven, leakage, boot,
           lat_tab, lat_diff, lat_info, retry_rows, df, main_set, extra: str = "") -> str:
    from src.evaluate import BASE, SYSTEMS

    p = cfg.pricing[cfg.llm.model]
    cm = cfg.eval.correct_metric
    L = [f"# Results{' (dry run)' if dry_run else ''}", "",
         f"Model `{cfg.llm.model}`; prices ${p['input_per_1m']}/1M input, ${p['cached_input_per_1m']}/1M cached "
         f"input, ${p['output_per_1m']}/1M output (source: {p['source']}, retrieved {p['retrieved']}). "
         f"BM25 retrieval cost ${cfg.pricing['retrieval_bm25']['per_call_usd']}/call (local). "
         f"\"Correct\" = **{cm}**. Main answer set: `{main_set}` (accuracy ignores aliases of <= "
         f"{cfg.eval.accuracy_min_alias_chars - 1} normalized chars). Bootstrap: {cfg.eval.bootstrap_samples:,} "
         f"paired resamples, stratified by dataset for pooled rows, {cfg.eval.ci:.0%} percentile CI.", "",
         "## Question set", "",
         f"{len(all_q)} questions; **{len(questions)} in the common comparison set**; "
         f"{len(excl_df)} excluded because the prompt was rejected by the provider's filter twice "
         f"(first call + one `--retry-flagged`).", ""]
    if len(excl_df):
        L += [md_table(excl_df, [("qid", "qid", None), ("dataset", "dataset", None), ("split", "split", None),
                                 ("flagged_in", "flagged in", None), ("calls", "calls", None)]), "",
              "Excluded per dataset: " + ", ".join(f"{k} {v}" for k, v in
                                                     excl_df.dataset.value_counts().sort_index().items()), ""]
    L += ["Calls and retries:", "", md_table(pd.DataFrame(retry_rows), [
        ("system", "system", None), ("calls", "calls", None),
        ("qids_called_more_than_once", "qids retried", None), ("recovered", "recovered on retry", None)]), ""]

    def main_tab(split, aset):
        m = metrics[(metrics.split == split) & (metrics.answer_set == aset)].copy()
        m["system"] = pd.Categorical(m.system, SYSTEMS)
        return m.sort_values(["dataset", "system"])

    cols = [("dataset", "dataset", None), ("system", "system", None), ("n", "n", None), ("em", "EM", 3),
            ("f1", "F1", 3), ("accuracy", "Acc", 3), ("mean_input_tokens", "in tok", 1),
            ("mean_output_tokens", "out tok", 1), ("mean_reasoning_tokens", "reas tok", 2),
            ("mean_response_ms", "resp ms", 0),
            ("usd_per_q", "$/q", 7), ("retrieval_calls", "retr calls", None), ("failed_calls", "failed", None)]
    L += ["## Main results (all splits)", "",
          "Tokens, response time, and dollar cost include the router call for `llm_decision_router`. "
          "Response time is the logged model-call time. Local weights have a dollar cost of 0; "
          "tokens and response time are what stay comparable. Failed calls count as wrong.", "",
          md_table(main_tab("all", main_set), cols), "",
          "## Test split only", "", md_table(main_tab("test", main_set)[lambda x: x.dataset == "ALL"], cols), ""]

    if "adaptive_rag" in cfg.eval.answer_sets:
        pc = [("dataset", "dataset", None), ("system", "system", None), ("em", "EM", 3), ("f1", "F1", 3),
              ("accuracy", "Acc", 3)]
        L += ["## Adaptive-RAG comparison: Adaptive-RAG's gold answers", "",
              "Gold = what Adaptive-RAG/IRCoT score against, without our short-alias filter: NQ/TriviaQA the "
              "full DPR answer list, HotpotQA/2Wiki/MuSiQue the single IRCoT answer, PopQA (not in "
              "Adaptive-RAG) all `possible_answers`. Accuracy is still token-bounded containment. "
              "Base systems only.", "",
              md_table(main_tab("all", "adaptive_rag")[lambda x: x.system.isin(BASE)], pc), ""]

    lab = labels[(labels.split == "all") & (labels.answer_set == main_set)]
    lab_cols = [("dataset", "dataset", None), ("n", "n", None), ("no_retrieval_ok", "no_retrieval_ok", None),
                ("both_ok", "both_ok", None), ("rag_hurts", "rag_hurts", None),
                ("retrieval_needed", "retrieval_needed", None), ("both_fail", "both_fail", None)]
    L += ["## Outcome labels", "",
          "`no_retrieval_ok` = llm_only correct (= both_ok + rag_hurts); `rag_hurts` = llm_only correct, "
          "always_rag wrong; `retrieval_needed` = llm_only wrong, always_rag correct; `both_fail` = both wrong.", "",
          md_table(lab, lab_cols), "",
          "### rag_hurts per dataset and split", "",
          md_table(labels[labels.answer_set == main_set]
                   .pivot(index="dataset", columns="split", values="rag_hurts")
                   .reindex(list(lab.dataset)).reset_index()[["dataset", "train", "dev", "test", "all"]],
                   [("dataset", "dataset", None), ("train", "train", None), ("dev", "dev", None),
                    ("test", "test", None), ("all", "all", None)]), ""]

    mo = metrics[(metrics.split == "all") & (metrics.answer_set == main_set) & (metrics.dataset == "ALL")] \
        .set_index("system")
    a = mo.loc["always_rag"]
    ocols = [("system", "system", None), ("correct", cm, 3), ("usd_per_q", "$/q", 7),
             ("saving", "cheaper than Always-RAG", 3), ("retrieval_rate", "retrieval rate", 3)]
    orows = mo.loc[["always_rag", "oracle_optimistic", "oracle_realistic"]].reset_index()
    orows["saving"] = 1 - orows.usd_per_q / a.usd_per_q
    dmean = mo.loc["llm_decision_router"].router_usd_per_q
    real = mo.loc["oracle_realistic"]
    ceiling = real.usd_per_q + dmean
    L += ["## Oracles vs Always-RAG", "",
          "Both oracles read the gold answers, so they are upper bounds and training labels, not routers. "
          "`oracle_optimistic` sends questions that both paths get wrong to the cheaper llm_only; that "
          "needs to know retrieval will fail too. `oracle_realistic` skips retrieval only when llm_only is "
          "correct and keeps retrieval as the default otherwise (the Adaptive-RAG labelling rule). "
          "Accuracy is identical; only cost differs.", "",
          md_table(orows, ocols), "",
          f"**A perfect router that costs one llm_decision call per question**: realistic oracle "
          f"${real.usd_per_q:.7f} + decision ${dmean:.7f} = ${ceiling:.7f}/q vs Always-RAG ${a.usd_per_q:.7f} "
          f"({1 - ceiling / a.usd_per_q:+.1%} saving). With the optimistic oracle it would be "
          f"{1 - (mo.loc['oracle_optimistic'].usd_per_q + dmean) / a.usd_per_q:+.1%}. Other price ratios: "
          f"`price_sensitivity.csv`.", ""]

    dsel = decision[decision.answer_set == main_set]
    L += ["## llm_decision router (the model's own YES/NO)", "",
          "Route: YES -> llm_only, NO/invalid -> always_rag. Decision cost is charged as router cost. "
          "Agreement with the optimistic oracle is dominated by both_fail questions (it sends them to "
          "llm_only); the realistic oracle sends them to always_rag. `agree on decisive` uses only "
          "rag_hurts + retrieval_needed, where the route changes the outcome (same for both oracles).", "",
          md_table(dsel, [("dataset", "dataset", None), ("n", "n", None), ("yes", "YES", None), ("no", "NO", None),
                          ("invalid", "invalid", None), ("agree_with_oracle_optimistic", "agree w/ opt. oracle", 3),
                          ("agree_with_oracle_realistic", "agree w/ real. oracle", 3),
                          ("n_decisive", "decisive q", None), ("agree_on_decisive", "agree on decisive", 3),
                          ("self_knowledge_acc", "YES<->llm_only correct", 3),
                          ("yes_precision", "P(llm_only correct | YES)", 3),
                          ("llm_only_correct_rate", "llm_only correct rate", 3)]), "",
          "Confusion vs the realistic oracle route (all datasets):", ""]
    allr = dsel[dsel.dataset == "ALL"].iloc[0]
    L += ["| | oracle_realistic: llm_only | oracle_realistic: always_rag |", "|---|---|---|",
          f"| decision YES | {allr.yes_and_oracle_llm_only} | {allr.yes_but_oracle_rag} |",
          f"| decision NO/invalid | {allr.no_but_oracle_llm_only} | {allr.no_and_oracle_rag} |", ""]
    dr = mo.loc["llm_decision_router"]
    L += [f"Score and cost (incl. decision call): {cm} {dr.correct:.3f}, ${dr.usd_per_q:.7f}/q "
          f"(router ${dr.router_usd_per_q:.7f}, generation ${dr.generation_usd_per_q:.7f}); "
          f"retrieval rate {dr.retrieval_rate:.1%}.", "",
          "Decision call tokens (mean per question): input "
          f"{df[(df.system == 'llm_decision_router') & (df.answer_set == main_set)].router_input_tokens.mean():.1f}, "
          f"output {df[(df.system == 'llm_decision_router') & (df.answer_set == main_set)].router_output_tokens.mean():.1f}, "
          f"reasoning {df[(df.system == 'llm_decision_router') & (df.answer_set == main_set)].router_reasoning_tokens.mean():.2f}.", ""]

    L += ["## Break-even: decision cost vs. skipped context", "",
          "For questions the decision routes to llm_only (YES), skipping retrieval saves the context tokens "
          "(always_rag input − llm_only input) and the cost difference. Ratio < 1 means the decision call pays "
          "for itself. `breakeven_skip_rate` = decision cost per question / mean saving per skipped question; "
          "the router must skip at least this share of questions to break even on cost.", "",
          md_table(breakeven, [("dataset", "dataset", None), ("n", "n", None), ("skipped_retrievals", "skipped", None),
                               ("saved_context_tokens_total", "saved ctx tok", None),
                               ("decision_tokens_total", "decision tok (in+out)", None),
                               ("token_ratio_decision_to_saved_context", "tok ratio", 3),
                               ("decision_usd_total", "decision $", 5), ("saved_usd_total", "saved $", 5),
                               ("cost_to_saving_ratio_usd", "$ ratio", 3),
                               ("breakeven_skip_rate", "break-even skip rate", 3),
                               ("actual_skip_rate", "actual skip rate", 3)]), ""]

    if lat_tab is not None:
        L += ["## Latency (sequential run, test subset)", "",
              f"{lat_info['n']} test questions with valid records for all three calls "
              f"(dropped: {len(lat_info['dropped_errors'])}); concurrency 1, fresh retrieval. "
              f"Adaptive = decision call followed by the chosen path, run sequentially; "
              f"{lat_info['routed_to_llm_only']} of {lat_info['n']} routed to llm_only.", "",
              md_table(lat_tab, [("system", "system", None), ("n", "n", None), ("mean_ms", "mean ms", 0),
                                 ("p50_ms", "P50 ms", 0), ("p95_ms", "P95 ms", 0)]), "",
              md_table(lat_diff, [("comparison", "comparison", None), ("mean_diff_ms", "mean diff ms", 0),
                                  ("mean_ci_lo", "CI lo", 0), ("mean_ci_hi", "CI hi", 0),
                                  ("median_diff_ms", "median diff ms", 0), ("median_ci_lo", "CI lo", 0),
                                  ("median_ci_hi", "CI hi", 0)]), ""]

    b = boot[(boot.answer_set == main_set) & (boot.dataset == "ALL")]
    L += ["## Paired bootstrap differences (all datasets)", "",
          md_table(b, [("comparison", "comparison", None), ("metric", "metric", None), ("diff", "diff", 4),
                       ("ci_lo", "CI lo", 4), ("ci_hi", "CI hi", 4), ("significant", "CI excludes 0", None)]), "",
          "Per-dataset intervals: `bootstrap.csv`.", ""]

    lk = leakage[leakage.dataset == "ALL"]
    L += ["## Reasoning leakage", "",
          "Leak = `incomplete` (hit max_output_tokens) or >= 17 words or a deliberation marker "
          "(see `src/leakage.py`). Common question set; final record per question.", "",
          md_table(lk, [("system", "system", None), ("n", "n", None), ("leak", "leaked", None),
                        ("leak_rate", "rate", 3), ("incomplete", "incomplete", None), ("long", ">=17 words", None),
                        ("marker", "marker", None)]), "",
          "Per dataset: `leakage.csv`.", ""]
    if extra:
        L += ["", extra.rstrip(), ""]
    return "\n".join(L) + "\n"


def price_markdown(price: pd.DataFrame) -> str:
    if price.empty:
        return ""
    keep = ["oracle_optimistic", "oracle_realistic", "oracle_realistic+decision", "llm_decision_router"]
    p = price[price.system.isin(keep)]
    wide = p.pivot_table(index=["model", "price_ratio"], columns="system", values="saving_vs_always_rag",
                         sort=False).reset_index()
    be = p[p.system == "llm_decision_router"].set_index(["model", "price_ratio"]).breakeven_skip_rate
    wide["breakeven"] = [be.loc[(m, r)] for m, r in zip(wide.model, wide.price_ratio)]
    cols = [("model", "model", None), ("price_ratio", "out:in price", None)]
    cols += [(k, k, 3) for k in keep] + [("breakeven", "llm_decision break-even skip rate", 3)]
    return "\n".join(["## Price sensitivity", "",
                      "Share cheaper than Always-RAG (negative = more expensive), recomputed from logged tokens "
                      "with output priced at the given multiple of input. The share does not depend on the "
                      "absolute price, so local models are included. Cached-input discounts are ignored. "
                      "`oracle_realistic+decision` = a router that is always right but pays one llm_decision "
                      "call per question.", "", md_table(wide, cols), ""])
