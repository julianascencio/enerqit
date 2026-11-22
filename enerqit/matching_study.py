"""Actual registered engineer workflow for temporal matching procurement."""

import hashlib
import importlib.metadata
import json
from importlib.resources import files
from pathlib import Path

from enerqit.benchmarking import environment
from enerqit.matching import procure_matching


def run_matching_study() -> dict:
    from energy_agents.quantum_ml import run_quantum_research_study

    raw = files("enerqit").joinpath("data/matching_20261120.json").read_bytes()
    data = json.loads(raw)
    a = data["inputs"]
    r = run_quantum_research_study(
        {
            "objective": "Compare total-energy and simultaneous renewable procurement",
            "classification": "synthetic",
        },
        {
            "inspect_evidence": lambda _: data,
            "benchmark_methods": lambda _: dict(
                total_energy=procure_matching(**a, interval_matching=False),
                interval=procure_matching(**a),
            ),
            "assess_sensitivity": lambda _: dict(
                target={
                    str(f): procure_matching(**a, target_fraction=f)
                    for f in [0, 0.25, 0.5, 0.75, 1]
                },
                wind_cost={
                    str(c): procure_matching(**dict(a, costs_eur_per_mw=[500, c]))
                    for c in [750, 1500, 3000]
                },
                scaling={
                    str(n): procure_matching(
                        **dict(
                            a,
                            profiles=[[1, 0] * (n // 2), [0.5] * n],
                            demand_mw=[1] * n,
                            hours=[1] * n,
                        )
                    )["runtime_s"]
                    for n in [2, 24, 168, 8760]
                },
            ),
            "prepare_handoff": lambda _: dict(
                quantum_used=False,
                next_action="Acquire aligned site generation/load, contract terms and attribute ownership; validate independently",
                limits="Perfect-known synthetic profiles; no grid, storage, emissions or compliance model",
            ),
        },
    )
    if not r["success"]:
        raise RuntimeError(r["trace"])
    r["fixture_sha256"] = hashlib.sha256(raw).hexdigest()
    r["environment"] = environment()
    r["agent_install"] = json.loads(
        importlib.metadata.distribution("energy-agents").read_text("direct_url.json") or "{}"
    )
    return r


if __name__ == "__main__":
    p = Path("results/matching.json")
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(run_matching_study(), indent=2, allow_nan=False) + "\n")
    print(p)
