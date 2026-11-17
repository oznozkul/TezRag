"""Features for routers that make no LLM call (src/learned_routers.py).

Every feature is available before the answer is generated:

  rules   from the question text only: question word, length, digits, capitalised words
  bm25    from the BM25 retrieval of the same question: top scores, the gap between them, and how
          many question words the five passages contain. Retrieval is local and free here (cost $0,
          P50 62 ms), so a router may run it and then decide whether to send the passages to the
          model; skipping saves the context tokens, not the search.
  embed   a sentence embedding of the question (BAAI/bge-small-en-v1.5, local CPU, cached)

Not used as features: the dataset name, hop type and PopQA popularity (they come from the source
dataset, not from the question; the `dataset_prior` baseline uses them on purpose), and anything
derived from gold answers or other models' outputs.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from src.config import Config

WH_WORDS = ("who", "whom", "whose", "what", "when", "where", "which", "why", "how many", "how much",
            "how")
YES_NO_STARTS = ("is", "are", "was", "were", "did", "do", "does", "can", "could", "has", "have",
                 "had", "will", "would", "should")
_TOKEN = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset("""a an the of in on at to for from by with and or is are was were be been being
did do does what who whom whose which when where why how many much that this these those it its as
into than then there their his her he she they them you your we our i me my not no yes""".split())
EMBED_MODEL = "BAAI/bge-small-en-v1.5"


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall((text or "").lower())


def rule_features(question: str) -> dict[str, float]:
    q = (question or "").strip()
    low = q.lower()
    toks = _tokens(q)
    first = toks[0] if toks else ""
    f = {f"wh_{w.replace(' ', '_')}": 0.0 for w in WH_WORDS}
    for w in WH_WORDS:                       # longest match first: "how many" before "how"
        if re.search(rf"\b{w}\b", low):
            f[f"wh_{w.replace(' ', '_')}"] = 1.0
            break
    f["yes_no"] = float(first in YES_NO_STARTS)
    f["n_tokens"] = float(len(toks))
    f["n_chars"] = float(len(q))
    f["has_digit"] = float(any(c.isdigit() for c in q))
    words = q.split()
    f["n_capitalised"] = float(sum(1 for w in words[1:] if w[:1].isupper()))
    f["n_commas"] = float(q.count(","))
    f["has_quote"] = float('"' in q or "'" in q)
    f["n_content_words"] = float(sum(1 for t in toks if t not in STOPWORDS))
    return f


def context_of(prompt: str) -> str:
    """The passages block of an always_rag prompt (between 'Context:' and the last 'Question:')."""
    if not prompt or "Context:" not in prompt:
        return ""
    body = prompt.split("Context:", 1)[1]
    return body.rsplit("Question:", 1)[0]


def bm25_features(question: str, scores: list[float], prompt: str) -> dict[str, float]:
    s = np.array(sorted(scores or [], reverse=True), dtype=float)
    top = s[0] if len(s) else 0.0
    second = s[1] if len(s) > 1 else 0.0
    content = [t for t in _tokens(question) if t not in STOPWORDS]
    ctx = set(_tokens(context_of(prompt)))
    return {
        "bm25_top1": float(top), "bm25_gap12": float(top - second),
        "bm25_mean5": float(s.mean()) if len(s) else 0.0, "bm25_std5": float(s.std()) if len(s) else 0.0,
        "bm25_top1_rel": float(top / s.mean()) if len(s) and s.mean() else 0.0,
        "q_overlap": float(sum(t in ctx for t in content) / len(content)) if content else 0.0,
    }


def embed_cache(cfg: Config, dry_run: bool) -> Path:
    return cfg.path("cache", dry_run) / "embeddings" / "bge-small-en-v1.5.npz"


def question_embeddings(cfg: Config, dry_run: bool, qids: list[str], texts: list[str]) -> np.ndarray:
    """L2-normalised CLS embeddings (bge convention), cached by qid. Downloads nothing: the model
    must already be in cache/hf (see README)."""
    path = embed_cache(cfg, dry_run)
    if path.exists():
        z = np.load(path, allow_pickle=False)
        have = dict(zip(z["qids"].tolist(), z["emb"]))
        if all(q in have for q in qids):
            return np.stack([have[q] for q in qids])
    import torch
    from transformers import AutoModel, AutoTokenizer

    hf = cfg.path("cache") / "hf"
    tok = AutoTokenizer.from_pretrained(EMBED_MODEL, cache_dir=hf, local_files_only=True)
    model = AutoModel.from_pretrained(EMBED_MODEL, cache_dir=hf, local_files_only=True).eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), 64):
            batch = tok(texts[i:i + 64], padding=True, truncation=True, max_length=128, return_tensors="pt")
            cls = model(**batch).last_hidden_state[:, 0]
            out.append(torch.nn.functional.normalize(cls, dim=-1).numpy())
    emb = np.concatenate(out).astype(np.float32)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, qids=np.array(qids), emb=emb)
    return emb
