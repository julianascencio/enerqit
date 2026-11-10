"""Deadline-constrained batch demand under scenario-specific grid import ceilings.

Profiles are incremental AC MW. Jobs run once, without interruption or migration.
The same advance schedule must work in every supplied baseline-load scenario.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import product
from math import prod
from time import perf_counter
from typing import Sequence

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from enerqit.qubo import QUBO


def _vector(values, name: str, *, nonnegative: bool = True) -> tuple[float, ...]:
    a = np.asarray(values, dtype=float)
    if (a.ndim != 1 or not 1 <= len(a) <= 168 or not np.isfinite(a).all()
            or np.any(np.abs(a) > 1e6) or (nonnegative and np.any(a < 0))):
        raise ValueError(f"{name} must be a finite bounded vector of length 1..168")
    return tuple(float(v) for v in a)


def _integer(value: int, name: str, lower: int, upper: int) -> None:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer in {lower}..{upper}")


@dataclass(frozen=True)
class BatchJob:
    """Fixed AC MW profile; release inclusive and completion deadline exclusive.

    A start at k consumes profile[j] in slot k+j. Finishing exactly at deadline
    is permitted. There is no optional dropping, interruption or variable speed.
    """

    id: str
    profile_mw: tuple[float, ...]
    release_slot: int
    deadline_slot: int

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Job ID must be nonempty")
        object.__setattr__(self, "profile_mw", _vector(self.profile_mw, "profile_mw"))
        if not any(self.profile_mw):
            raise ValueError("A job must perform positive-energy work")
        _integer(self.release_slot, "release_slot", 0, 167)
        _integer(self.deadline_slot, "deadline_slot", 1, 168)
        if self.deadline_slot - self.release_slot < len(self.profile_mw):
            raise ValueError("Job cannot finish within its release/deadline window")

    @property
    def starts(self) -> range:
        """All allowed start slots, including the latest feasible start."""
        return range(self.release_slot, self.deadline_slot - len(self.profile_mw) + 1)


@dataclass(frozen=True)
class GridScenario:
    """A named deterministic baseline/ceiling pair, both at the AC import meter."""

    name: str
    baseline_mw: tuple[float, ...]
    import_limit_mw: tuple[float, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Scenario name must be nonempty")
        for field in ("baseline_mw", "import_limit_mw"):
            object.__setattr__(self, field, _vector(getattr(self, field), field))
        if len(self.baseline_mw) != len(self.import_limit_mw):
            raise ValueError("Baseline and ceiling horizons differ")


@dataclass(frozen=True)
class BatchProblem:
    """One UTC horizon, common prices/jobs and deterministic grid scenarios.

    Prices are EUR/MWh and may be negative. Only incremental batch energy cost is
    optimized; each scenario's inflexible energy bill is a schedule-independent
    constant. Grid limits, profile estimates and prices must be known or assumed
    at scheduling time; this model supplies neither forecasts nor SLA guarantees.
    """

    start_utc: str
    step_hours: float
    prices_eur_mwh: tuple[float, ...]
    jobs: tuple[BatchJob, ...]
    scenarios: tuple[GridScenario, ...]

    def __post_init__(self) -> None:
        instant = datetime.fromisoformat(self.start_utc.replace("Z", "+00:00"))
        if instant.utcoffset() != timedelta(0):
            raise ValueError("start_utc must have explicit UTC offset")
        if (isinstance(self.step_hours, bool) or not np.isfinite(self.step_hours)
                or not 1/60 <= self.step_hours <= 24):
            raise ValueError("step_hours must be finite in 1/60..24")
        object.__setattr__(self, "prices_eur_mwh", _vector(
            self.prices_eur_mwh, "prices_eur_mwh", nonnegative=False))
        object.__setattr__(self, "jobs", tuple(self.jobs))
        object.__setattr__(self, "scenarios", tuple(self.scenarios))
        if not 1 <= len(self.jobs) <= 32 or not all(isinstance(j, BatchJob) for j in self.jobs):
            raise ValueError("Supply 1..32 BatchJob objects")
        if (not 1 <= len(self.scenarios) <= 32
                or not all(isinstance(s, GridScenario) for s in self.scenarios)):
            raise ValueError("Supply 1..32 GridScenario objects")
        if len({j.id for j in self.jobs}) != len(self.jobs):
            raise ValueError("Job IDs must be unique")
        if len({s.name for s in self.scenarios}) != len(self.scenarios):
            raise ValueError("Scenario names must be unique")
        if any(j.deadline_slot > self.horizon for j in self.jobs):
            raise ValueError("Job deadline exceeds the complete horizon")
        if any(len(s.baseline_mw) != self.horizon for s in self.scenarios):
            raise ValueError("Scenario does not cover the complete horizon")
        if sum(len(j.starts) for j in self.jobs) > 512:
            raise ValueError("More than 512 start choices; shorten windows or decompose")

    @property
    def horizon(self) -> int:
        return len(self.prices_eur_mwh)

    @property
    def headroom_mw(self) -> np.ndarray:
        """Tightest capacity at each slot; exact for one shared schedule."""
        return np.min([np.subtract(s.import_limit_mw, s.baseline_mw)
                       for s in self.scenarios], axis=0)


def evaluate_schedule(problem: BatchProblem, starts: Sequence[int]) -> dict:
    """Rebuild demand from job profiles, independent of solver matrices.

    Report all scenario violations, energy conservation and incremental energy
    cost. Constraint violation is not unserved energy and schedules are advisory.
    """
    if len(starts) != len(problem.jobs):
        raise ValueError("Exactly one start is required for each job")
    demand = np.zeros(problem.horizon)
    for job, start in zip(problem.jobs, starts):
        if not isinstance(start, (int, np.integer)) or isinstance(start, (bool, np.bool_)):
            raise ValueError("Start slots must be integers")
        if start not in job.starts:
            raise ValueError("Start violates release or deadline")
        for offset, power in enumerate(job.profile_mw):
            demand[start + offset] += power
    scenarios = []
    for scenario in problem.scenarios:
        load = np.array(scenario.baseline_mw) + demand
        violation = np.maximum(load - scenario.import_limit_mw, 0)
        scenarios.append({"name": scenario.name, "grid_import_mw": load.tolist(),
                          "max_violation_mw": float(violation.max()),
                          "violation_mw": violation.tolist(),
                          "feasible": bool(np.max(violation) <= 1e-8)})
    return {"feasible": all(r["feasible"] for r in scenarios),
            "starts": [int(v) for v in starts], "job_ids": [j.id for j in problem.jobs],
            "incremental_mw": demand.tolist(),
            "work_energy_mwh": float(demand.sum() * problem.step_hours),
            "energy_charge_eur": float(np.dot(demand, problem.prices_eur_mwh) * problem.step_hours),
            "all_jobs_completed": True, "scenarios": scenarios,
            "max_violation_mw": max(r["max_violation_mw"] for r in scenarios)}


def batch_options(problem: BatchProblem) -> dict:
    """Compile allowed noninterruptible start profiles into native MILP columns."""
    columns, groups, options = [], [], []
    for job in problem.jobs:
        group = []
        for start in job.starts:
            column = np.zeros(problem.horizon)
            column[start:start+len(job.profile_mw)] = job.profile_mw
            group.append(len(columns))
            columns.append(column)
            options.append({"job_id": job.id, "start_slot": start})
        groups.append(tuple(group))
    profiles = np.column_stack(columns)
    return {"profiles": profiles, "groups": tuple(groups), "options": options,
            "costs": problem.step_hours * np.array(problem.prices_eur_mwh) @ profiles}


def evaluate_batch_bits(problem: BatchProblem, bits) -> dict:
    """Decode one-hot choices; invalid selections never become repaired schedules."""
    data = batch_options(problem)
    x = np.asarray(bits)
    if x.shape != (len(data["options"]),) or not np.isin(x, [0, 1]).all():
        raise ValueError("One binary value per start choice is required")
    counts = [int(x[list(g)].sum()) for g in data["groups"]]
    if any(n != 1 for n in counts):
        return {"feasible": False, "all_jobs_completed": False,
                "selection_counts": counts, "energy_charge_eur": None, "starts": None}
    starts = [data["options"][next(i for i in g if x[i])]["start_slot"] for g in data["groups"]]
    return {**evaluate_schedule(problem, starts), "selection_counts": counts}


def solve_batch_milp(problem: BatchProblem, *, enforce_grid: bool = True) -> dict:
    """Minimize incremental energy charges with native MW grid inequalities.

    ``enforce_grid=False`` is a labelled price-only ablation. Its result is still
    evaluated against the actual grid limits. No candidate is returned as optimal
    after a timeout or solver failure. Infeasibility is returned explicitly.
    """
    if type(enforce_grid) is not bool:
        raise ValueError("enforce_grid must be boolean")
    begun = perf_counter()
    data = batch_options(problem)
    n = len(data["costs"])
    groups = np.zeros((len(problem.jobs), n))
    for row, indices in enumerate(data["groups"]):
        groups[row, list(indices)] = 1
    constraints = [LinearConstraint(groups, 1, 1)]
    if enforce_grid:
        constraints.append(LinearConstraint(data["profiles"], -np.inf, problem.headroom_mw))
    construction_s = perf_counter() - begun
    start = perf_counter()
    result = milp(data["costs"], integrality=np.ones(n), bounds=Bounds(0, 1),
                  constraints=constraints, options={"time_limit": 30, "mip_rel_gap": 0.0})
    timings = {"construction_s": construction_s, "solver_s": perf_counter() - start}
    if result.status == 2:
        return {"status": "infeasible", "physical": None, **timings}
    if not result.success or result.x is None:
        raise RuntimeError(f"MILP not certified; solver status {result.status}")
    bits = np.rint(result.x).astype(int)
    physical = evaluate_batch_bits(problem, bits)
    if not physical["all_jobs_completed"] or (enforce_grid and not physical["feasible"]):
        raise RuntimeError("MILP failed independent schedule evaluation")
    return {"status": "optimal", "physical": physical, "bits": bits.tolist(),
            "grid_enforced": enforce_grid, "mip_gap": float(result.mip_gap), **timings}


def enumerate_batch_schedules(problem: BatchProblem, *, max_combinations: int = 1_000_000) -> dict:
    """Independent Cartesian enumeration of actual start times, without a QUBO."""
    _integer(max_combinations, "max_combinations", 1, 1_000_000)
    count = prod(len(j.starts) for j in problem.jobs)
    if count > max_combinations:
        raise ValueError("Native enumeration budget exceeded")
    start = perf_counter()
    best = None
    for starts in product(*(j.starts for j in problem.jobs)):
        physical = evaluate_schedule(problem, starts)
        if physical["feasible"] and (best is None or
                                     physical["energy_charge_eur"] < best["energy_charge_eur"]):
            best = physical
    return {"status": "optimal" if best is not None else "infeasible", "physical": best,
            "combinations": count, "solver_s": perf_counter() - start}


def batch_schedule_qubo(problem: BatchProblem, *, step_mw: float = 1.0) -> QUBO:
    """Encode one-hot job starts and conservative import ceilings with slack bits.

    Profiles round UP and headroom DOWN in MW steps. Redundant capacity rows are
    omitted using per-job maxima, valid under the explicit one-hot equalities.
    Shift each job's costs by its cheapest choice; all coefficients become
    nonnegative, even with negative prices. A penalty greater than the sum of
    per-job cost ranges separates every feasible optimum from infeasible states.
    """
    if (isinstance(step_mw, bool) or not np.isfinite(step_mw) or not 1e-3 <= step_mw <= 1e6):
        raise ValueError("step_mw must be finite in 1e-3..1e6")
    data = batch_options(problem)
    if np.any(problem.headroom_mw < 0):
        raise ValueError("Inflexible baseline already exceeds a grid ceiling")
    units = np.ceil(data["profiles"] / step_mw)
    capacity = np.floor(problem.headroom_mw / step_mw)
    if max(float(units.max()), float(capacity.max())) > 1_000_000:
        raise ValueError("Discretization exceeds one million power units")
    maximum = sum(np.max(units[:, g], axis=1) for g in data["groups"])
    active = np.flatnonzero(capacity < maximum)
    n = len(data["costs"])
    slack = {int(t): [2**i for i in range(int(capacity[t]).bit_length())] for t in active}
    size = n + sum(len(w) for w in slack.values())
    if size > 256:
        raise ValueError("Dense QUBO exceeds 256 variables; use native MILP or decompose")
    c = np.zeros((len(problem.jobs)+len(active), size))
    rhs = np.r_[np.ones(len(problem.jobs)), capacity[active]]
    shifted, offset, span = data["costs"].copy(), 0.0, 0.0
    for row, g in enumerate(data["groups"]):
        c[row, list(g)] = 1
        minimum = float(np.min(data["costs"][list(g)]))
        shifted[list(g)] -= minimum
        offset += minimum
        span += float(np.max(shifted[list(g)]))
    penalty = span + 1.0
    cursor = n
    for row, t in enumerate(active, start=len(problem.jobs)):
        c[row, :n] = units[t]
        weights = slack[int(t)]
        c[row, cursor:cursor+len(weights)] = weights
        cursor += len(weights)
    linear_cost = np.r_[shifted, np.zeros(size-n)]
    matrix = penalty * c.T @ c + np.diag(linear_cost - 2*penalty*c.T @ rhs)
    return QUBO(matrix, offset + penalty * float(rhs @ rhs), constraints=((c, rhs),),
                groups=data["groups"], metadata={
                    "kind": "deadline_constrained_batch_schedule", "choice_bits": n,
                    "slack_bits": size-n, "active_capacity_slots": active.tolist(),
                    "step_mw": float(step_mw), "penalty_eur": penalty,
                    "economic_offset_eur": offset, "shifted_costs_eur": shifted.tolist(),
                    "capacity_units": capacity.tolist(), "profile_units": units.tolist(),
                    "slack_weights": {str(t): w for t, w in slack.items()},
                    "rounding": "profile ceiling; headroom floor", "options": data["options"],
                    "convention": "full symmetric x.T @ Q @ x + offset"})
