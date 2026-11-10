"""Lossless DC dispatch and independent physical checks for connected small grids."""

from collections.abc import Sequence
from dataclasses import dataclass
from time import perf_counter

import numpy as np
from scipy.optimize import linprog


@dataclass(frozen=True)
class Line:
    """Oriented AC line: susceptance in MW/radian, symmetric thermal limit in MW."""

    source: int
    target: int
    susceptance_mw_rad: float
    limit_mw: float


@dataclass(frozen=True)
class DispatchCase:
    """Single constant-power interval; all generation/load vectors are bus-aligned.

    Renewable dispatch is free; firm generation has the supplied EUR/MWh marginal
    cost. No load shedding, losses, reactive power, voltage or security constraints
    are modeled. Bounds and costs are assumptions, not market bids.
    """

    demand_mw: tuple[float, ...]
    renewable_mw: tuple[float, ...]
    firm_capacity_mw: tuple[float, ...]
    firm_cost_eur_mwh: tuple[float, ...]
    lines: tuple[Line, ...]
    hours: float = 1.0

    def __post_init__(self) -> None:
        for name in ("demand_mw", "renewable_mw", "firm_capacity_mw", "firm_cost_eur_mwh"):
            a = np.asarray(getattr(self, name), float)
            if a.ndim != 1 or not np.isfinite(a).all() or np.any(a < 0):
                raise ValueError(f"{name} must be finite and nonnegative")
            object.__setattr__(self, name, tuple(float(x) for x in a))
        n = len(self.demand_mw)
        if not 2 <= n <= 100 or any(
            len(getattr(self, k)) != n
            for k in ("renewable_mw", "firm_capacity_mw", "firm_cost_eur_mwh")
        ):
            raise ValueError("Supply matching vectors for 2..100 buses")
        if (
            isinstance(self.hours, bool)
            or not np.isfinite(self.hours)
            or not 0 < self.hours <= 168
        ):
            raise ValueError("hours must be finite in (0,168]")
        object.__setattr__(self, "lines", tuple(self.lines))
        if not 1 <= len(self.lines) <= 300:
            raise ValueError("Supply 1..300 lines")
        connected = {0}
        for line in self.lines:
            if (
                not isinstance(line, Line)
                or type(line.source) is not int
                or type(line.target) is not int
                or not 0 <= line.source < n
                or not 0 <= line.target < n
                or line.source == line.target
            ):
                raise ValueError("Invalid line endpoints")
            if (
                not np.isfinite(line.susceptance_mw_rad)
                or line.susceptance_mw_rad <= 0
                or not np.isfinite(line.limit_mw)
                or line.limit_mw < 0
            ):
                raise ValueError("Invalid line susceptance or rating")
        for _ in range(n):
            for line in self.lines:
                if line.source in connected or line.target in connected:
                    connected.update((line.source, line.target))
        if len(connected) != n:
            raise ValueError("Disconnected grids need explicit island modeling")


def network_matrices(case: DispatchCase) -> tuple[np.ndarray, np.ndarray]:
    """Return oriented flow-angle matrix H and nodal Laplacian A @ H."""
    a = np.zeros((len(case.demand_mw), len(case.lines)))
    for i, line in enumerate(case.lines):
        a[line.source, i], a[line.target, i] = 1, -1
    h = np.array([line.susceptance_mw_rad for line in case.lines])[:, None] * a.T
    return h, a @ h


def evaluate_dispatch(
    case: DispatchCase, renewable_mw: Sequence[float], firm_mw: Sequence[float]
) -> dict:
    """Re-solve DC angles from injections independently of the optimization state.

    Reject unbalanced injections; do not hide energy imbalance in the reference
    bus. Return line overload and generation-bound checks for every candidate.
    """
    r, g = np.asarray(renewable_mw, float), np.asarray(firm_mw, float)
    n = len(case.demand_mw)
    if r.shape != (n,) or g.shape != (n,) or not np.isfinite(r).all() or not np.isfinite(g).all():
        raise ValueError("Supply finite bus-aligned generation vectors")
    injection = r + g - case.demand_mw
    if abs(injection.sum()) > 1e-7:
        raise ValueError("Generation and demand must balance; no implicit slack injection")
    h, laplacian = network_matrices(case)
    theta = np.r_[0.0, np.linalg.solve(laplacian[1:, 1:], injection[1:])]
    flows = h @ theta
    overload = np.maximum(np.abs(flows) - [line.limit_mw for line in case.lines], 0)
    bounds = bool(
        np.all(r >= -1e-7)
        and np.all(g >= -1e-7)
        and np.all(r <= np.array(case.renewable_mw) + 1e-7)
        and np.all(g <= np.array(case.firm_capacity_mw) + 1e-7)
    )
    residual = float(np.max(np.abs(laplacian @ theta - injection)))
    return {
        "dc_feasible": bool(bounds and overload.max() <= 1e-7 and residual <= 1e-7),
        "renewable_mw": r.tolist(),
        "firm_mw": g.tolist(),
        "angles_rad": theta.tolist(),
        "line_flows_mw": flows.tolist(),
        "max_overload_mw": float(overload.max()),
        "balance_residual_mw": residual,
        "generation_bounds_met": bounds,
        "curtailed_mwh": float((np.array(case.renewable_mw) - r).sum() * case.hours),
        "firm_energy_cost_eur": float(g @ case.firm_cost_eur_mwh * case.hours),
    }


def solve_dispatch(case: DispatchCase, *, model: str = "dc") -> dict:
    """Solve DC, transport relaxation, or copperplate dispatch with HiGHS LP.

    Only DC honors both nodal balance and passive-line angle/flow relations.
    Relaxations are explicitly audited against DC physics after optimization.
    Infeasibility returns no fabricated dispatch. No shedding is introduced.
    """
    if model not in {"dc", "transport", "copperplate"}:
        raise ValueError("Unknown model")
    started = perf_counter()
    n, m = len(case.demand_mw), len(case.lines)
    h, laplacian = network_matrices(case)
    costs = np.r_[np.zeros(n), np.array(case.firm_cost_eur_mwh) * case.hours]
    bounds = [(0, x) for x in (*case.renewable_mw, *case.firm_capacity_mw)]
    ub, rhs = None, None
    if model == "dc":
        eq = np.c_[np.eye(n), np.eye(n), -laplacian]
        target = np.array(case.demand_mw)
        costs = np.r_[costs, np.zeros(n)]
        bounds += [(0, 0)] + [(None, None)] * (n - 1)
        row = np.c_[np.zeros((m, 2 * n)), h]
        ub = np.r_[row, -row]
        rhs = np.tile([line.limit_mw for line in case.lines], 2)
    elif model == "transport":
        a = np.zeros((n, m))
        for i, line in enumerate(case.lines):
            a[line.source, i], a[line.target, i] = 1, -1
        eq = np.c_[np.eye(n), np.eye(n), -a]
        target = np.array(case.demand_mw)
        costs = np.r_[costs, np.zeros(m)]
        bounds += [(-line.limit_mw, line.limit_mw) for line in case.lines]
    else:
        eq, target = np.ones((1, 2 * n)), [sum(case.demand_mw)]
    construction = perf_counter() - started
    start = perf_counter()
    result = linprog(costs, A_ub=ub, b_ub=rhs, A_eq=eq, b_eq=target, bounds=bounds, method="highs")
    timing = {
        "construction_s": construction,
        "solver_s": perf_counter() - start,
        "resources": {
            "buses": n,
            "lines": m,
            "lp_variables": len(costs),
            "constraint_matrix_bytes": eq.nbytes + (0 if ub is None else ub.nbytes),
        },
    }
    if result.status == 2:
        return {"model": model, "status": "infeasible", "physical": None, **timing}
    if not result.success:
        raise RuntimeError(f"LP failed with status {result.status}")
    physical = evaluate_dispatch(case, result.x[:n], result.x[n : 2 * n])
    if model == "dc" and not physical["dc_feasible"]:
        raise RuntimeError("DC solution failed independent physical validation")
    return {"model": model, "status": "optimal", "physical": physical, **timing}
