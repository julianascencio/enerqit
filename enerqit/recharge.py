"""Minimum-cost recharge between mandatory battery service intervals."""

from collections.abc import Sequence
from time import perf_counter

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

from enerqit.storage_envelope import ActivationWindow, replay_activation


def plan_recharge(
    discharge_mw: Sequence[float],
    charge_limit_mw: Sequence[float],
    hours: Sequence[float],
    price_eur_mwh: Sequence[float],
    *,
    capacity_dc_mwh: float,
    initial_dc_mwh: float,
    discharge_limit_mw: float,
    terminal_dc_mwh: float = 0,
    charge_efficiency: float = 0.9,
    discharge_efficiency: float = 0.9,
) -> dict:
    """Minimize recharge purchase EUR while exactly delivering mandatory AC MW.

    Consecutive piecewise-constant UTC intervals, elapsed hours. Usable DC MWh
    exclude minimum SOC and other reservations. Import limits must be zero in
    every positive-discharge interval: split mixed intervals explicitly. All
    costs are nonnegative scenario EUR/MWh; negative-price arbitrage is excluded.
    Terminal inventory is a lower bound, not a value credited as revenue.
    Returns optimal/infeasible status, AC charging MW, DC states, purchase MWh,
    cost EUR and an independent replay audit. Perfect foresight; no startup,
    ramp, standby loss, degradation, network model or dispatch authorization.
    Bounds: 1..8760 intervals, powers/energy <=1e6, durations 1e-6..8760 hours,
    prices <=1e7 EUR/MWh, efficiencies .01..1. Sparse O(n) LP.
    """
    start = perf_counter()
    d, c, h, price = [
        np.asarray(x, float) for x in (discharge_mw, charge_limit_mw, hours, price_eur_mwh)
    ]
    if (
        d.ndim != 1
        or not 1 <= d.size <= 8760
        or any(x.shape != d.shape or not np.isfinite(x).all() for x in (c, h, price, d))
        or np.any(d < 0)
        or np.any(c < 0)
        or np.any(d > 1e6)
        or np.any(c > 1e6)
        or np.any(h < 1e-6)
        or np.any(h > 8760)
        or np.any(price < 0)
        or np.any(price > 1e7)
        or np.any((d > 0) & (c > 0))
    ):
        raise ValueError("Invalid aligned service, recharge, hour or price inputs")
    for v in (capacity_dc_mwh, initial_dc_mwh, terminal_dc_mwh, discharge_limit_mw):
        if (
            isinstance(v, (bool, np.bool_))
            or not np.isscalar(v)
            or not np.isfinite(v)
            or not 0 <= v <= 1e6
        ):
            raise ValueError("Invalid usable DC energy or discharge bound")
    for v in (charge_efficiency, discharge_efficiency):
        if (
            isinstance(v, (bool, np.bool_))
            or not np.isscalar(v)
            or not np.isfinite(v)
            or not 0.01 <= v <= 1
        ):
            raise ValueError("Efficiency must be in .01..1")
    if max(initial_dc_mwh, terminal_dc_mwh) > capacity_dc_mwh:
        raise ValueError("Inventory outside usable capacity")
    if np.any(d > discharge_limit_mw):
        return {
            "status": "infeasible",
            "reason": "discharge_power",
            "runtime_s": perf_counter() - start,
        }
    n = len(d)
    a = lil_matrix((n, 2 * n + 1))
    for t in range(n):
        a[t, t] = -h[t] * charge_efficiency
        a[t, n + t] = -1
        a[t, n + t + 1] = 1
    bounds = list(zip(np.zeros(n), c)) + [(initial_dc_mwh, initial_dc_mwh)]
    bounds += [(0, capacity_dc_mwh)] * (n - 1) + [(terminal_dc_mwh, capacity_dc_mwh)]
    sol = linprog(
        np.r_[h * price, np.zeros(n + 1)],
        A_eq=a.tocsr(),
        b_eq=-d * h / discharge_efficiency,
        bounds=bounds,
        method="highs",
    )
    if sol.status == 2:
        return {
            "status": "infeasible",
            "reason": "energy_or_recharge",
            "runtime_s": perf_counter() - start,
        }
    if not sol.success:
        raise RuntimeError(sol.message)
    q = sol.x[:n]
    signed = d - q
    case = ActivationWindow(
        tuple(signed),
        tuple(signed),
        tuple(h),
        float(c.max()),
        discharge_limit_mw,
        capacity_dc_mwh,
        charge_efficiency,
        discharge_efficiency,
    )
    replay = replay_activation(case, signed, initial_dc_mwh)
    states = np.asarray(replay["energy_dc_mwh"])
    cost = float(q @ (h * price))
    if (
        np.any(q < -1e-7)
        or np.any(q > c + 1e-7)
        or replay["missed_discharge_ac_mwh"] > 1e-7
        or replay["missed_absorption_ac_mwh"] > 1e-7
        or states[-1] < terminal_dc_mwh - 1e-7
        or not np.allclose(states, sol.x[n:], atol=1e-7, rtol=1e-9)
        or not np.isclose(cost, sol.fun, atol=1e-7, rtol=1e-9)
    ):
        raise RuntimeError("Independent activation or accounting audit failed")
    return {
        "status": "optimal",
        "charge_mw": q.tolist(),
        "energy_dc_mwh": states.tolist(),
        "purchase_ac_mwh": float(q @ h),
        "cost_eur": cost,
        "audit": replay,
        "variables": 2 * n + 1,
        "runtime_s": perf_counter() - start,
    }
