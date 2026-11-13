"""Matched wall-budget experiments with audited native and encoded objectives."""

import tracemalloc
from time import perf_counter

import numpy as np

from enerqit.datasets import coupled_inventory
from enerqit.decomposition import block_coordinate
from enerqit.experiments import ExperimentRecord, fingerprint, write_records
from enerqit.qubo import QUBO
from enerqit.solvers import simulated_annealing, simulated_bifurcation
from enerqit.solvers.milp import native_milp


def problem_fingerprint(problem):
    """Identify the objective, constraints and groups, not just the QUBO matrix."""
    return fingerprint(
        {
            "matrix": problem.matrix.tolist(),
            "offset": problem.offset,
            "constraints": [(c.tolist(), h.tolist()) for c, h in problem.constraints],
            "groups": problem.groups,
        }
    )


def benchmark_case(
    problem,
    *,
    seconds=0.2,
    seeds=(0, 1, 2),
    reference_seconds=5.0,
    target_tolerance=1e-7,
    instance_id="provided",
    synthetic=False,
):
    """Compare native MILP, SA, bSB and boundary-aware blocks on paired inputs.

    Each method receives the same feasible warm start, computed from constraints
    only. The allotted search wall time includes each solver's preparation and
    polishing. Batches completed after the deadline are discarded and overruns
    retained. This is an admission deadline, not an OS preemption guarantee.
    Common preparation and verification are reported separately in total costs.
    The independent reference budget is excluded from contender search budgets.
    """
    if (
        not np.isfinite(seconds)
        or seconds <= 0
        or not np.isfinite(target_tolerance)
        or target_tolerance < 0
    ):
        raise ValueError("Positive budget and nonnegative finite target tolerance required")
    prepare_start = perf_counter()
    initial_result = native_milp(
        QUBO(np.zeros_like(problem.matrix), constraints=problem.constraints),
        time_limit_s=reference_seconds,
    )
    if initial_result["x"] is None:
        raise ValueError(
            "Cannot establish a common feasible warm start within the reference budget"
        )
    initial = initial_result["x"]
    preparation_s = perf_counter() - prepare_start
    reference = native_milp(problem, time_limit_s=reference_seconds)
    certified = reference["status"] == "optimal"
    target = reference["energy"] if certified else None
    digest = problem_fingerprint(problem)
    records = []
    methods = [
        "native_milp",
        "simulated_annealing",
        "ballistic_simulated_bifurcation",
        "block_coordinate",
    ]
    for seed in seeds:
        for method in np.random.default_rng(seed).permutation(methods):
            best = initial.copy()
            best_energy = float(problem.energy(best))
            history = [(0.0, best_energy)]
            status, error, solver_details = "feasible", None, {}
            completed_batches, late_batches = 0, 0
            tracemalloc.start()
            start = perf_counter()
            try:
                if method == "native_milp":
                    result = native_milp(problem, time_limit_s=seconds)
                    elapsed = perf_counter() - start
                    solver_details = {k: v for k, v in result.items() if k != "x"}
                    if result["status"] in {"timeout", "failed", "infeasible"}:
                        status = result["status"]
                    if elapsed <= seconds and result["x"] is not None:
                        best, best_energy = result["x"], result["energy"]
                        status = result["status"]
                        history.append((elapsed, best_energy))
                        completed_batches += 1
                    else:
                        late_batches += int(elapsed > seconds)
                elif method == "block_coordinate":
                    block_offset = perf_counter() - start
                    remaining = max(1e-9, seconds - block_offset)
                    result = block_coordinate(
                        problem,
                        initial,
                        seed=seed,
                        block_size=min(12, problem.size),
                        passes=100,
                        time_limit_s=remaining,
                    )
                    # Its internal trace admits only block solutions completed on time.
                    best, best_energy = result.x, result.energy
                    history.extend(
                        (r["elapsed_s"] + block_offset, r["objective"])
                        for r in result.metadata["trace"]
                        if r["accepted"]
                    )
                    completed_batches = len(result.metadata["trace"])
                    solver_details = {
                        "block_size": result.metadata["block_size"],
                        "certified": False,
                    }
                else:
                    batch = 0
                    while perf_counter() - start < seconds:
                        if method == "simulated_annealing":
                            candidate = simulated_annealing(
                                problem,
                                seed=seed * 100000 + batch,
                                reads=4,
                                sweeps=20,
                                initial=initial,
                            )
                        else:
                            candidate = simulated_bifurcation(
                                problem, seed=seed * 100000 + batch, agents=8, steps=60
                            )
                        valid = problem.feasible(candidate.x)
                        elapsed = perf_counter() - start
                        if elapsed > seconds:
                            late_batches += 1
                            break
                        completed_batches += 1
                        if valid and candidate.energy < best_energy:
                            best, best_energy = candidate.x.copy(), candidate.energy
                            history.append((elapsed, best_energy))
                        batch += 1
            except Exception as exc:
                status, error = "failed", f"{type(exc).__name__}: {exc}"
            elapsed_s = perf_counter() - start
            _, memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            verify_start = perf_counter()
            feasible = bool(problem.feasible(best))
            energy = float(problem.energy(best))
            verification_s = perf_counter() - verify_start
            hit_times = [
                t
                for t, value in history
                if target is not None and value <= target + target_tolerance
            ]
            metrics = {
                "instance": instance_id,
                "variables": problem.size,
                "budget_s": seconds,
                "budget_overrun_s": max(0.0, elapsed_s - seconds),
                "completed_batches": completed_batches,
                "late_batches_discarded": late_batches,
                "target_objective": target,
                "target_tolerance": target_tolerance,
                "target_hit": bool(hit_times) if target is not None else None,
                "time_to_target_s": min(hit_times) if hit_times else None,
                "certified_reference": certified,
                "reference_status": reference["status"],
                "reference_lower_bound": reference.get("lower_bound"),
                "reference_mip_relative_gap": reference.get("mip_relative_gap"),
                "reference_s": reference.get("elapsed_s", reference["construction_s"]),
                "absolute_gap": max(0.0, energy - target) if target is not None else None,
                "initial_objective": float(problem.energy(initial)),
                "solution": best.tolist(),
                "solver_details": solver_details,
            }
            record = ExperimentRecord(
                experiment="matched-budget",
                method=str(method),
                execution_kind="quantum_inspired"
                if method == "ballistic_simulated_bifurcation"
                else "classical",
                input_sha256=digest,
                seed=int(seed),
                status=status,
                feasible=feasible,
                objective=energy,
                timings_s={
                    "shared_preparation": preparation_s,
                    "search": elapsed_s,
                    "verification": verification_s,
                    "total": preparation_s + elapsed_s + verification_s,
                },
                resources={
                    "python_peak_bytes": memory,
                    "memory_scope": "tracemalloc; excludes native allocations",
                    "input_matrix_bytes": problem.matrix.nbytes,
                },
                metrics=metrics,
                error=error,
                provenance={
                    "synthetic": synthetic,
                    "warm_start": "constraint-only feasibility MILP; shared by every method",
                    "hardware": "CPU",
                    "budget_policy": "completed candidates only; soft batch deadline",
                },
            )
            records.append(record.to_dict())
    return records


def run_scaling_benchmark(
    output=None,
    *,
    groups=(4, 8, 16),
    seeds=(0, 1, 2),
    instance_seeds=(42, 43),
    seconds=0.2,
    reference_seconds=5.0,
):
    """Run growing 12/24/48-bit synthetic inference instances by default."""
    records = []
    for count in groups:
        for instance_seed in instance_seeds:
            start = perf_counter()
            problem, _, a, y = coupled_inventory(groups=count, seed=instance_seed)
            construction_s = perf_counter() - start
            rows = benchmark_case(
                problem,
                seconds=seconds,
                seeds=seeds,
                reference_seconds=reference_seconds,
                instance_id=f"groups-{count}-seed-{instance_seed}",
                synthetic=True,
            )
            for row in rows:
                x = np.asarray(row["metrics"]["solution"])
                row["metrics"]["signal_rmse"] = float(np.sqrt(np.mean((a @ x - y) ** 2)))
                row["timings_s"]["problem_construction"] = construction_s
                row["timings_s"]["total"] += construction_s
                row["provenance"]["instance_seed"] = instance_seed
            records.extend(rows)
    if output is not None:
        write_records(records, output)
    return records
