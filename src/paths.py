"""Where run logs and parameter probes are written.

OpenAI stays under results/. Every other provider writes under results/models/<model>/.
The shared summary directory (dispatch and strata for every model) is not this root;
callers that need it use cfg.path("results") / "summary".
"""
from __future__ import annotations

from pathlib import Path

from src.config import Config


def results_root(cfg: Config, dry_run: bool = False) -> Path:
    root = cfg.path("results", dry_run)
    if cfg.llm.provider != "openai":
        root = root / "models" / cfg.llm.model
    return root


def out_path(cfg: Config, system: str, dry_run: bool, latency: bool) -> Path:
    """OpenAI logs stay in results/raw. Every other provider writes under results/models/<model>/."""
    return results_root(cfg, dry_run) / ("latency" if latency else "raw") / f"{system}.jsonl"


def probe_path(cfg: Config) -> Path:
    """OpenAI keeps the original probe file. Other providers get their own directory."""
    return results_root(cfg) / "meta" / "param_probe.json"
