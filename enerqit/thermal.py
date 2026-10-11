"""Thermal limiting envelopes with explicit excitation requirements."""

import numpy as np
from scipy.optimize import least_squares

from enerqit.quality import finite_vectors
from enerqit.results import InferenceResult
from enerqit.uncertainty import jacobian_diagnostics


def derating_cap(temperature, rated_power, knee, slope):
    """Piecewise power cap in W; slope is fractional rating per degree C."""
    if rated_power <= 0 or slope < 0:
        raise ValueError("positive rating and nonnegative slope required")
    return rated_power * np.clip(1 - slope * np.maximum(np.asarray(temperature) - knee, 0), 0, 1)


def fit_derating(temperature, power_ac, available_ac, *, rated_power, command_limit=None):
    """Fit knee/slope using unconstrained available-power estimates and command limits.

    Temperature must be the defined relevant sensor (e.g. heatsink), consistently
    used in fitting and inference. Ambient temperature cannot identify junction
    limits without a thermal transfer model. Available AC must be estimated
    independently; defining it from measured output makes the inference circular.
    """
    t, ac, available = finite_vectors(temperature, power_ac, available_ac, minimum_rows=20)
    if rated_power <= 0 or np.any(ac < 0) or np.any(available < 0):
        raise ValueError("positive rating and nonnegative power required")
    command = (
        np.full_like(t, rated_power) if command_limit is None else np.asarray(command_limit, float)
    )
    if command.shape != t.shape or not np.isfinite(command).all() or np.any(command < 0):
        raise ValueError("command_limit must match observations and be nonnegative")
    eligible = (available >= 1.02 * rated_power) & (command >= rated_power)
    tt, yy = t[eligible], ac[eligible]
    warnings = [
        "Conditional on independent available-power estimates and exclusion of other limits.",
        "Thermal association alone does not establish thermal causation or an OEM specification.",
    ]
    if len(tt) < 20 or np.ptp(tt) < 8 or not np.any(yy < 0.95 * rated_power):
        return InferenceResult(
            {},
            "classical_piecewise_least_squares",
            float("nan"),
            len(tt),
            status="not_identifiable",
            warnings=warnings
            + ["Insufficient high-power thermal excitation; no knee is reported."],
        )
    opt = least_squares(
        lambda x: (derating_cap(tt, rated_power, *x) - yy) / rated_power,
        [np.quantile(tt, 0.4), 0.01],
        bounds=([tt.min(), 1e-5], [tt.max(), 0.1]),
        x_scale="jac",
    )
    diag = jacobian_diagnostics(opt.jac)
    low = int(np.sum(tt <= opt.x[0]))
    high = int(np.sum(tt > opt.x[0]))
    identified = diag["rank"] == 2 and low >= 3 and high >= 3
    params = {"knee": float(opt.x[0]), "slope": float(opt.x[1])} if identified else {}
    return InferenceResult(
        params,
        "classical_piecewise_least_squares",
        float(np.sqrt(np.mean(opt.fun**2)) * rated_power),
        len(tt),
        status="estimated" if identified else "not_identifiable",
        units={"knee": "degC", "slope": "1/degC", "rmse": "W"},
        diagnostics={
            **diag,
            "below_knee_samples": low,
            "above_knee_samples": high,
            "excluded_samples": int(len(t) - len(tt)),
        },
        warnings=warnings,
    )
