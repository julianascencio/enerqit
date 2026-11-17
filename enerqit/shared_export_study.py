"""Offline registered engineer study of a shared export bottleneck."""

import hashlib
import importlib.metadata
import json
from importlib.resources import files
from pathlib import Path

from enerqit.benchmarking import environment
from enerqit.shared_export import compare_independent_export, coordinate_export


def run_shared_export_study() -> dict:
    from energy_agents.quantum_ml import run_quantum_research_study

    raw = files("enerqit").joinpath("data/shared_export_20261117.json").read_bytes()
    d = json.loads(raw)
    a = d["inputs"]
    r = run_quantum_research_study(
        {
            "objective": "Coordinate stored-energy exports under a common connection limit",
            "classification": "mixed",
        },
        {
            "inspect_evidence": lambda _: d,
            "benchmark_methods": lambda _: compare_independent_export(**a),
            "assess_sensitivity": lambda _: {
                "connection": [
                    {
                        "connection_mw": cap,
                        **compare_independent_export(**dict(a, connection_mw=[cap] * 6)),
                    }
                    for cap in (25, 50, 75, 100)
                ],
                "energy": [
                    {
                        "energy_factor": f,
                        **coordinate_export(**dict(a, energy_ac_mwh=[50 * f, 100 * f])),
                    }
                    for f in (0.5, 1, 1.5)
                ],
                "scaling": [
                    {
                        "intervals": n,
                        **coordinate_export(
                            [50, 50],
                            [50, 100],
                            ([10, 100, 90, 20, 60, 30] * n)[:n],
                            [1] * n,
                            [50] * n,
                        ),
                    }
                    for n in (6, 24, 168)
                ],
            },
            "prepare_handoff": lambda _: {
                "quantum_used": False,
                "next_action": "Verify connection agreement, usable AC budgets, price forecasts, losses and terminal values before bidding",
                "limits": "Synthetic discharge-only perfect-price scenario; not Forbach calibration or realized trading revenue",
            },
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
    p = Path("results/shared-export.json")
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(run_shared_export_study(), indent=2, allow_nan=False) + "\n")
    print(p)
