"""Discrete ramp-constrained dispatch screening, with explicit spill accounting."""

from collections.abc import Sequence
from time import perf_counter

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import diags, eye, hstack, vstack


def plan_ramping(
    demand_mw: Sequence[float],
    hours: Sequence[float],
    ramp_window_hours: Sequence[float],
    *,
    capacity_mw: float,
    initial_mw: float,
    ramp_mw_per_hour: float,
    generation_eur_mwh: float = 50,
    shortage_eur_mwh: float = 1000,
) -> dict:
    """Minimize generation plus unserved-energy penalty using a sparse LP.

    Parameters
    ----------
    demand_mw : sequence of float
        Nonnegative residual demand in MW, after other scheduled resources.
    hours : sequence of float
        Positive energy-accounting durations for ordered intervals (hours).
    ramp_window_hours : sequence of float
        Positive transition budgets from previous setpoint, including initial
        output to first setpoint. Separate from energy durations deliberately.
    capacity_mw, initial_mw : float
        Online controllable capacity and preceding output in MW.
    ramp_mw_per_hour : float
        Symmetric change limit in MW per elapsed hour.
    generation_eur_mwh, shortage_eur_mwh : float
        Positive generation cost and unserved-energy penalty, EUR/MWh.

    Returns
    -------
    dict
        Optimized, causal tracking and capacity-only benchmarks, MW traces,
        MWh totals, EUR objectives, constraint residual and runtime seconds.

    Notes
    -----
    A discrete setpoint model, not continuous ramp integration. Output is held
    constant for energy accounting; transition energy is excluded. Perfect
    foresight, online resource, no startup/minimum output/network/storage limit.
    Surplus may be spilled at zero additional cost. No market dispatch authority.
    Bounds: at most 8760 intervals, MW <=1e6, hours <=8760, costs <=1e7.
    """
    d, h, w = [np.asarray(x, float) for x in (demand_mw, hours, ramp_window_hours)]
    if (
        d.ndim != 1
        or not 1 <= len(d) <= 8760
        or h.shape != d.shape
        or w.shape != d.shape
        or any(not np.isfinite(x).all() for x in (d, h, w))
        or np.any(d < 0)
        or np.any(d > 1e6)
        or np.any(h <= 0)
        or np.any(w <= 0)
        or np.any(h > 8760)
        or np.any(w > 8760)
    ):
        raise ValueError("Invalid finite MW/hour interval arrays")
    scalars = np.array(
        [capacity_mw, initial_mw, ramp_mw_per_hour, generation_eur_mwh, shortage_eur_mwh], float
    )
    if (
        not np.isfinite(scalars).all()
        or not 0 <= initial_mw <= capacity_mw <= 1e6
        or not 0 <= ramp_mw_per_hour <= 1e6
        or not 0 < generation_eur_mwh <= 1e7
        or not 0 < shortage_eur_mwh <= 1e7
    ):
        raise ValueError("Invalid capacity, initial output, ramp or costs")
    n = len(d)
    identity = eye(n, format="csr")
    delta = diags([np.ones(n), -np.ones(n - 1)], [0, -1], shape=(n, n), format="csr")
    zero = identity * 0
    initial = np.r_[initial_mw, np.zeros(n - 1)]
    start = perf_counter()
    solution = linprog(
        np.r_[h * generation_eur_mwh, h * shortage_eur_mwh],
        A_ub=vstack(
            [hstack([-identity, -identity]), hstack([delta, zero]), hstack([-delta, zero])],
            format="csr",
        ),
        b_ub=np.r_[-d, ramp_mw_per_hour * w + initial, ramp_mw_per_hour * w - initial],
        bounds=[(0, capacity_mw)] * n + list(zip(np.zeros(n), d)),
        method="highs",
    )
    if not solution.success:
        raise RuntimeError(solution.message)

    def account(p):
        u = np.maximum(d - p, 0)
        spill = np.maximum(p - d, 0)
        return dict(
            dispatch_mw=p.tolist(),
            unserved_mwh=float(u @ h),
            spill_mwh=float(spill @ h),
            generation_mwh=float(p @ h),
            objective_eur=float((p * generation_eur_mwh + u * shortage_eur_mwh) @ h),
        )

    p = solution.x[:n]
    violation = max(
        float(np.max(np.abs(np.diff(np.r_[initial_mw, p])) - ramp_mw_per_hour * w)),
        float(np.max(p - capacity_mw)),
        float(np.max(-p)),
        0,
    )
    if violation > 1e-6 or not np.isclose(
        account(p)["objective_eur"], solution.fun, rtol=1e-8, atol=1e-6
    ):
        raise RuntimeError("Independent physical/objective audit failed")
    causal = []
    previous = initial_mw
    for demand, window in zip(d, w):
        previous = float(
            np.clip(
                demand,
                max(0, previous - ramp_mw_per_hour * window),
                min(capacity_mw, previous + ramp_mw_per_hour * window),
            )
        )
        causal.append(previous)
    return dict(
        optimized=account(p),
        causal=account(np.array(causal)),
        capacity_only=account(np.minimum(d, capacity_mw)),
        max_constraint_violation_mw=violation,
        runtime_s=perf_counter() - start,
        solver="classical sparse HiGHS LP",
        variables=2 * n,
    )
