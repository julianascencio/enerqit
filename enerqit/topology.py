"""Conditional integer string topology inference from DC electrical channels."""

from itertools import product

import numpy as np

from enerqit.ivtools import operating_points
from enerqit.quality import finite_vectors
from enerqit.results import InferenceResult


def fit_string_counts(
    voltage,
    current,
    irradiance,
    temperature,
    *,
    module=None,
    series_candidates=range(10, 31),
    parallel_candidates=range(1, 21),
):
    """Rank uniform Ns/Np configurations using known module physics at MPPT.

    Requires array DC voltage/current for an electrically homogeneous subarray.
    It cannot recover inverter inventory from aggregate AC power or distinguish
    arbitrary wiring, module mismatch, unavailable strings and sensor gain errors.
    """
    v, i, g, t = finite_vectors(voltage, current, irradiance, temperature, minimum_rows=10)
    series, parallel = list(series_candidates), list(parallel_candidates)
    if not series or not parallel or any(x <= 0 or int(x) != x for x in series + parallel):
        raise ValueError("nonempty positive integer candidates required")
    if np.any(v <= 0) or np.any(i <= 0):
        raise ValueError("positive operating voltage/current required")
    predicted = operating_points(g, t, module)
    vm, im = np.asarray(predicted["v_mp"]), np.asarray(predicted["i_mp"])
    candidates = []
    for ns, np_ in product(series, parallel):
        error = np.r_[(ns * vm - v) / np.median(v), (np_ * im - i) / np.median(i)]
        candidates.append((float(np.mean(error**2)), int(ns), int(np_)))
    candidates.sort()
    score, ns, np_ = candidates[0]
    return InferenceResult(
        {"modules_per_string": ns, "parallel_strings": np_, "module_count": ns * np_},
        "classical_integer_enumeration",
        float(np.sqrt(score)),
        len(v),
        units={"rmse": "normalized V/I"},
        diagnostics={
            "top_candidates": [{"mse": s, "ns": n, "np": p} for s, n, p in candidates[:5]],
            "candidate_count": len(candidates),
        },
        warnings=[
            "Conditional on known module type, uniform strings and MPPT.",
            "Candidate score separation is not a confidence probability.",
        ],
    )
