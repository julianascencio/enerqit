"""Exact energy audit of continuous piecewise-linear power trajectories."""

from collections.abc import Sequence
from time import perf_counter

import numpy as np


def audit_linear_ramps(
    generation_mw: Sequence[float],
    demand_mw: Sequence[float],
    hours: Sequence[float],
    *,
    capacity_mw: float,
    ramp_mw_per_hour: float,
    generation_eur_mwh: float = 50,
    shortage_eur_mwh: float = 1000,
) -> dict:
    """Integrate generation, demand, shortage and spill exactly between boundaries.

    Power arrays contain n+1 instantaneous boundary MW values; hours contains n
    positive elapsed UTC interval durations. Both trajectories interpolate
    linearly. Interval-average measurements must NOT be passed as boundary data.
    Costs are constant scenario EUR/MWh, not settlement prices or realized losses.
    At most 8760 intervals; power <=1e6 MW, 1e-6 <= duration <=8760 h, costs <=1e7.
    Returns per-interval MWh and totals, EUR objective, feasibility and runtime.
    Violating trajectories are reported, not repaired. Capacity and ramp bounds
    hold everywhere iff they hold at endpoints/slopes for this interpolation.
    No startup, network, storage, uncertainty or operational authority is modeled.
    """
    start = perf_counter()
    p, d, h = [np.asarray(v, float) for v in (generation_mw, demand_mw, hours)]
    if (
        h.ndim != 1
        or not 1 <= h.size <= 8760
        or p.shape != (h.size + 1,)
        or d.shape != p.shape
        or any(not np.isfinite(a).all() for a in (p, d, h))
        or np.any(h < 1e-6)
        or np.any(h > 8760)
        or np.any(p < 0)
        or np.any(d < 0)
        or np.any(p > 1e6)
        or np.any(d > 1e6)
    ):
        raise ValueError("Finite nonnegative boundary MW and positive interval hours required")
    scalars = (capacity_mw, ramp_mw_per_hour, generation_eur_mwh, shortage_eur_mwh)
    if any(
        isinstance(v, (bool, np.bool_))
        or not np.isscalar(v)
        or not np.isfinite(v)
        or not 0 <= v <= 1e7
        for v in scalars
    ):
        raise ValueError("Finite nonnegative bounds and costs required")
    a, b = d[:-1] - p[:-1], d[1:] - p[1:]
    # Positive-part integral: trapezoid on same-sign endpoints, triangle on crossings.
    shortage = h * (np.maximum(a, 0) + np.maximum(b, 0)) / 2
    crossing = a * b < 0
    shortage[crossing] = (
        h[crossing]
        * np.maximum(a[crossing], b[crossing]) ** 2
        / (2 * np.abs(b[crossing] - a[crossing]))
    )
    generation = h * (p[:-1] + p[1:]) / 2
    demand = h * (d[:-1] + d[1:]) / 2
    spill = np.maximum(shortage + generation - demand, 0)
    capacity_violation = max(0.0, float(p.max() - capacity_mw))
    ramp_violation = max(0.0, float(np.max(np.abs(np.diff(p)) / h - ramp_mw_per_hour)))
    return dict(
        generation_mwh=generation.tolist(),
        demand_mwh=demand.tolist(),
        shortage_mwh=shortage.tolist(),
        spill_mwh=spill.tolist(),
        total_shortage_mwh=float(shortage.sum()),
        total_spill_mwh=float(spill.sum()),
        total_generation_mwh=float(generation.sum()),
        objective_eur=float(
            generation.sum() * generation_eur_mwh + shortage.sum() * shortage_eur_mwh
        ),
        feasible=capacity_violation <= 1e-8 and ramp_violation <= 1e-8,
        capacity_violation_mw=capacity_violation,
        ramp_violation_mw_per_hour=ramp_violation,
        runtime_s=perf_counter() - start,
    )
