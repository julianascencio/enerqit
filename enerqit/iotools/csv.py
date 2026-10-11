"""Strict UTC CSV interchange."""

import pandas as pd

from enerqit.quality import validate_frame


def read_csv(path, *, required=()):
    """Read CSV with explicitly offset-aware timestamp column and numeric channels.

    Timestamps are normalized to UTC. Naive timestamps are rejected, not assumed
    to be UTC; order and duplicates remain validation errors.
    """
    data = pd.read_csv(path)
    if "timestamp" not in data:
        raise ValueError("timestamp column required")
    parsed = [pd.Timestamp(value) for value in data.pop("timestamp")]
    if any(pd.isna(t) or t.tzinfo is None for t in parsed):
        raise ValueError("every timestamp must contain a UTC offset")
    data.index = pd.DatetimeIndex([t.tz_convert("UTC") for t in parsed], name="timestamp")
    return validate_frame(data, required)
