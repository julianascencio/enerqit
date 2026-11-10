"""Agent-led batch flexibility experiment with complete-horizon feasibility checks."""

import argparse
import hashlib
import importlib.metadata
import json
from dataclasses import replace
from importlib.resources import files
from math import prod
from pathlib import Path
from time import perf_counter

import numpy as np

from enerqit.benchmarking import environment
from enerqit.flexibility import (
    BatchJob,
    BatchProblem,
    GridScenario,
    batch_schedule_qubo,
    enumerate_batch_schedules,
    evaluate_batch_bits,
    evaluate_schedule,
    solve_batch_milp,
)
from enerqit.solvers import exact, simulated_annealing, simulated_bifurcation


def flexibility_case() -> dict:
    """Load dated source facts and wholly synthetic operational inputs offline."""
    return json.loads(files("enerqit").joinpath("data/batch_flexibility_20261110.json").read_text())


def problem_from_case(case: dict) -> BatchProblem:
    """Validate the fixture/caller's numerical inputs without interpreting news."""
    p = case["problem"]
    return BatchProblem(p["start_utc"], p["step_hours"], p["prices_eur_mwh"],
                        tuple(BatchJob(**j) for j in p["jobs"]),
                        tuple(GridScenario(**s) for s in p["scenarios"]))


def _candidate(problem, qubo, result, native_cost: float, construction_s: float) -> dict:
    physical = evaluate_batch_bits(problem, result.x[:qubo.metadata["choice_bits"]])
    return {**result.to_dict(), "physical": physical, "encoded_feasible": result.feasible,
            "physical_feasible": physical["feasible"], "construction_s": construction_s,
            "total_s": construction_s + result.elapsed_s,
            "native_cost_gap_eur": physical["energy_charge_eur"] - native_cost
            if physical["feasible"] else None}


def benchmark_flexibility(case: dict) -> dict:
    """Compare price-only, nominal-only, robust native and robust encoded schedules.

    Seeds/budgets are fixed before execution. Native oracle uses actual start
    combinations; exact QUBO enumerates all encoded states including slack.
    """
    problem = problem_from_case(case)
    native = solve_batch_milp(problem)
    oracle = enumerate_batch_schedules(problem)
    if native["status"] != "optimal" or oracle["status"] != "optimal":
        raise ValueError("Main benchmark needs a feasible robust case")
    native_cost = native["physical"]["energy_charge_eur"]
    if not np.isclose(native_cost, oracle["physical"]["energy_charge_eur"]):
        raise RuntimeError("Native optimization certificates disagree")
    price_only = solve_batch_milp(problem, enforce_grid=False)
    nominal = solve_batch_milp(replace(problem, scenarios=problem.scenarios[:1]))
    if nominal["status"] != "optimal":
        raise ValueError("Nominal-only ablation must be feasible")
    nominal["evaluated_on_all_scenarios"] = evaluate_schedule(
        problem, nominal["physical"]["starts"])
    earliest = evaluate_schedule(problem, [j.release_slot for j in problem.jobs])
    start = perf_counter()
    q = batch_schedule_qubo(problem, step_mw=case["step_mw"])
    construction_s = perf_counter() - start
    optimum = exact(q)
    seeds = case["seeds"]
    if (not isinstance(seeds, list) or not 1 <= len(seeds) <= 20
            or any(type(s) is not int or s < 0 for s in seeds)):
        raise ValueError("Supply 1..20 nonnegative integer seeds")
    runs = [optimum]
    for seed in seeds:
        runs.extend([simulated_annealing(q, seed=seed, reads=32, sweeps=150),
                     simulated_bifurcation(q, seed=seed, agents=64, steps=800)])
    records = [_candidate(problem, q, r, native_cost, construction_s) for r in runs]
    for row in records:
        row["qubo_energy_gap_eur"] = row["energy"] - optimum.energy
    env = environment()
    try:
        distribution = importlib.metadata.distribution("energy-agents")
        env["versions"]["energy-agents"] = distribution.version
        direct = json.loads(distribution.read_text("direct_url.json") or "{}")
        env["agent_source_revision"] = direct.get("vcs_info", {}).get("commit_id", "unknown")
    except importlib.metadata.PackageNotFoundError:
        env["versions"]["energy-agents"] = "not installed; core methods remain available"
    return {"native_milp": native, "native_enumeration": oracle,
            "price_only": price_only, "nominal_only": nominal, "earliest_start": earliest,
            "records": records, "environment": env,
            "economic_comparison": {
                "robust_minus_nominal_eur": native_cost - nominal["physical"]["energy_charge_eur"],
                "robust_minus_price_only_eur": native_cost - price_only["physical"]["energy_charge_eur"],
                "interpretation": "Synthetic cost of respecting constraints, not realized savings",
                "work_energy_mwh": native["physical"]["work_energy_mwh"]},
            "qubo": {"variables": q.size, "states": 2**q.size,
                     "dense_matrix_bytes": q.matrix.nbytes, **q.metadata,
                     "sha256": hashlib.sha256(q.matrix.tobytes()+np.array(q.offset).tobytes()).hexdigest()},
            "budgets": {"seeds": seeds, "sa_reads": 32, "sa_sweeps": 150,
                        "bsb_agents": 64, "bsb_steps": 800, "shared_one_bit_polish": True,
                        "equal_runtime": False}, "quantum_advantage_established": False}


def flexibility_sensitivity(case: dict) -> dict:
    """Stress deterministic margins/deadlines/encoding and measure modest scaling.

    Replicated cohorts test implementation resources, not independent real-site
    performance. No probability or confidence level is assigned to scenarios.
    """
    problem = problem_from_case(case)
    if problem.horizon != 6 or "Batch-C" not in {j.id for j in problem.jobs}:
        raise ValueError("This case-specific sensitivity requires six slots and Batch-C")
    margins, deadlines, steps, scaling = [], [], [], []
    for margin in (0, .25, .5, 1, 1.25):
        scenarios = tuple(replace(s, baseline_mw=tuple(v+margin for v in s.baseline_mw))
                          for s in problem.scenarios)
        result = solve_batch_milp(replace(problem, scenarios=scenarios))
        margins.append({"extra_baseline_mw": margin, **result})
    # Tighten only the explicitly named batch; no silent change to work energy.
    for deadline in (4, 5, 6):
        jobs = tuple(replace(j, deadline_slot=deadline) if j.id == "Batch-C" else j
                     for j in problem.jobs)
        deadlines.append({"batch_c_deadline_slot": deadline,
                          **solve_batch_milp(replace(problem, jobs=jobs))})
    for step in (.5, 1, 2):
        q = batch_schedule_qubo(problem, step_mw=step)
        result = exact(q)
        steps.append({"step_mw": step, "encoded_variables": q.size,
                      "encoded_feasible": result.feasible,
                      "physical": evaluate_batch_bits(problem, result.x[:q.metadata["choice_bits"]])})
    for copies in (1, 2, 4):
        jobs = tuple(replace(j, id=f"{j.id}-cohort-{i}")
                     for i in range(copies) for j in problem.jobs)
        scenarios = tuple(replace(s, baseline_mw=tuple(v*copies for v in s.baseline_mw),
                                  import_limit_mw=tuple(v*copies for v in s.import_limit_mw))
                          for s in problem.scenarios)
        expanded = replace(problem, jobs=jobs, scenarios=scenarios)
        native = solve_batch_milp(expanded)
        if native["status"] != "optimal":
            raise RuntimeError("Replicated cohort unexpectedly infeasible")
        start = perf_counter()
        q = batch_schedule_qubo(expanded, step_mw=case["step_mw"])
        construction_s = perf_counter() - start
        runs = [simulated_annealing(q, seed=0, reads=32, sweeps=150),
                simulated_bifurcation(q, seed=0, agents=64, steps=800)]
        scaling.append({"cohorts": copies, "jobs": len(jobs), "choice_bits": q.metadata["choice_bits"],
                        "qubo_variables": q.size, "dense_matrix_bytes": q.matrix.nbytes,
                        "native_combinations": prod(len(j.starts) for j in jobs),
                        "encoded_states": 2**q.size, "native_milp": native,
                        "heuristics": [_candidate(expanded, q, r,
                                       native["physical"]["energy_charge_eur"], construction_s)
                                       for r in runs]})
    return {"baseline_margin": margins, "deadline": deadlines, "discretization": steps,
            "scaling": scaling, "interpretation": "Deterministic assumptions, not calibrated risk bounds"}


def run_flexibility_engineer(case: dict | None = None, *, planner=None) -> dict:
    """Run the existing Quantum ML Engineer through trusted EnerQit callbacks."""
    try:
        from energy_agents.quantum_ml import run_quantum_research_study
    except ImportError as exc:
        raise ImportError("Install python -m pip install -r requirements/agent-study.txt") from exc
    case = flexibility_case() if case is None else case

    def evidence(context):
        c = context["case"]
        problem_from_case(c)
        return {"sources": c["sources"], "selection": c["selection"],
                "repository_awareness": c["repository_awareness"],
                "input_classification": c["input_classification"],
                "case_sha256": hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest()}

    def handoff(context):
        report = context["reports"]["benchmark_methods"]
        return {"recommended_method": "native_milp", "schedule": report["native_milp"]["physical"],
                "economic_comparison": report["economic_comparison"],
                "reason": "Certifies the stated native model without MW quantization or slack bits",
                "next_evidence": ["Metered job profiles and validated release/deadline constraints",
                                  "Contracted site import ceilings and baseline forecasts",
                                  "Actual supply tariff, taxes, demand charges and uncertainty data"],
                "limitations": ["Synthetic jobs, prices and limits; no observed Spanish site",
                                "Robust only to supplied baseline scenarios; no calibrated probability",
                                "No ramp, thermal, production precedence, staffing or network power flow",
                                "Cheap energy is not proof of renewable absorption or avoided emissions",
                                "No quantum hardware or advantage; no equipment commands"],
                "execution_authorized": False}

    result = run_quantum_research_study(case, {
        "inspect_evidence": evidence, "benchmark_methods": lambda c: benchmark_flexibility(c["case"]),
        "assess_sensitivity": lambda c: flexibility_sensitivity(c["case"]),
        "prepare_handoff": handoff,
    }, planner=planner)
    if not result["success"]:
        raise RuntimeError(f"Engineer workflow failed: {result['trace']}")
    return result


def main() -> None:
    """Write complete, finite JSON from a reproducible offline engineering run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/flexibility-engineer.json")
    args = parser.parse_args()
    result = run_flexibility_engineer()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps(result["reports"]["prepare_handoff"], indent=2))
    print(f"Complete evidence: {path}")


if __name__ == "__main__":
    main()
