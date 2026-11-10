"""Offline agent-led grid curtailment study; a convex problem needs no QUBO."""

import argparse
import hashlib
import importlib.metadata
import json
from dataclasses import asdict, replace
from importlib.resources import files
from pathlib import Path

from enerqit.benchmarking import environment
from enerqit.network import DispatchCase, Line, solve_dispatch


def network_case() -> DispatchCase:
    """Synthetic equal-reactance triangle, 150 MW renewable supply and demand."""
    data = json.loads(
        files("enerqit").joinpath("data/network_research_20261110.json").read_text()
    )["inputs"]
    return DispatchCase(**{**data, "lines": tuple(Line(**v) for v in data["lines"])})


def run_network_engineer() -> dict:
    """Invoke the existing role on evidence, convex benchmarks, sensitivity and handoff."""
    from energy_agents.quantum_ml import run_quantum_research_study

    evidence = json.loads(
        files("enerqit").joinpath("data/network_research_20261110.json").read_text()
    )
    case = network_case()

    def benchmark(context):
        return {
            model: solve_dispatch(case, model=model)
            for model in ("copperplate", "transport", "dc")
        }

    def sensitivity(context):
        upgrades = []
        for index in range(3):
            lines = list(case.lines)
            lines[index] = replace(lines[index], limit_mw=lines[index].limit_mw + 10)
            result = solve_dispatch(replace(case, lines=tuple(lines)))
            upgrades.append({"line_index": index, "added_rating_mw": 10, **result})
        availability = [
            dict(available_mw=v, **solve_dispatch(replace(case, renewable_mw=(v, 0, 0))))
            for v in (50, 100, 150, 200)
        ]
        # Physical scaling of the same instance; not a computational speedup experiment.
        scaling = [
            dict(
                scale=k,
                **solve_dispatch(
                    DispatchCase(
                        tuple(v * k for v in case.demand_mw),
                        tuple(v * k for v in case.renewable_mw),
                        tuple(v * k for v in case.firm_capacity_mw),
                        case.firm_cost_eur_mwh,
                        tuple(
                            replace(
                                line,
                                susceptance_mw_rad=line.susceptance_mw_rad * k,
                                limit_mw=line.limit_mw * k,
                            )
                            for line in case.lines
                        ),
                    )
                ),
            )
            for k in (0.1, 1, 10)
        ]
        cost_range = [
            dict(cost_eur_mwh=c, **solve_dispatch(replace(case, firm_cost_eur_mwh=(c, c, c))))
            for c in (50, 100, 200)
        ]
        size_scaling = []
        for n in (5, 20, 100):
            # Radial chain: independent min-cut is 40 MW; firm supply = 110 MW.
            chain = DispatchCase(
                (0,) * (n - 1) + (150,),
                (150,) + (0,) * (n - 1),
                (0,) * (n - 1) + (150,),
                (100,) * n,
                tuple(Line(i, i + 1, 1000, 40) for i in range(n - 1)),
            )
            size_scaling.append(solve_dispatch(chain))
        return {
            "upgrades": upgrades,
            "renewable_availability": availability,
            "physical_scaling": scaling,
            "firm_cost_range": cost_range,
            "size_scaling": size_scaling,
        }

    def handoff(context):
        return {
            "recommended_method": "classical DC linear programming",
            "baseline": context["reports"]["benchmark_methods"]["dc"]["physical"],
            "interpretation": "Upgrade value is avoided modeled firm energy cost in one hour, not annual revenue or investment NPV",
            "next_evidence": [
                "Licensed topology, reactance and line ratings",
                "Hourly generation, demand, outages and marginal costs",
                "AC power-flow, voltage and contingency validation",
            ],
            "quantum_method_used": False,
            "quantum_advantage_claimed": False,
            "execution_authorized": False,
        }

    result = run_quantum_research_study(
        {
            "objective": "Audit curtailment and line-upgrade value under passive-grid physics",
            "classification": "mixed",
        },
        {
            "inspect_evidence": lambda c: evidence,
            "benchmark_methods": benchmark,
            "assess_sensitivity": sensitivity,
            "prepare_handoff": handoff,
        },
    )
    if not result["success"]:
        raise RuntimeError(result["trace"])
    result["environment"] = environment()
    dist = importlib.metadata.distribution("energy-agents")
    result["agent_source"] = json.loads(dist.read_text("direct_url.json") or "{}")
    result["evidence_sha256"] = hashlib.sha256(
        files("enerqit").joinpath("data/network_research_20261110.json").read_bytes()
    ).hexdigest()
    result["agent_revision"] = evidence["agent_revision"]
    result["input_sha256"] = hashlib.sha256(
        json.dumps(asdict(case), sort_keys=True).encode()
    ).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/network-engineer.json")
    args = parser.parse_args()
    result = run_network_engineer()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result["reports"]["prepare_handoff"], indent=2))


if __name__ == "__main__":
    main()
