"""Actual engineer execution of bounded bidirectional storage readiness tools."""

import hashlib
import importlib.metadata
import itertools
import json
from dataclasses import replace
from importlib.resources import files
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.optimize import linprog

from enerqit.benchmarking import environment
from enerqit.storage_envelope import (
    ActivationWindow,
    initial_energy_envelope,
    prepare_activation,
    replay_activation,
)


def vertex_lp_reference(case: ActivationWindow) -> dict:
    """Small independent state-variable LP; enumerate box vertices, n <= 8.

    This benchmark is exponential and deliberately not the production method.
    Each path owns its boundary states but shares the initial-energy variable.
    Separate minimization/maximization finds the admissible initial interval.
    """
    n = len(case.hours)
    if n > 8:
        raise ValueError("Reference limited to eight intervals")
    start = perf_counter()
    paths = list(itertools.product(*zip(case.lower_mw, case.upper_mw)))
    size = 1 + len(paths) * n
    a, b = [], []
    for j, path in enumerate(paths):
        for t, p in enumerate(path):
            if p < -case.charge_mw or p > case.discharge_mw:
                return {"status": "infeasible", "runtime_s": perf_counter() - start}
            row = np.zeros(size)
            row[1 + j * n + t] = 1
            row[0 if t == 0 else j * n + t] = -1
            increment = (-p * case.charge_efficiency if p < 0
                         else -p / case.discharge_efficiency) * case.hours[t]
            a.append(row)
            b.append(increment)
    objective = np.zeros(size)
    objective[0] = 1
    results = [linprog(sign * objective, A_eq=a, b_eq=b,
                       bounds=(0, case.capacity_dc_mwh), method="highs") for sign in (1, -1)]
    if any(r.status == 2 for r in results):
        return {"status": "infeasible", "runtime_s": perf_counter() - start}
    if not all(r.success for r in results):
        raise RuntimeError("Reference LP did not solve")
    return {"status": "feasible", "initial_lower_dc_mwh": float(results[0].x[0]),
            "initial_upper_dc_mwh": float(results[1].x[0]),
            "variables": size, "paths": len(paths), "runtime_s": perf_counter() - start}


def run_activation_study() -> dict:
    from energy_agents.quantum_ml import run_quantum_research_study

    raw = files("enerqit").joinpath("data/activation_20261121.json").read_bytes()
    data = json.loads(raw)
    case = ActivationWindow(**data["inputs"])

    def benchmark(_):
        envelope = initial_energy_envelope(case)
        reference = vertex_lp_reference(case)
        gap = max(abs(envelope[k] - reference[k]) for k in
                  ("initial_lower_dc_mwh", "initial_upper_dc_mwh"))
        if gap > 1e-7:
            raise RuntimeError("Envelope disagrees with independent reference")
        prep = prepare_activation(case, data["initial_dc_mwh"], data["preparation_hours"])
        runs = {name: replay_activation(case, data["probe_ac_mw"], initial)
                for name, initial in (("full", 40), ("half", 20), ("empty", 0),
                                      ("prepared", prep["target_dc_mwh"]))}
        return {"envelope": envelope, "vertex_lp": reference, "max_reference_gap_mwh": gap,
                "probe_replays": runs, "preparation": prep,
                "preparation_fee_eur": (prep["import_ac_mwh"] + prep["export_ac_mwh"])
                * data["assumed_preparation_throughput_eur_per_ac_mwh"]}

    def sensitivity(_):
        return {
            "capacity": {str(e): initial_energy_envelope(replace(case, capacity_dc_mwh=e))
                         for e in (20, 30, 40, 60)},
            "efficiency": {str(e): initial_energy_envelope(replace(
                case, charge_efficiency=e, discharge_efficiency=e)) for e in (0.8, 0.9, 1)},
            "uncertainty_radius_mw": {str(w): initial_energy_envelope(replace(
                case, lower_mw=(-15-w, 15-w), upper_mw=(-15+w, 15+w)))
                for w in (0, 2.5, 5, 10)},
            "preparation_hours": {str(h): prepare_activation(case, 40, h) for h in (0, .5, 1)},
            "scaling": {str(n): initial_energy_envelope(replace(
                case, lower_mw=(-1,) * n, upper_mw=(1,) * n, hours=(1/12,) * n))
                for n in (2, 24, 288, 8760, 100000)},
        }

    result = run_quantum_research_study(
        {"objective": "Certify charging headroom and discharge readiness for every bounded activation",
         "classification": "synthetic"},
        {"inspect_evidence": lambda _: data, "benchmark_methods": benchmark,
         "assess_sensitivity": sensitivity,
         "prepare_handoff": lambda _: {
             "quantum_used": False,
             "algorithm": "Exact classical monotone cumulative bounds; classical LP reference",
             "limits": "Box guarantee only; no probability, correlated-path inference, grid dynamics or dispatch permission",
             "next_action": "Validate SOC/efficiencies, activation bounds, charging permission and preparation opportunity cost with independent asset/operator reviewers",
         }},
    )
    if not result["success"]:
        raise RuntimeError(result["trace"])
    result["fixture_sha256"] = hashlib.sha256(raw).hexdigest()
    result["environment"] = environment()
    result["seeds"] = {"study": None, "independent_test_instances": list(range(8))}
    result["timing_scope"] = "Envelope function including array conversion; dataclass construction excluded. Single-run diagnostics, not a speedup claim."
    result["agent_install"] = json.loads(
        importlib.metadata.distribution("energy-agents").read_text("direct_url.json") or "{}")
    return result


if __name__ == "__main__":
    path = Path("results/activation.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(run_activation_study(), indent=2, allow_nan=False) + "\n")
    print(path)
