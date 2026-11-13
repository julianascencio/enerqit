"""Chronological, cyclic renewable firming with explicit AC/DC accounting."""

from collections.abc import Sequence
from dataclasses import dataclass
from time import perf_counter

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix


@dataclass(frozen=True)
class FirmingCase:
    """Repeated profile in chronological order; MW, hours, usable DC MWh.

    The initial stored energy is optimized but must equal final energy. This is
    steady periodic operation, not a cold start or an observed reliability year.
    """

    renewable_mw: tuple[float, ...]
    demand_mw: tuple[float, ...]
    power_mw: float
    max_energy_mwh: float
    hours: float = 1.0
    charge_efficiency: float = 0.9
    discharge_efficiency: float = 0.9

    def __post_init__(self) -> None:
        for key in ("renewable_mw", "demand_mw"):
            a = np.asarray(getattr(self, key), float)
            if (
                a.ndim != 1
                or not 1 <= len(a) <= 87840
                or not np.isfinite(a).all()
                or (a < 0).any()
            ):
                raise ValueError("Profiles must have 1..87840 finite nonnegative intervals")
            object.__setattr__(self, key, tuple(float(v) for v in a))
        if len(self.renewable_mw) != len(self.demand_mw):
            raise ValueError("Profiles must align")
        for key in (
            "power_mw",
            "max_energy_mwh",
            "hours",
            "charge_efficiency",
            "discharge_efficiency",
        ):
            v = getattr(self, key)
            if isinstance(v, bool) or not np.isfinite(v) or v <= 0:
                raise ValueError(f"{key} must be finite and positive")
        if max(self.charge_efficiency, self.discharge_efficiency) > 1:
            raise ValueError("Efficiencies must not exceed one")


def audit_firming(
    case: FirmingCase,
    charge_mw: Sequence[float],
    discharge_mw: Sequence[float],
    energy_mwh: Sequence[float],
    capacity_mwh: float,
) -> dict:
    """Reconstruct energy increments and load balance independently of matrices."""
    c, d, s = map(lambda v: np.asarray(v, float), (charge_mw, discharge_mw, energy_mwh))
    n = len(case.demand_mw)
    if (
        c.shape != (n,)
        or d.shape != (n,)
        or s.shape != (n + 1,)
        or not all(np.isfinite(a).all() for a in (c, d, s))
        or not np.isfinite(capacity_mwh)
    ):
        raise ValueError("Invalid dispatch arrays")
    residual = np.diff(s) - case.hours * (
        case.charge_efficiency * c - d / case.discharge_efficiency
    )
    spill = np.asarray(case.renewable_mw) + d - c - case.demand_mw
    simultaneous = float(np.max(np.minimum(c, d)))
    bounds = bool(
        min(c.min(), d.min(), s.min(), capacity_mwh) >= -1e-7
        and max(c.max(), d.max()) <= case.power_mw + 1e-7
        and s.max() <= capacity_mwh + 1e-7
        and capacity_mwh <= case.max_energy_mwh + 1e-7
    )
    return {
        "feasible": bool(
            bounds
            and np.max(abs(residual)) <= 1e-7
            and abs(s[-1] - s[0]) <= 1e-7
            and spill.min() >= -1e-7
            and simultaneous <= 1e-7
        ),
        "max_energy_residual_mwh": float(np.max(abs(residual))),
        "cycle_residual_mwh": float(s[-1] - s[0]),
        "simultaneous_mw": simultaneous,
        "spill_mwh": float(spill.sum() * case.hours),
        "shortfall_mwh": float(np.maximum(-spill, 0).sum() * case.hours),
        "conversion_loss_mwh": float(
            ((1 - case.charge_efficiency) * c + (1 / case.discharge_efficiency - 1) * d).sum()
            * case.hours
        ),
    }


def minimum_storage(
    case: FirmingCase,
    *,
    exclusive: bool = True,
    time_limit_s=30.0,
    net_balance_modes=False,
    allow_incomplete=False,
) -> dict:
    """Minimize usable DC capacity; fixed AC power, no backup or unserved load.

    Binary modes forbid simultaneous charge/discharge. exclusive=False gives a
    labeled LP lower bound, audited by the same physical evaluator. A finite
    max_energy_mwh is a search bound; infeasibility does not imply no larger
    battery can work. No stochastic solver or quantum algorithm is used.

    ``net_balance_modes=True`` fixes charge mode on renewable surplus and
    discharge mode on deficit, yielding a physical LP for this restricted model.
    With free curtailment, no grid charging, no export value and fixed demand,
    charging during a deficit or discharging during a surplus cannot reduce the
    minimum capacity. This reduction is not valid for arbitrary market dispatch.
    ``allow_incomplete=True`` retains timeout/failure metadata without accepting
    an unproven solution; the default preserves the original exception behavior.
    """
    if type(exclusive) is not bool:
        raise ValueError("exclusive must be boolean")
    if type(net_balance_modes) is not bool or type(allow_incomplete) is not bool:
        raise ValueError("Mode and incomplete flags must be boolean")
    if net_balance_modes and not exclusive:
        raise ValueError("Net-balance modes describe physical operation, not the relaxation")
    if isinstance(time_limit_s, bool) or not np.isfinite(time_limit_s) or time_limit_s <= 0:
        raise ValueError("time_limit_s must be finite and positive")
    start = perf_counter()
    n = len(case.demand_mw)
    # Variables c[n], d[n], s[n+1], E, mode[n]. Spill is eliminated.
    size = 4 * n + 2
    cap = 3 * n + 1
    lower = np.zeros(size)
    upper = np.full(size, np.inf)
    upper[: 2 * n] = case.power_mw
    upper[2 * n : cap + 1] = case.max_energy_mwh
    upper[cap + 1 :] = 1
    if net_balance_modes:
        mode = (np.asarray(case.renewable_mw) >= case.demand_mw).astype(float)
        lower[cap + 1 :] = mode
        upper[cap + 1 :] = mode
    row_indices, column_indices, coefficients = [], [], []
    lo = []
    hi = []

    def add(values, low, high):
        for j, v in values.items():
            row_indices.append(len(lo))
            column_indices.append(j)
            coefficients.append(v)
        lo.append(low)
        hi.append(high)

    for t in range(n):
        add(
            {
                t: -case.hours * case.charge_efficiency,
                n + t: case.hours / case.discharge_efficiency,
                2 * n + t: -1,
                2 * n + t + 1: 1,
            },
            0,
            0,
        )
        add({t: 1, n + t: -1}, -np.inf, case.renewable_mw[t] - case.demand_mw[t])
        add({t: 1, cap + 1 + t: -case.power_mw}, -np.inf, 0)
        add({n + t: 1, cap + 1 + t: case.power_mw}, -np.inf, case.power_mw)
    for t in range(n + 1):
        add({2 * n + t: 1, cap: -1}, -np.inf, 0)
    add({2 * n: 1, 3 * n: -1}, 0, 0)
    matrix = coo_matrix(
        (coefficients, (row_indices, column_indices)), shape=(len(lo), size)
    ).tocsc()
    objective = np.zeros(size)
    objective[cap] = 1
    integer = np.zeros(size)
    integer[cap + 1 :] = int(exclusive and not net_balance_modes)
    construction = perf_counter() - start
    start = perf_counter()
    result = milp(
        objective,
        integrality=integer,
        bounds=Bounds(lower, upper),
        constraints=LinearConstraint(matrix, lo, hi),
        options={"time_limit": time_limit_s, "mip_rel_gap": 1e-9},
    )
    info = {
        "method": "physical net-balance LP"
        if net_balance_modes
        else "MILP"
        if exclusive
        else "LP relaxation",
        "construction_s": construction,
        "solver_s": perf_counter() - start,
        "variables": size,
        "binary_variables": n if exclusive and not net_balance_modes else 0,
        "matrix_bytes": matrix.data.nbytes + matrix.indices.nbytes + matrix.indptr.nbytes,
        "matrix_nnz": matrix.nnz,
        "time_limit_s": time_limit_s,
    }
    if result.status == 2:
        return {"status": "infeasible", "audit": None, **info}
    if not result.success:
        if allow_incomplete:
            return {
                "status": "timeout" if result.status == 1 else "failed",
                "audit": None,
                "message": result.message,
                **info,
            }
        raise RuntimeError(f"Solver did not prove optimality: {result.message}")
    x = result.x
    audit = audit_firming(case, x[:n], x[n : 2 * n], x[2 * n : cap], x[cap])
    if exclusive and not audit["feasible"]:
        raise RuntimeError("Independent audit failed")
    return {
        "status": "optimal",
        "capacity_mwh": float(x[cap]),
        "charge_mw": x[:n].tolist(),
        "discharge_mw": x[n : 2 * n].tolist(),
        "energy_mwh": x[2 * n : cap].tolist(),
        "audit": audit,
        **info,
    }
