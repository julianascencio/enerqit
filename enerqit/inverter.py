"""Effective inverter loss/efficiency curves from synchronized DC and AC power."""

import numpy as np
from scipy.optimize import lsq_linear

from enerqit.quality import finite_vectors
from enerqit.results import InferenceResult
from enerqit.uncertainty import jacobian_diagnostics


def efficiency_curve(power_dc, rated_power, coefficients):
    """Evaluate efficiency for nonnegative loss coefficients a, b, c.

    Model: loss/Prated = a + b*u + c*u², u=Pdc/Prated.
    Output is clipped to [0,1], with zero at Pdc=0. Valid only in the fitted
    load/voltage/temperature domain; clipping is not a thermal model.
    """
    p = np.asarray(power_dc, float)
    c = np.asarray(coefficients, float)
    if (
        rated_power <= 0
        or c.shape != (3,)
        or np.any(c < 0)
        or not np.isfinite(c).all()
        or not np.isfinite(p).all()
        or np.any(p < 0)
    ):
        raise ValueError(
            "positive rating, finite nonnegative power and three coefficients required"
        )
    u = p / rated_power
    loss = rated_power * (c[0] + c[1] * u + c[2] * u**2)
    return np.clip(np.divide(p - loss, p, out=np.zeros_like(p), where=p > 0), 0, 1)


def fit_efficiency(power_dc, power_ac, *, rated_power, minimum_load=0.05, maximum_load=0.95):
    """Fit nonnegative quadratic losses with a constrained classical solver.

    Use actual synchronized converter input/output measurements, excluding
    thermal limits and command limits. Available DC power is not actual DC input.
    Points near rated AC clipping are excluded automatically; measurement errors
    with AC>DC are rejected. The measured boundary includes any auxiliaries/meters.
    """
    dc, ac = finite_vectors(power_dc, power_ac, minimum_rows=10)
    if rated_power <= 0 or not 0 <= minimum_load < maximum_load <= 1:
        raise ValueError("invalid rating or load bounds")
    if np.any(dc < 0) or np.any(ac < 0) or np.any(ac > dc * 1.001 + 1):
        raise ValueError("invalid power or AC exceeds DC: check meter calibration/boundaries")
    mask = (
        (dc / rated_power >= minimum_load)
        & (dc / rated_power <= maximum_load)
        & (ac < 0.98 * rated_power)
    )
    dc, ac = dc[mask], ac[mask]
    if len(dc) < 10:
        raise ValueError("insufficient unclipped samples in the selected load domain")
    u = dc / rated_power
    design = np.column_stack((np.ones(len(u)), u, u**2))
    opt = lsq_linear(design, (dc - ac) / rated_power, bounds=(0, np.inf))
    diag = jacobian_diagnostics(design)
    identified = diag["rank"] == 3 and diag["condition_number"] < 1e6
    return InferenceResult(
        dict(zip(("loss_constant", "loss_linear", "loss_quadratic"), map(float, opt.x))),
        "classical_nonnegative_least_squares",
        float(np.sqrt(np.mean((design @ opt.x - (dc - ac) / rated_power) ** 2)) * rated_power),
        len(dc),
        status="estimated" if identified else "not_identifiable",
        units={"rmse": "W", "coefficients": "normalized loss"},
        diagnostics={
            **diag,
            "load_min": float(u.min()),
            "load_max": float(u.max()),
            "excluded_samples": int(len(mask) - mask.sum()),
            "rated_power_w": rated_power,
        },
        warnings=[
            "Effective field curve, not the manufacturer's certified efficiency map.",
            "No voltage or temperature dependence is inferred by this 1-D model.",
        ],
    )
