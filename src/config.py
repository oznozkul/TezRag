"""Config loading and validation. Everything experiment-relevant comes from one YAML file."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Literal

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, model_validator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "default.yaml"

# OPENAI_API_KEY and JAVA_HOME come only from .env (git-ignored) or the environment.
load_dotenv(PROJECT_ROOT / ".env", override=False)

SINGLE_HOP = {"nq", "triviaqa", "popqa"}
MULTI_HOP = {"hotpotqa", "2wikimultihopqa", "musique"}


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Paths(_Strict):
    raw: str
    processed: str
    splits: str
    corpora: str
    indexes: str
    cache: str
    results: str
    dryrun_root: str


class DataCfg(_Strict):
    n_per_dataset: int = Field(gt=0)
    split_ratios: dict[str, float]
    datasets: list[str]
    dry_run_n: int = Field(gt=0)

    @model_validator(mode="after")
    def _check(self) -> "DataCfg":
        if set(self.split_ratios) != {"train", "dev", "test"}:
            raise ValueError("split_ratios must have exactly train/dev/test")
        if abs(sum(self.split_ratios.values()) - 1.0) > 1e-9:
            raise ValueError("split_ratios must sum to 1")
        unknown = set(self.datasets) - SINGLE_HOP - MULTI_HOP
        if unknown:
            raise ValueError(f"unknown datasets: {unknown}")
        return self


class BM25Cfg(_Strict):
    k1: float
    b: float


class RetrievalCfg(_Strict):
    top_k: int = Field(gt=0)
    candidate_k: int = Field(gt=0)
    bm25: BM25Cfg
    dedup_by_text: bool
    corpus_for: dict[str, str]


class LLMCfg(_Strict):
    provider: Literal["openai", "gemini", "deepseek", "ollama", "anthropic"]
    model: str
    api: Literal["responses", "generate_content", "chat", "messages"]
    ollama_tag: str | None = None
    params: dict[str, Any]
    timeout_s: float

    @model_validator(mode="after")
    def _api(self) -> "LLMCfg":
        expected = {"openai": "responses", "gemini": "generate_content", "deepseek": "responses",
                    "ollama": "chat", "anthropic": "messages"}[self.provider]
        if self.api != expected:
            raise ValueError(f"{self.provider} uses api {expected!r}, not {self.api!r}")
        if self.provider == "ollama" and not self.ollama_tag:
            raise ValueError("ollama requires ollama_tag")
        return self


class PromptsCfg(_Strict):
    llm_only: str
    always_rag: str
    llm_decision: str
    passage: str
    passage_separator: str


class RunnerCfg(_Strict):
    concurrency: int = Field(gt=0)
    rpm: int = Field(gt=0)
    tpm: int = Field(gt=0)
    max_retries: int = Field(ge=0)
    backoff_base_s: float
    backoff_max_s: float


class LatencyCfg(_Strict):
    split: Literal["train", "dev", "test"]
    n: int = Field(gt=0)
    concurrency: int = Field(gt=0)
    warmup: int = Field(ge=0)


class EvalCfg(_Strict):
    correct_metric: Literal["accuracy", "em", "f1"]
    f1_threshold: float
    accuracy_min_alias_chars: int = Field(ge=0)
    answer_sets: list[Literal["all", "adaptive_rag"]]
    bootstrap_samples: int = Field(ge=1000)
    ci: float


class Config(_Strict):
    seed: int
    paths: Paths
    data: DataCfg
    retrieval: RetrievalCfg
    llm: LLMCfg
    prompts: PromptsCfg
    systems: list[Literal["llm_only", "always_rag", "llm_decision"]]
    runner: RunnerCfg
    latency: LatencyCfg
    eval: EvalCfg
    pricing: dict[str, dict[str, Any]]

    @model_validator(mode="after")
    def _check(self) -> "Config":
        missing = set(self.data.datasets) - set(self.retrieval.corpus_for)
        if missing:
            raise ValueError(f"retrieval.corpus_for missing datasets: {missing}")
        if self.llm.model not in self.pricing:
            raise ValueError(f"no pricing entry for model {self.llm.model}")
        return self

    # --- helpers -------------------------------------------------------------
    def path(self, key: str, dry_run: bool = False) -> Path:
        """Resolve a path. Outputs that depend on sampled questions are redirected under
        dryrun_root in dry-run mode, so a dry run never touches the real split/results."""
        rel = getattr(self.paths, key)
        if dry_run and key in {"processed", "splits", "results", "cache"}:
            return PROJECT_ROOT / self.paths.dryrun_root / key
        return PROJECT_ROOT / rel

    def hash(self) -> str:
        return config_hash(self)


def config_hash(cfg: Config) -> str:
    blob = json.dumps(cfg.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _merge(base: dict, over: dict, replace_keys: frozenset[str] = frozenset()) -> dict:
    """Deep-merge `over` onto `base`. `llm.params` is replaced whole, not key by key,
    so a Gemini overlay does not inherit OpenAI-only parameters."""
    out = dict(base)
    for key, value in over.items():
        if (key in replace_keys or not isinstance(value, dict)
                or not isinstance(out.get(key), dict)):
            out[key] = value
        else:
            child = frozenset({"params"}) if key == "llm" else frozenset()
            out[key] = _merge(out[key], value, child)
    return out


def load_config(path: str | os.PathLike | None = None) -> Config:
    with open(DEFAULT_CONFIG) as f:
        raw = yaml.safe_load(f)
    if path:
        p = Path(path)
        if p.resolve() != DEFAULT_CONFIG.resolve():
            with open(p) as f:
                raw = _merge(raw, yaml.safe_load(f) or {})
    return Config.model_validate(raw)


def hop_type(dataset: str) -> str:
    if dataset in SINGLE_HOP:
        return "single"
    if dataset in MULTI_HOP:
        return "multi"
    raise ValueError(dataset)
