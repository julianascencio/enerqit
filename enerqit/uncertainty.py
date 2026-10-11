"""Identifiability diagnostics and time-block uncertainty resampling."""

import numpy as np
import pandas as pd


def jacobian_diagnostics(jacobian):
    """Report local sensitivity rank after column normalization.

    This is a local diagnostic, not proof of global identifiability or a
    calibrated posterior. Near-zero sensitivity is reported separately.
    """
    j = np.asarray(jacobian, float)
    norms = np.linalg.norm(j, axis=0)
    normalized = j / np.maximum(norms, 1e-15)
    s = np.linalg.svd(normalized, compute_uv=False)
    rank = int(np.linalg.matrix_rank(normalized, tol=1e-7))
    condition = float(s[0] / s[-1]) if s[-1] > 1e-15 else float("inf")
    return {
        "rank": rank,
        "n_parameters": j.shape[1],
        "condition_number": condition,
        "column_norms": norms.tolist(),
        "singular_values": s.tolist(),
    }


def day_block_bootstrap(frame, estimator, *, repeats=100, seed=0, quantiles=(0.025, 0.975)):
    """Resample complete local-calendar days, preserving within-day dependence.

    ``estimator`` accepts a frame (possibly repeated timestamps) and returns a
    dict of scalar estimates. For APIs requiring unique timestamps, aggregate
    resampling weights or use a residual-based estimator instead. The caller
    controls those semantics. Intervals remain conditional on data/model choice.
    """
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
        raise ValueError("timezone-aware index required")
    days = frame.index.normalize().unique()
    if len(days) < 3 or repeats < 2:
        raise ValueError("at least three days and two repeats required")
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(repeats):
        selected = rng.choice(len(days), size=len(days), replace=True)
        sample = pd.concat([frame.loc[frame.index.normalize() == days[i]] for i in selected])
        samples.append(estimator(sample))
    table = pd.DataFrame(samples)
    return {
        name: {
            "lower": float(table[name].quantile(quantiles[0])),
            "upper": float(table[name].quantile(quantiles[1])),
        }
        for name in table
    }
