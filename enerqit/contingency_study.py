"""Offline preventive-security study using the existing Quantum ML Engineer."""

import argparse
import hashlib
import importlib.metadata
import json
from dataclasses import replace
from importlib.resources import files
from pathlib import Path

from enerqit.benchmarking import environment
from enerqit.contingency import audit_outages, solve_preventive_dispatch
from enerqit.network import DispatchCase, Line, solve_dispatch
from enerqit.network_study import network_case


def run_contingency_engineer() -> dict:
    """Run evidence, benchmark, sensitivity and handoff through registered tools."""
    from energy_agents.quantum_ml import run_quantum_research_study

    raw = files("enerqit").joinpath("data/contingency_20261111.json").read_bytes()
    evidence = json.loads(raw)
    case = network_case()

    def benchmark(_):
        base = solve_dispatch(case)["physical"]
        derated = replace(
            case, lines=tuple(replace(line, limit_mw=line.limit_mw * 0.7) for line in case.lines)
        )
        margin = solve_dispatch(derated)["physical"]
        return {
            "base": base,
            "base_audit": audit_outages(case, base["renewable_mw"], base["firm_mw"]),
            "margin_70_percent": margin,
            "margin_audit": audit_outages(case, margin["renewable_mw"], margin["firm_mw"]),
            "preventive": solve_preventive_dispatch(case),
        }

    def sensitivity(_):
        scaling = []
        for n in (5, 10, 20):
            ring = DispatchCase(
                (0,) * (n - 1) + (150,),
                (150,) + (0,) * (n - 1),
                (0,) * (n - 1) + (150,),
                (100,) * n,
                tuple(Line(i, (i + 1) % n, 1000, 40) for i in range(n)),
            )
            result = solve_preventive_dispatch(ring)
            scaling.append(
                {
                    "buses": n,
                    "cost_eur": result["cost_eur"],
                    **{
                        k: result[k]
                        for k in (
                            "construction_s",
                            "solver_s",
                            "variables",
                            "inequality_rows",
                            "matrix_bytes",
                        )
                    },
                }
            )
        return {
            "size_scaling": scaling,
            "outage_ablations": [
                solve_preventive_dispatch(case, ids) for ids in ([], [0], [1], [2], [0, 1, 2])
            ],
            "rating_sweep": [
                {
                    "rating_mw": v,
                    **solve_preventive_dispatch(
                        replace(case, lines=(replace(case.lines[0], limit_mw=v), *case.lines[1:]))
                    ),
                }
                for v in (30, 40, 50, 80)
            ],
            "cost_sweep": [
                {
                    "firm_eur_mwh": v,
                    **solve_preventive_dispatch(replace(case, firm_cost_eur_mwh=(v, v, v))),
                }
                for v in (50, 100, 200)
            ],
        }

    run = run_quantum_research_study(
        {
            "objective": "Find minimum-cost fixed dispatch feasible for every selected line outage",
            "classification": "mixed",
        },
        {
            "inspect_evidence": lambda _: evidence,
            "benchmark_methods": benchmark,
            "assess_sensitivity": sensitivity,
            "prepare_handoff": lambda c: {
                "method": "classical preventive DC LP",
                "quantum_used": False,
                "modeled_security_premium_eur": c["reports"]["benchmark_methods"]["preventive"][
                    "cost_eur"
                ]
                - c["reports"]["benchmark_methods"]["base"]["firm_energy_cost_eur"],
                "next_action": "Obtain licensed topology, contingency lists and emergency ratings; validate AC and corrective response before operations",
                "limits": "Synthetic stationary hour; no realized revenue, no corrective redispatch or generator/islanding contingencies",
            },
        },
    )
    if not run["success"]:
        raise RuntimeError(run["trace"])
    run["environment"] = environment()
    run["agent_revision"] = evidence["agent_revision"]
    run["agent_install"] = json.loads(
        importlib.metadata.distribution("energy-agents").read_text("direct_url.json") or "{}"
    )
    run["source_fixture_sha256"] = hashlib.sha256(raw).hexdigest()
    run["numerical_fixture_sha256"] = hashlib.sha256(
        files("enerqit").joinpath("data/network_research_20261110.json").read_bytes()
    ).hexdigest()
    return run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/contingency-engineer.json")
    args = parser.parse_args()
    result = run_contingency_engineer()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result["reports"]["prepare_handoff"], indent=2))


if __name__ == "__main__":
    main()
