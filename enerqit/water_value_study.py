"""Actual engineer study of the end-of-horizon reservoir depletion bias."""

import hashlib
import importlib.metadata
import json
from importlib.resources import files
from pathlib import Path

from enerqit.benchmarking import environment
from enerqit.hydro import TerminalWaterValue, dispatch_reservoir


def run_water_value_study() -> dict:
    from energy_agents.quantum_ml import run_quantum_research_study

    raw = files("enerqit").joinpath("data/water_value_20261123.json").read_bytes()
    data = json.loads(raw)
    a = data["inputs"]
    curve = TerminalWaterValue(**data["terminal_curve"])

    def benchmark(_):
        policies = {
            "cash_only": dispatch_reservoir(**a),
            "fixed_floor": dispatch_reservoir(**dict(a, terminal_min_m3=60000)),
            "water_value": dispatch_reservoir(**a, terminal_value=curve),
        }
        for r in policies.values():
            r["common_valuation_eur"] = curve.evaluate(r["reservoir_m3"][-1])
            r["common_score_eur"] = r["gross_value_eur"] + r["common_valuation_eur"]
        return policies

    result = run_quantum_research_study(
        {
            "objective": "Compare release policies under one common terminal-water valuation",
            "classification": "synthetic",
        },
        {
            "inspect_evidence": lambda _: data,
            "benchmark_methods": benchmark,
            "assess_sensitivity": lambda _: {
                "valuation_multiplier": {
                    str(f): dispatch_reservoir(
                        **a,
                        terminal_value=TerminalWaterValue(
                            curve.volumes_m3, tuple(y * f for y in curve.values_eur)
                        ),
                    )
                    for f in (0, 0.5, 1, 2)
                },
                "inflow_m3_s": {
                    str(v): dispatch_reservoir(
                        **dict(a, inflow_m3_s=[v] * 3), terminal_value=curve
                    )
                    for v in (0, 5, 10)
                },
                "scaling": {
                    str(n): dispatch_reservoir(
                        **dict(
                            a,
                            inflow_m3_s=[10] * n,
                            prices_eur_mwh=[50] * n,
                            hours=[1] * n,
                            minimum_release_m3_s=[5] * n,
                        ),
                        terminal_value=curve,
                    )["runtime_s"]
                    for n in (3, 24, 168, 8760)
                },
            },
            "prepare_handoff": lambda _: {
                "quantum_used": False,
                "limits": "Caller-assumed curve, constant head, perfect foresight, unlimited bypass; no realized revenue",
                "next_action": "Estimate continuation values on pre-decision data; validate on untouched later inflows/prices and review reservoir constraints",
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
    result["seeds"] = {"study": None, "independent_tests": list(range(6))}
    return result


if __name__ == "__main__":
    p = Path("results/water-value.json")
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(run_water_value_study(), indent=2, allow_nan=False) + "\n")
    print(p)
