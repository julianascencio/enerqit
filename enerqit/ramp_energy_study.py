"""Bounded engineer execution of a continuous-ramp energy reconciliation."""

import hashlib
import importlib.metadata
import json
from importlib.resources import files
from pathlib import Path

import numpy as np

from enerqit.benchmarking import environment
from enerqit.ramp_energy import audit_linear_ramps
from enerqit.ramping import plan_ramping


def run_ramp_energy_study() -> dict:
    from energy_agents.quantum_ml import run_quantum_research_study

    raw = files("enerqit").joinpath("data/ramp_energy_20261127.json").read_bytes()
    data = json.loads(raw)

    def calculate(n=1, duration=1.0):
        return audit_linear_ramps(
            np.linspace(0, 40, n + 1),
            [40] * (n + 1),
            [duration / n] * n,
            capacity_mw=40,
            ramp_mw_per_hour=40,
        )

    def benchmark(_):
        discrete = plan_ramping([40], [1], [1], capacity_mw=40, initial_mw=0, ramp_mw_per_hour=40)
        return {
            "discrete": discrete,
            "continuous": calculate(),
            "interpretation": "Endpoint schedule reinterpreted as linear ramp, not an optimizer bug or continuous optimum",
        }

    r = run_quantum_research_study(
        {
            "objective": "Audit energy during a feasible ramp before accepting a shortage-free schedule",
            "classification": "synthetic",
        },
        {
            "inspect_evidence": lambda _: data,
            "benchmark_methods": benchmark,
            "assess_sensitivity": lambda _: {
                "duration": {str(h): calculate(duration=h) for h in (0.5, 1, 2)},
                "subdivision": {
                    str(n): {k: v for k, v in calculate(n).items() if not isinstance(v, list)}
                    for n in (1, 12, 60, 8760)
                },
            },
            "prepare_handoff": lambda _: {
                "quantum_used": False,
                "next_action": "Validate instantaneous telemetry and trajectory shape with operator; do not relabel interval averages as endpoints",
                "limits": "Linear interpolation assumption; scenario shortage penalty not realized loss; audit is not a continuous dispatch optimizer",
            },
        },
    )
    if not r["success"]:
        raise RuntimeError(r["trace"])
    r.update(
        fixture_sha256=hashlib.sha256(raw).hexdigest(),
        environment=environment(),
        seeds=list(range(6)),
    )
    r["agent_install"] = json.loads(
        importlib.metadata.distribution("energy-agents").read_text("direct_url.json") or "{}"
    )
    return r


if __name__ == "__main__":
    p = Path("results/ramp-energy.json")
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(run_ramp_energy_study(), indent=2, allow_nan=False) + "\n")
    print(p)
