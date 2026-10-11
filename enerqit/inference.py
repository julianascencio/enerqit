"""Physical configuration inference with explicit classical baselines."""

import numpy as np
from scipy.optimize import differential_evolution, least_squares

from enerqit.pvsystem import WEATHER_CHANNELS, fixed_ac, solar_position, tracker_ac
from enerqit.quality import validate_frame
from enerqit.qubo import least_squares_qubo
from enerqit.results import InferenceResult
from enerqit.uncertainty import jacobian_diagnostics


def fit_orientation(
    frame,
    latitude,
    longitude,
    *,
    dc_capacity=100_000,
    ac_capacity=90_000,
    initial=(25, 180),
    bounds=((0, 0), (80, 360)),
):
    """Fit tilt and azimuth by bounded physical nonlinear least squares.

    ``frame`` requires weather channels and ``power_ac`` in W. Capacity,
    calibration, timestamps, losses and location are assumed known. Only GHI
    above 50 W/m² is fitted. This is not inference from AC power alone.
    """
    validate_frame(frame, (*WEATHER_CHANNELS, "power_ac"), minimum_rows=10)
    f = frame.loc[frame.ghi > 50]
    if len(f) < 10:
        raise ValueError("insufficient daylight observations")
    pos = solar_position(f, latitude, longitude)
    y = f.power_ac.to_numpy()

    def residual(theta):
        return (
            fixed_ac(
                f,
                latitude,
                longitude,
                *theta,
                dc_capacity=dc_capacity,
                ac_capacity=ac_capacity,
                position=pos,
            )
            - y
        ) / dc_capacity

    opt = least_squares(residual, initial, bounds=bounds, x_scale="jac")
    diagnostics = jacobian_diagnostics(opt.jac)
    warnings = ["Conditional on known capacities, irradiance calibration and loss model."]
    identified = diagnostics["rank"] == 2 and diagnostics["condition_number"] < 1e6
    if not identified:
        warnings.append("Local sensitivity is rank-deficient or ill-conditioned.")
    return InferenceResult(
        dict(zip(("tilt", "azimuth"), map(float, opt.x))),
        "classical_bounded_least_squares",
        float(np.sqrt(np.mean(residual(opt.x) ** 2)) * dc_capacity),
        len(f),
        status="estimated" if opt.success and identified else "not_identifiable",
        units={"tilt": "deg", "azimuth": "deg", "rmse": "W"},
        diagnostics={**diagnostics, "optimizer_success": bool(opt.success), "nfev": int(opt.nfev)},
        warnings=warnings,
    )


def fit_tracker(
    frame,
    latitude,
    longitude,
    *,
    dc_capacity=100_000,
    ac_capacity=90_000,
    axis_azimuth=180,
    seed=0,
    maxiter=50,
):
    """Fit GCR and rotation limit with a classical global optimizer.

    Axis orientation and backtracking=True are fixed. Low-sun coverage is
    needed; multiple equally good settings can remain observationally equivalent.
    """
    validate_frame(frame, (*WEATHER_CHANNELS, "power_ac"), minimum_rows=10)
    f = frame.loc[frame.ghi > 20]
    if len(f) < 10:
        raise ValueError("insufficient daylight observations")
    pos = solar_position(f, latitude, longitude)

    def residual(theta):
        return (
            tracker_ac(
                f,
                latitude,
                longitude,
                gcr=theta[0],
                max_angle=theta[1],
                axis_azimuth=axis_azimuth,
                dc_capacity=dc_capacity,
                ac_capacity=ac_capacity,
                position=pos,
            )
            - f.power_ac
        ) / dc_capacity

    opt = differential_evolution(
        lambda x: float(np.mean(residual(x) ** 2)),
        [(0.15, 0.65), (35, 75)],
        seed=seed,
        maxiter=maxiter,
        popsize=8,
        tol=1e-8,
        polish=True,
    )
    eps = np.array([1e-4, 1e-2])
    jac = np.column_stack(
        [
            (residual(opt.x + np.eye(2)[i] * eps[i]) - residual(opt.x - np.eye(2)[i] * eps[i]))
            / (2 * eps[i])
            for i in range(2)
        ]
    )
    diag = jacobian_diagnostics(jac)
    status = (
        "estimated" if diag["rank"] == 2 and diag["condition_number"] < 1e6 else "not_identifiable"
    )
    return InferenceResult(
        {"gcr": float(opt.x[0]), "max_angle": float(opt.x[1])},
        "classical_differential_evolution",
        float(np.sqrt(opt.fun) * dc_capacity),
        len(f),
        status=status,
        units={"gcr": "1", "max_angle": "deg", "rmse": "W"},
        diagnostics={
            **diag,
            "optimizer_success": bool(opt.success),
            "nfev": int(opt.nfev),
            "seed": seed,
        },
        warnings=[
            "Conditional on known axis geometry and enabled backtracking.",
            "Local sensitivity does not establish a unique global solution.",
        ],
    )


def candidate_problem(predictions, observations, *, penalty=10.0):
    """Encode one discrete model choice as a one-hot QUBO with mean-square loss.

    The best classical baseline for this simple case is a direct argmin over
    candidates. Quantum-inspired solvers add overhead here; their research value
    lies in coupled groups and constraints, not this elementary selection task.
    """
    a, y = np.asarray(predictions, float), np.asarray(observations, float)
    scale = max(float(np.max(np.abs(y))), 1.0)
    return least_squares_qubo(
        a / scale,
        y / scale,
        weights=np.ones(len(y)) / len(y),
        groups=(tuple(range(a.shape[1])),),
        penalty=penalty,
    )
