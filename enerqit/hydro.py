"""Constant-head single-reservoir dispatch with explicit water conservation."""

from collections.abc import Sequence
from time import perf_counter

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix


def dispatch_reservoir(
    inflow_m3_s: Sequence[float], prices_eur_mwh: Sequence[float],
    hours: Sequence[float], minimum_release_m3_s: Sequence[float], *,
    initial_m3: float, capacity_m3: float, terminal_min_m3: float,
    turbine_m3_s: float, head_m: float, efficiency: float = .9,
) -> dict:
    """Maximize gross generation value subject to water and release constraints.

    Inputs are contiguous piecewise-constant intervals in UTC order; durations
    are elapsed hours. Positive inflow enters one usable reservoir. Turbine and
    bypass releases both count toward the assumed downstream minimum. Unlimited
    bypass is an explicit idealization. Head is constant, density 1000 kg/m3,
    gravity 9.81 m/s2; generation = volume*rho*g*head*efficiency/3.6e9 MWh.
    Initial/terminal/capacity values are usable cubic metres above dead storage.
    Prices are known scenario EUR/MWh, including negatives; not forecasts.

    Returns optimal/infeasible status, interval turbine/bypass m3, boundary
    reservoir m3, generation MWh, gross EUR and independent physical audit.
    No variable head, evaporation, ramps, cascades, spillway limits, terminal
    water value or operational permission is modeled. Perfect-foresight LP,
    1..8760 intervals, O(n) sparse formulation; no quantum method used.
    """
    start = perf_counter()
    inflow, prices, h, release = [np.asarray(v, float) for v in
                                (inflow_m3_s, prices_eur_mwh, hours, minimum_release_m3_s)]
    if (inflow.ndim != 1 or not 1 <= len(inflow) <= 8760
            or any(a.shape != inflow.shape or not np.isfinite(a).all()
                   for a in (inflow, prices, h, release))
            or np.any(inflow < 0) or np.any(release < 0) or np.any(h <= 0)):
        raise ValueError("Aligned finite flows >=0, prices and positive hours required")
    values = (initial_m3, capacity_m3, terminal_min_m3, turbine_m3_s, head_m, efficiency)
    if any(isinstance(v, (bool, np.bool_)) or not np.isscalar(v)
           or not np.isfinite(v) or v < 0 for v in values):
        raise ValueError("Finite nonnegative physical scalars required")
    if max(initial_m3, terminal_min_m3) > capacity_m3 or head_m <= 0 or not 0 < efficiency <= 1:
        raise ValueError("Invalid reservoir bounds, head or efficiency")
    n = len(h)
    k = 1000 * 9.81 * head_m * efficiency / 3.6e9
    water, minimum, maximum = inflow * h * 3600, release * h * 3600, turbine_m3_s * h * 3600
    if not all(np.isfinite(a).all() for a in (water, minimum, maximum)) or not np.isfinite(k):
        raise ValueError("Overflow in unit conversion")
    # Variables turbine[n], bypass[n], boundary storage[n+1].
    eq, ub = lil_matrix((n, 3*n+1)), lil_matrix((n, 3*n+1))
    for t in range(n):
        eq[t, t] = eq[t, n+t] = eq[t, 2*n+t+1] = 1
        eq[t, 2*n+t] = -1
        ub[t, t] = ub[t, n+t] = -1
    bounds = [(0, float(v)) for v in maximum] + [(0, None)] * n
    bounds += [(initial_m3, initial_m3)] + [(0, capacity_m3)] * (n-1)
    bounds += [(terminal_min_m3, capacity_m3)]
    c = np.r_[-prices*k, np.zeros(2*n+1)]
    result = linprog(c, A_eq=eq.tocsr(), b_eq=water, A_ub=ub.tocsr(),
                     b_ub=-minimum, bounds=bounds, method="highs")
    info = {"runtime_s": perf_counter()-start, "variables": 3*n+1,
            "constraint_nnz": 6*n, "mwh_per_m3": k}
    if result.status == 2:
        return {"status": "infeasible", **info}
    if not result.success:
        raise RuntimeError(result.message)
    q, bypass, s = result.x[:n], result.x[n:2*n], result.x[2*n:]
    residual = np.diff(s) - water + q + bypass
    tol = 1e-6
    feasible = bool(np.max(abs(residual)) <= tol and min(q.min(), bypass.min(), s.min()) >= -tol
                    and np.all(q <= maximum+tol) and np.all(q+bypass >= minimum-tol)
                    and s.max() <= capacity_m3+tol and abs(s[0]-initial_m3) <= tol
                    and s[-1] >= terminal_min_m3-tol)
    value = float((q*k) @ prices)
    if not feasible or not np.isclose(value, -result.fun, rtol=1e-9, atol=1e-6):
        raise RuntimeError("Independent water/objective audit failed")
    return {"status": "optimal", "turbine_m3": q.tolist(), "bypass_m3": bypass.tolist(),
            "reservoir_m3": s.tolist(), "generation_mwh": (q*k).tolist(),
            "gross_value_eur": value, "feasible": feasible,
            "max_water_residual_m3": float(np.max(abs(residual))), **info}
