"""Registered engineer workflow for curtailment recovery accounting."""

import hashlib
import importlib.metadata
import json
from importlib.resources import files
from pathlib import Path
from time import perf_counter

from enerqit.benchmarking import environment
from enerqit.curtailment import recover_curtailment


def run_curtailment_study() -> dict:
    from energy_agents.quantum_ml import run_quantum_research_study

    raw = files("enerqit").joinpath("data/curtailment_20261118.json").read_bytes()
    data = json.loads(raw)
    a = data["inputs"]

    def benchmark(_):
        rows = {str(e): recover_curtailment(**dict(a, energy_dc_mwh=e)) for e in (0, 20, 40, 80)}
        return {
            "capacity_cases": rows,
            "illustrative_export_value_eur": {
                k: v["recovered_export_mwh"] * data["assumed_export_price_eur_mwh"]
                for k, v in rows.items()
            },
        }

    def sensitivity(_):
        scaling = []
        for n in (6, 24, 168, 8760):
            start = perf_counter()
            r = recover_curtailment(
                [50, 50, 0, 0, 0, 0] * (n // 6), [30] * n, [1] * n, power_mw=20, energy_dc_mwh=40
            )
            scaling.append(
                {
                    "intervals": n,
                    "runtime_s": perf_counter() - start,
                    "recovered_export_mwh": r["recovered_export_mwh"],
                }
            )
        return {
            "efficiency": {
                str(e): recover_curtailment(**dict(a, charge_efficiency=e, discharge_efficiency=e))
                for e in (0.8, 0.9, 1)
            },
            "no_later_headroom": recover_curtailment(
                **dict(a, export_limit_mw=[30, 30, 0, 0, 0, 0])
            ),
            "scaling": scaling,
        }

    r = run_quantum_research_study(
        {
            "objective": "Distinguish captured curtailment from delivered export value",
            "classification": "mixed",
        },
        {
            "inspect_evidence": lambda _: data,
            "benchmark_methods": benchmark,
            "assess_sensitivity": sensitivity,
            "prepare_handoff": lambda _: {
                "quantum_used": False,
                "next_action": "Verify charging permission and licensed interval-level generation, export limits and settlement terms",
                "limits": "Synthetic export-ceiling case; not Spanish grid stability simulation or realized savings",
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
    p = Path("results/curtailment-recovery.json")
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(run_curtailment_study(), indent=2, allow_nan=False) + "\n")
    print(p)
