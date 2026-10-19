"""Paired bootstrap confidence intervals over questions.

Differences between two systems are computed on the same questions (paired). For pooled results the
resampling is stratified by dataset (each dataset keeps its size), so the pooled mix stays fixed.
"""
from __future__ import annotations

import numpy as np


def paired_mean_diff(a, b, strata=None, n_boot: int = 10_000, ci: float = 0.95,
                     seed: int = 42) -> tuple[float, float, float]:
    """Mean of (a - b) and its percentile CI."""
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    if len(d) == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    strata = np.zeros(len(d), dtype=int) if strata is None else np.asarray(strata)
    total = np.zeros(n_boot)
    for s in np.unique(strata):
        ds = d[strata == s]
        idx = rng.integers(0, len(ds), size=(n_boot, len(ds)))
        total += ds[idx].sum(axis=1)
    boots = total / len(d)
    lo, hi = np.quantile(boots, [(1 - ci) / 2, 1 - (1 - ci) / 2])
    return float(d.mean()), float(lo), float(hi)


def paired_stat_diff(a, b, stat=np.median, n_boot: int = 10_000, ci: float = 0.95,
                     seed: int = 42) -> tuple[float, float, float]:
    """stat(a) - stat(b) on paired resamples (e.g. median latency difference)."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(a), size=(n_boot, len(a)))
    boots = stat(a[idx], axis=1) - stat(b[idx], axis=1)
    lo, hi = np.quantile(boots, [(1 - ci) / 2, 1 - (1 - ci) / 2])
    return float(stat(a) - stat(b)), float(lo), float(hi)
