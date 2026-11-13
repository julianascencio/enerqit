"""Offline wind/solar storage-sizing study through the existing engineer role."""

import argparse
import hashlib
import importlib.metadata
import json
from dataclasses import replace
from importlib.resources import files
from pathlib import Path

from enerqit.benchmarking import environment
from enerqit.storage_sizing import FirmingCase, minimum_storage


def run_firming_engineer() -> dict:
    """Execute four bounded registered tools with synthetic chronological profiles."""
    from energy_agents.quantum_ml import run_quantum_research_study

    raw = files("enerqit").joinpath("data/firming_20261113.json").read_bytes()
    evidence = json.loads(raw)
    inputs = evidence["inputs"]
    cases = {
        k: FirmingCase(
            tuple(v), tuple(inputs["demand_mw"]), inputs["power_mw"], inputs["max_energy_mwh"]
        )
        for k, v in inputs["profiles"].items()
    }

    def benchmark(_):
        return {
            k: {
                "physical": minimum_storage(p),
                "lp_lower_bound": minimum_storage(p, exclusive=False),
                "no_storage_shortfall_mwh": sum(
                    max(d - r, 0) * p.hours for d, r in zip(p.demand_mw, p.renewable_mw)
                ),
            }
            for k, p in cases.items()
        }

    def sensitivity(_):
        p = cases["complementary_mix"]
        return {
            "efficiency": [
                {
                    "eta": v,
                    **minimum_storage(replace(p, charge_efficiency=v, discharge_efficiency=v)),
                }
                for v in (0.8, 0.9, 1)
            ],
            "power": [
                {"power_mw": v, **minimum_storage(replace(p, power_mw=v))} for v in (0.2, 0.5, 2)
            ],
            "lull": minimum_storage(
                replace(p, renewable_mw=tuple(v * 0.5 for v in p.renewable_mw))
            ),
            "scaling": [
                {
                    "intervals": 4 * k,
                    **minimum_storage(
                        replace(p, renewable_mw=p.renewable_mw * k, demand_mw=p.demand_mw * k)
                    ),
                }
                for k in (1, 6, 24)
            ],
        }

    run = run_quantum_research_study(
        {
            "objective": "Size cyclic usable battery energy for renewable firming at fixed AC power",
            "classification": "mixed",
        },
        {
            "inspect_evidence": lambda _: evidence,
            "benchmark_methods": benchmark,
            "assess_sensitivity": sensitivity,
            "prepare_handoff": lambda c: {
                "method": "classical MILP; LP lower bound",
                "quantum_used": False,
                "capacity_reduction_mwh": c["reports"]["benchmark_methods"]["solar_only"][
                    "physical"
                ]["capacity_mwh"]
                - c["reports"]["benchmark_methods"]["complementary_mix"]["physical"][
                    "capacity_mwh"
                ],
                "next_action": "Licensed chronological multi-year co-located wind, solar and demand; evaluate lulls, reserve and lifecycle costs",
                "limits": "Synthetic periodic four-hour horizon, not annual reliability or replicated global economics",
            },
        },
    )
    if not run["success"]:
        raise RuntimeError(run["trace"])
    run["environment"] = environment()
    run["fixture_sha256"] = hashlib.sha256(raw).hexdigest()
    run["agent_install"] = json.loads(
        importlib.metadata.distribution("energy-agents").read_text("direct_url.json") or "{}"
    )
    return run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/firming-engineer.json")
    args = parser.parse_args()
    result = run_firming_engineer()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result["reports"]["prepare_handoff"], indent=2))


if __name__ == "__main__":
    main()
