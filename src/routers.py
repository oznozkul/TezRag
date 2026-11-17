"""Routers choose, per question, between the no-retrieval path (llm_only) and retrieval (always_rag).

Composed systems need no new API calls: they reuse the logged llm_only / always_rag records of the
chosen path and add the router's own cost and latency.

  oracle_optimistic    llm_only if it is correct, else always_rag; if both are wrong, the cheaper
                       llm_only. The cost-minimal route at oracle accuracy. It needs to know that
                       retrieval will also fail, which no router can know, so its savings are optimistic.
  oracle_realistic     llm_only only if it is correct, else always_rag (both wrong -> always_rag).
                       Same accuracy as oracle_optimistic. Retrieval stays the default when the model
                       cannot answer alone. This is the Adaptive-RAG labelling rule (Jeong et al., 2024):
                       unanswerable queries get a retrieval label, never "no retrieval". It is also the
                       target a learned router is trained on.
  Both oracles use the gold answers: they are upper bounds and training labels, not routers.
  llm_decision_router  the model's own YES/NO answer (system `llm_decision`): yes -> llm_only,
                       no or invalid -> always_rag. Its call is charged as router cost.

Learned routers will implement `route(question_row) -> "llm_only" | "always_rag"` the same way.
"""
from __future__ import annotations

PATHS = ("llm_only", "always_rag")


ORACLES = ("oracle_optimistic", "oracle_realistic")


def oracle_optimistic_route(llm_only_correct: bool, always_rag_correct: bool) -> str:
    if llm_only_correct or not always_rag_correct:
        return "llm_only"
    return "always_rag"


def oracle_realistic_route(llm_only_correct: bool, always_rag_correct: bool) -> str:
    return "llm_only" if llm_only_correct else "always_rag"


ORACLE_ROUTES = {"oracle_optimistic": oracle_optimistic_route, "oracle_realistic": oracle_realistic_route}


def outcome_label(llm_only_correct: bool, always_rag_correct: bool) -> str:
    """Outcome-based label; `no_retrieval_ok` splits into both_ok and rag_hurts."""
    if llm_only_correct and always_rag_correct:
        return "both_ok"
    if llm_only_correct:
        return "rag_hurts"
    if always_rag_correct:
        return "retrieval_needed"
    return "both_fail"
