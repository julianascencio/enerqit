"""Explicit time-series contracts; units are never guessed."""

import numpy as np
import pandas as pd


def validate_frame(frame, required=(), *, minimum_rows=1):
    """Validate unique, ordered, timezone-aware observations with finite channels.

    Units: irradiance W/m², temperature °C, power W, current A, voltage V.
    Missing or nonfinite requested channels raise instead of being imputed.
    """
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
        raise ValueError("index must be a timezone-aware DatetimeIndex")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError("timestamps must be unique and increasing")
    if len(frame) < minimum_rows:
        raise ValueError(f"at least {minimum_rows} observations required")
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"missing channels: {sorted(missing)}")
    for name in required:
        try:
            finite = np.isfinite(frame[name].to_numpy(dtype=float)).all()
        except (TypeError, ValueError):
            finite = False
        if not finite:
            raise ValueError(f"{name} must be numeric and finite")
    return frame


def finite_vectors(*values, minimum_rows=3):
    """Return matching finite one-dimensional float arrays."""
    arrays = tuple(np.asarray(v, dtype=float) for v in values)
    if (
        not arrays
        or any(a.ndim != 1 for a in arrays)
        or len({a.shape for a in arrays}) != 1
        or len(arrays[0]) < minimum_rows
        or any(not np.isfinite(a).all() for a in arrays)
    ):
        raise ValueError("matching finite 1-D vectors with enough observations required")
    return arrays
