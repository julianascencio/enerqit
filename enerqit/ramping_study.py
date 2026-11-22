"""Registered engineer study of discrete ramp deliverability."""

import hashlib
import importlib.metadata
import json
from importlib.resources import files
from pathlib import Path

from enerqit.benchmarking import environment
from enerqit.ramping import plan_ramping


def run_ramping_study() -> dict:
    from energy_agents.quantum_ml import run_quantum_research_study

    raw = files("enerqit").joinpath("data/ramping_20261119.json").read_bytes()
    data = json.loads(raw)
    a = data["inputs"]
    r = run_quantum_research_study(
        {
            "objective": "Screen ramp-constrained pre-positioning cost and unserved energy",
            "classification": "synthetic",
        },
        {
            "inspect_evidence": lambda _: data,
            "benchmark_methods": lambda _: plan_ramping(**a),
            "assess_sensitivity": lambda _: dict(
                ramp={str(v): plan_ramping(**dict(a, ramp_mw_per_hour=v)) for v in [10, 20, 40]},
                penalty={
                    str(v): plan_ramping(**dict(a, shortage_eur_mwh=v)) for v in [40, 100, 1000]
                },
                scaling={
                    str(n): plan_ramping(
                        **dict(
                            a,
                            demand_mw=[0, 40, 40] * (n // 3),
                            hours=[1] * n,
                            ramp_window_hours=[1] * n,
                        )
                    )["runtime_s"]
                    for n in [3, 24, 168, 8760]
                },
            ),
            "prepare_handoff": lambda _: dict(
                quantum_used=False,
                limits="Synthetic discrete setpoint model; perfect foresight; no continuous ramp energy integration or unit commitment",
                next_action="Obtain operator ramp envelopes, transition conventions, forecast vintages and spill permission before field use",
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
    p = Path("results/ramping.json")
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(run_ramping_study(), indent=2, allow_nan=False) + "\n")
    print(p)
