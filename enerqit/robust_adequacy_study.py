"""Offline probability-ambiguity study using the registered engineer role."""

import hashlib
import importlib.metadata
import json
from importlib.resources import files
from pathlib import Path

from enerqit.benchmarking import environment
from enerqit.robust_adequacy import robust_capacity_offers, worst_case_eens


def run_robust_adequacy() -> dict:
    """Execute evidence, benchmark, sensitivity and handoff callbacks."""
    from energy_agents.quantum_ml import run_quantum_research_study

    raw = files("enerqit").joinpath("data/robust_adequacy_20261115.json").read_bytes()
    data = json.loads(raw)
    states = data["states"]
    offers = [(v, v * 100) for v in range(0, 101, 20)]
    result = run_quantum_research_study(
        {
            "objective": "Procure window reserve under probability ambiguity",
            "classification": "mixed",
        },
        {
            "inspect_evidence": lambda _: data,
            "benchmark_methods": lambda _: {
                str(r): robust_capacity_offers(states, 100, 4, offers, 20, r)
                for r in (0, 0.05, 0.1)
            },
            "assess_sensitivity": lambda _: {
                "radius": [
                    {"radius": r, **worst_case_eens(states, 100, hours=4, firm_mw=60, radius=r)}
                    for r in (0, 0.025, 0.05, 0.1, 0.2, 1)
                ],
                "scaling": [
                    {
                        "states": n,
                        **worst_case_eens(
                            [
                                {"available_mw": 100 * i / (n - 1), "probability": 1 / n}
                                for i in range(n)
                            ],
                            100,
                            radius=0.05,
                        ),
                    }
                    for n in (2, 16, 128)
                ],
            },
            "prepare_handoff": lambda _: {
                "next_action": "Calibrate support and ambiguity radius on licensed joint-outage evidence before procurement",
                "quantum_used": False,
                "limits": "Synthetic single window; radius is not statistical confidence",
            },
        },
    )
    if not result["success"]:
        raise RuntimeError(result["trace"])
    result["fixture_sha256"] = hashlib.sha256(raw).hexdigest()
    result["environment"] = environment()
    result["agent_install"] = json.loads(
        importlib.metadata.distribution("energy-agents").read_text("direct_url.json") or "{}"
    )
    return result


if __name__ == "__main__":
    p = Path("results/robust-adequacy.json")
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(run_robust_adequacy(), indent=2, allow_nan=False) + "\n")
    print(p)
