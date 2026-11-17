"""Discharge-only resource coordination behind a shared export connection."""

from collections.abc import Sequence
from time import perf_counter

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, eye, kron, vstack


def coordinate_export(
    power_mw: Sequence[float],
    energy_ac_mwh: Sequence[float],
    prices_eur_mwh: Sequence[float],
    hours: Sequence[float],
    connection_mw: Sequence[float],
) -> dict:
    """Maximize gross scenario export value, with no charging or terminal credit.

    Energy budgets are already deliverable AC MWh after losses/reserves. They
    are available at horizon start. This is not a hydraulic/head model, a battery
    arbitrage model, a market bid, or a forecast. Negative-price export is optional.
    Uses sparse native LP and independently audits power, energy and connection.
    """
    p, e, v, h, c = [
        np.asarray(x, dtype=float)
        for x in (power_mw, energy_ac_mwh, prices_eur_mwh, hours, connection_mw)
    ]
    if (
        any(x.ndim != 1 or not np.isfinite(x).all() for x in (p, e, v, h, c))
        or not 1 <= len(p) <= 64
        or e.shape != p.shape
        or not 1 <= len(v) <= 8760
        or h.shape != v.shape
        or c.shape != v.shape
        or np.any(p < 0)
        or np.any(e < 0)
        or np.any(h <= 0)
        or np.any(c < 0)
    ):
        raise ValueError("Invalid finite resource/interval arrays or units")
    n, t = len(p), len(v)
    a_energy = kron(eye(n, format="csr"), csr_matrix(h[None, :]), format="csr")
    a_grid = kron(csr_matrix(np.ones((1, n))), eye(t, format="csr"), format="csr")
    start = perf_counter()
    result = linprog(
        -np.tile(v * h, n),
        A_ub=vstack([a_energy, a_grid], format="csr"),
        b_ub=np.r_[e, c],
        bounds=list(zip(np.zeros(n * t), np.repeat(p, t))),
        method="highs",
    )
    if not result.success:
        raise RuntimeError(result.message)
    x = result.x.reshape(n, t)
    violation = max(
        float(np.max(-x)),
        float(np.max(x - p[:, None])),
        float(np.max(x @ h - e)),
        float(np.max(x.sum(axis=0) - c)),
        0.0,
    )
    if violation > 1e-6:
        raise RuntimeError("Physical feasibility audit failed")
    return {
        "dispatch_mw": x.tolist(),
        "export_mw": x.sum(axis=0).tolist(),
        "used_ac_mwh": (x @ h).tolist(),
        "gross_value_eur": float(x @ (v * h) @ np.ones(n)),
        "max_constraint_violation": violation,
        "runtime_s": perf_counter() - start,
        "solver": "classical HiGHS LP",
        "optimal": True,
    }


def compare_independent_export(
    power_mw: Sequence[float],
    energy_ac_mwh: Sequence[float],
    prices_eur_mwh: Sequence[float],
    hours: Sequence[float],
    connection_mw: Sequence[float],
) -> dict:
    """Compare coordinated LP with independent scheduling and proportional clipping.

    Clipping is a feasible no-rescheduling baseline; withheld energy is retained,
    not destroyed, and has no terminal value in this study. Independent requested
    value is infeasible whenever its aggregate schedule exceeds the connection.
    """
    joint = coordinate_export(power_mw, energy_ac_mwh, prices_eur_mwh, hours, connection_mw)
    independent = coordinate_export(
        power_mw, energy_ac_mwh, prices_eur_mwh, hours, [sum(power_mw)] * len(hours)
    )
    x = np.array(independent["dispatch_mw"])
    total = x.sum(axis=0)
    cap = np.array(connection_mw)
    ratio = np.minimum(1, np.divide(cap, total, out=np.ones_like(total), where=total > 0))
    clipped = x * ratio
    value = float(clipped.sum(axis=0) @ (np.array(hours) * prices_eur_mwh))
    return {
        "coordinated": joint,
        "independent_requested": independent,
        "independent_overload_mw": np.maximum(total - cap, 0).tolist(),
        "clipped_dispatch_mw": clipped.tolist(),
        "clipped_gross_value_eur": value,
        "coordination_value_eur": joint["gross_value_eur"] - value,
    }
