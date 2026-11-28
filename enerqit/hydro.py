"""Constant-head single-reservoir dispatch with explicit water conservation."""

from collections.abc import Sequence
from dataclasses import dataclass
from time import perf_counter

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix


@dataclass(frozen=True)
class TerminalWaterValue:
    """Concave piecewise-linear value of usable terminal water, m3 and EUR.

    Knots start at (0, 0), strictly increase in volume, and have finite,
    nonnegative, nonincreasing marginal EUR/m3. At most 1000 knots. These are
    caller-supplied scenario values, not estimated prices or realized revenue.
    All represented inventory is valued, including water below a terminal floor.
    The curve must cover the reservoir's entire usable capacity; no extrapolation.
    """

    volumes_m3: tuple[float, ...]
    values_eur: tuple[float, ...]

    def __post_init__(self) -> None:
        x, y = np.asarray(self.volumes_m3, float), np.asarray(self.values_eur, float)
        if (
            x.ndim != 1
            or not 2 <= len(x) <= 1000
            or y.shape != x.shape
            or not np.isfinite(x).all()
            or not np.isfinite(y).all()
            or x[0] != 0
            or y[0] != 0
            or np.any(np.diff(x) <= 0)
        ):
            raise ValueError("Finite aligned knots starting at (0,0), increasing volumes required")
        slopes = np.diff(y) / np.diff(x)
        if not np.isfinite(slopes).all() or np.any(slopes < 0) or np.any(np.diff(slopes) > 0):
            raise ValueError("Marginal water values must be nonnegative and nonincreasing")
        object.__setattr__(self, "volumes_m3", tuple(x.tolist()))
        object.__setattr__(self, "values_eur", tuple(y.tolist()))

    def evaluate(self, volume_m3: float) -> float:
        """Interpolate EUR at a finite usable volume inside the curve domain."""
        if (
            isinstance(volume_m3, (bool, np.bool_))
            or not np.isscalar(volume_m3)
            or not np.isfinite(volume_m3)
            or not 0 <= volume_m3 <= self.volumes_m3[-1]
        ):
            raise ValueError("Volume outside terminal value domain")
        return float(np.interp(volume_m3, self.volumes_m3, self.values_eur))


def dispatch_reservoir(
    inflow_m3_s: Sequence[float],
    prices_eur_mwh: Sequence[float],
    hours: Sequence[float],
    minimum_release_m3_s: Sequence[float],
    *,
    initial_m3: float,
    capacity_m3: float,
    terminal_min_m3: float,
    turbine_m3_s: float,
    head_m: float,
    efficiency: float = 0.9,
    terminal_value: TerminalWaterValue | None = None,
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
    Optional terminal_value adds a caller-declared concave inventory valuation
    to gross energy value. The default None preserves the cash-only objective.
    Returned terminal_value_eur is NOT cash revenue; objective_value_eur is
    gross_value_eur plus this valuation. No initial inventory charge is applied
    (it is constant across policies with the same initial state).
    No variable head, evaporation, ramps, cascades, spillway limits or
    operational permission is modeled. Perfect-foresight LP,
    1..8760 intervals, O(n) sparse formulation; no quantum method used.
    """
    start = perf_counter()
    inflow, prices, h, release = [
        np.asarray(v, float) for v in (inflow_m3_s, prices_eur_mwh, hours, minimum_release_m3_s)
    ]
    if (
        inflow.ndim != 1
        or not 1 <= len(inflow) <= 8760
        or any(
            a.shape != inflow.shape or not np.isfinite(a).all()
            for a in (inflow, prices, h, release)
        )
        or np.any(inflow < 0)
        or np.any(release < 0)
        or np.any(h <= 0)
    ):
        raise ValueError("Aligned finite flows >=0, prices and positive hours required")
    values = (initial_m3, capacity_m3, terminal_min_m3, turbine_m3_s, head_m, efficiency)
    if any(
        isinstance(v, (bool, np.bool_)) or not np.isscalar(v) or not np.isfinite(v) or v < 0
        for v in values
    ):
        raise ValueError("Finite nonnegative physical scalars required")
    if max(initial_m3, terminal_min_m3) > capacity_m3 or head_m <= 0 or not 0 < efficiency <= 1:
        raise ValueError("Invalid reservoir bounds, head or efficiency")
    n = len(h)
    k = 1000 * 9.81 * head_m * efficiency / 3.6e9
    water, minimum, maximum = inflow * h * 3600, release * h * 3600, turbine_m3_s * h * 3600
    if not all(np.isfinite(a).all() for a in (water, minimum, maximum)) or not np.isfinite(k):
        raise ValueError("Overflow in unit conversion")
    if terminal_value is not None and not isinstance(terminal_value, TerminalWaterValue):
        raise ValueError("terminal_value must be TerminalWaterValue or None")
    segments = 0 if terminal_value is None else len(terminal_value.volumes_m3) - 1
    if terminal_value is not None and terminal_value.volumes_m3[-1] < capacity_m3:
        raise ValueError("Terminal curve must cover usable reservoir capacity")
    # Add one value variable z; hypograph z <= slope*S_final + intercept.
    size = 3 * n + 1 + int(segments > 0)
    eq, ub = lil_matrix((n, size)), lil_matrix((n + segments, size))
    for t in range(n):
        eq[t, t] = eq[t, n + t] = eq[t, 2 * n + t + 1] = 1
        eq[t, 2 * n + t] = -1
        ub[t, t] = ub[t, n + t] = -1
    bounds = [(0, float(v)) for v in maximum] + [(0, None)] * n
    bounds += [(initial_m3, initial_m3)] + [(0, capacity_m3)] * (n - 1)
    bounds += [(terminal_min_m3, capacity_m3)]
    c = np.r_[-prices * k, np.zeros(size - n)]
    rhs = -minimum
    if segments:
        x, y = np.array(terminal_value.volumes_m3), np.array(terminal_value.values_eur)
        slopes = np.diff(y) / np.diff(x)
        intercepts = y[:-1] - slopes * x[:-1]
        for j, slope in enumerate(slopes):
            ub[n + j, 3 * n] = -slope
            ub[n + j, -1] = 1
        rhs = np.r_[rhs, intercepts]
        bounds.append((0, None))
        c[-1] = -1
    result = linprog(
        c, A_eq=eq.tocsr(), b_eq=water, A_ub=ub.tocsr(), b_ub=rhs, bounds=bounds, method="highs"
    )
    info = {
        "runtime_s": perf_counter() - start,
        "variables": size,
        "constraint_nnz": eq.nnz + ub.nnz,
        "mwh_per_m3": k,
    }
    if result.status == 2:
        return {"status": "infeasible", **info}
    if not result.success:
        raise RuntimeError(result.message)
    q, bypass, s = result.x[:n], result.x[n : 2 * n], result.x[2 * n : 3 * n + 1]
    residual = np.diff(s) - water + q + bypass
    tol = 1e-6
    feasible = bool(
        np.max(abs(residual)) <= tol
        and min(q.min(), bypass.min(), s.min()) >= -tol
        and np.all(q <= maximum + tol)
        and np.all(q + bypass >= minimum - tol)
        and s.max() <= capacity_m3 + tol
        and abs(s[0] - initial_m3) <= tol
        and s[-1] >= terminal_min_m3 - tol
    )
    value = float((q * k) @ prices)
    terminal_eur = (
        0.0
        if terminal_value is None
        else terminal_value.evaluate(float(np.clip(s[-1], 0, capacity_m3)))
    )
    objective = value + terminal_eur
    if not feasible or not np.isclose(objective, -result.fun, rtol=1e-9, atol=1e-6):
        raise RuntimeError("Independent water/objective audit failed")
    return {
        "status": "optimal",
        "turbine_m3": q.tolist(),
        "bypass_m3": bypass.tolist(),
        "reservoir_m3": s.tolist(),
        "generation_mwh": (q * k).tolist(),
        "gross_value_eur": value,
        "terminal_value_eur": terminal_eur,
        "objective_value_eur": objective,
        "feasible": feasible,
        "max_water_residual_m3": float(np.max(abs(residual))),
        **info,
    }
