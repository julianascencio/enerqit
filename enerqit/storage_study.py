"""Reproducible battery portfolio research owned by EnerQit, optionally agent-led."""

import argparse
import hashlib
import json
from importlib.resources import files
from pathlib import Path
from time import perf_counter

import numpy as np

from enerqit.benchmarking import environment
from enerqit.solvers import exact, simulated_annealing, simulated_bifurcation
from enerqit.storage import (
    BatteryOffer,
    deliverable_capacity,
    enumerate_cover,
    evaluate_portfolio,
    portfolio_qubo,
    solve_cover_milp,
)


def battery_portfolio_case() -> dict:
    """Load the offline 10 November 2026 evidence and synthetic offer fixture."""
    return json.loads(files("enerqit").joinpath("data/battery_portfolio_20261110.json").read_text())


def _inputs(case):
    offers = [BatteryOffer(**row) for row in case["offers"]]
    target, duration = case["target_mw"], case["duration_hours"]
    capacities = deliverable_capacity(offers, duration)
    return offers, target, duration, capacities, [o.reservation_cost_gbp for o in offers]


def benchmark_portfolio(case: dict) -> dict:
    """Compare native and encoded optima plus fixed-budget stochastic candidates.

    Native subset enumeration is capped at 20 assets; encoded exact at 22 bits.
    This intentionally small comparison has no equal-runtime or speedup claim.
    Every candidate is physically evaluated independently of its QUBO penalty.
    """
    offers, target, duration, capacities, costs = _inputs(case)
    power = [r["deliverable_mw"] for r in capacities]
    native = solve_cover_milp(power, costs, target)
    enumeration = enumerate_cover(power, costs, target)
    if native["status"] != "optimal" or enumeration["status"] != "optimal":
        raise ValueError("The benchmark requires a feasible native cover")
    if not np.isclose(native["cost_gbp"], enumeration["cost_gbp"]):
        raise RuntimeError("Native optimum certificates disagree")
    native["physical"] = evaluate_portfolio(offers, native["selected"], target, duration)
    baseline = solve_cover_milp([r["power_only_mw"] for r in capacities], costs, target)
    baseline["physical"] = evaluate_portfolio(offers, baseline["selected"], target, duration)
    start = perf_counter()
    problem = portfolio_qubo(power, costs, target, step_mw=case["step_mw"])
    construction_s = perf_counter() - start
    encoded_optimum = exact(problem)
    candidates = [encoded_optimum]
    seeds = case["seeds"]
    if (not isinstance(seeds, list) or not seeds or len(seeds) > 20
            or any(type(s) is not int or s < 0 for s in seeds)):
        raise ValueError("Supply 1..20 nonnegative integer seeds")
    for seed in seeds:
        candidates.extend([simulated_annealing(problem, seed=seed, reads=32, sweeps=150),
                           simulated_bifurcation(problem, seed=seed, agents=64, steps=800)])
    records = []
    for candidate in candidates:
        physical = evaluate_portfolio(offers, candidate.x[:len(offers)], target, duration)
        row = candidate.to_dict()
        row.update({"physical": physical, "encoded_feasible": candidate.feasible,
                    "physical_feasible": physical["feasible"],
                    "construction_s": construction_s,
                    "total_s": construction_s + candidate.elapsed_s,
                    "qubo_energy_gap_gbp": candidate.energy - encoded_optimum.energy,
                    "native_cost_gap_gbp": physical["reservation_cost_gbp"] - native["cost_gbp"]
                    if physical["feasible"] else None})
        records.append(row)
    return {"capacities": capacities, "native_milp": native, "native_enumeration": enumeration,
            "power_only_baseline": baseline, "records": records, "environment": environment(),
            "qubo": {"variables": problem.size, "states": 2**problem.size,
                     "dense_matrix_bytes": problem.matrix.nbytes,
                     "sha256": hashlib.sha256(problem.matrix.tobytes() +
                                              np.array(problem.offset).tobytes()).hexdigest(),
                     **problem.metadata},
            "budgets": {"seeds": seeds, "sa_reads": 32, "sa_sweeps": 150,
                        "bsb_agents": 64, "bsb_steps": 800,
                        "shared_one_bit_polish": True, "equal_runtime": False},
            "quantum_hardware_used": False, "quantum_advantage_established": False}


def portfolio_sensitivity(case: dict) -> dict:
    """Re-optimize fixed synthetic quotes for duration, SOC buffer and grid step.

    Fees are deliberately held fixed across durations; this is physical resource
    sensitivity, not a duration-dependent tariff or market-price forecast.
    """
    offers, target, duration, capacities, costs = _inputs(case)
    output = {"duration": [], "soc_buffer": [], "discretization": []}
    for hours in (1, 2, 3, 4, 5, 6, 8, 12):
        power = [r["deliverable_mw"] for r in deliverable_capacity(offers, hours)]
        result = solve_cover_milp(power, costs, target)
        output["duration"].append({"duration_hours": hours, **result})
    for haircut in (0.0, 0.05, 0.10):
        power = [r["deliverable_mw"] for r in
                 deliverable_capacity(offers, duration, soc_haircut=haircut)]
        result = solve_cover_milp(power, costs, target)
        output["soc_buffer"].append({"withheld_soc_fraction": haircut, **result})
    power = [r["deliverable_mw"] for r in capacities]
    for step in (1.0, 5.0, 10.0, 20.0):
        # Solve the discretized feasible set natively, avoiding exponential bit enumeration.
        units = np.floor(np.array(power) / step)
        required = np.ceil(target / step)
        result = solve_cover_milp(units, costs, required)
        output["discretization"].append({"step_mw": step, **result})
    output["assumptions"] = "Fixed synthetic fees; deterministic SOC buffer, not a confidence interval"
    return output


def run_battery_engineer(case: dict | None = None, *, planner=None) -> dict:
    """Use the real energy-agents Quantum ML Engineer to execute this study.

    The default planner is deterministic, offline and explicitly scripted.
    No API key, paid service or quantum device is needed. Install the immutable
    optional integration from requirements/agent-study.txt before using it.
    """
    try:
        from energy_agents.quantum_ml import run_quantum_research_study
    except ImportError as exc:
        raise ImportError("Install: python -m pip install -r requirements/agent-study.txt") from exc
    case = battery_portfolio_case() if case is None else case

    def inspect(context):
        c = context["case"]
        return {"evidence": c["evidence"], "news_selection": c["news_selection"],
                "repository_awareness": c["repository_awareness"],
                "input_classification": c["input_classification"],
                "case_sha256": hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest()}

    def handoff(context):
        benchmark = context["reports"]["benchmark_methods"]
        native = benchmark["native_milp"]
        return {"recommended_method": "native_milp", "portfolio": native["physical"],
                "reason": "Native MILP avoids capacity quantization and certifies this small model; independent subset enumeration agrees.",
                "next_evidence": ["Validated asset-level SOC, usable energy and export headroom",
                                  "Actual availability fees and service qualification",
                                  "Network, ramp, recharge and degradation constraints"],
                "limitations": ["Synthetic portfolio; not a GB dispatch recommendation",
                                "Single constant-power block, no intertemporal operation",
                                "News motivation is not causal or field validation",
                                "No hardware execution or quantum advantage"],
                "execution_authorized": False}

    run = run_quantum_research_study(case, {
        "inspect_evidence": inspect,
        "benchmark_methods": lambda c: benchmark_portfolio(c["case"]),
        "assess_sensitivity": lambda c: portfolio_sensitivity(c["case"]),
        "prepare_handoff": handoff,
    }, planner=planner)
    if not run["success"]:
        raise RuntimeError(f"Engineer workflow failed: {run['trace']}")
    return run


def main():
    """Run the agent-led offline study and write its complete JSON evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/battery-engineer.json")
    args = parser.parse_args()
    result = run_battery_engineer()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result["reports"]["prepare_handoff"], indent=2))
    print(f"Complete evidence: {path}")


if __name__ == "__main__":
    main()
