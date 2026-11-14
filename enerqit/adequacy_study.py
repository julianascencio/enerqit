"""Agent-led synthetic winter adequacy screen, not a regional forecast."""

import argparse
import hashlib
import importlib.metadata
import json
from importlib.resources import files
from pathlib import Path
from time import perf_counter

from enerqit.adequacy import CapacityUnit, capacity_states, screen_firm_capacity, window_risk
from enerqit.benchmarking import environment


def run_adequacy_engineer() -> dict:
    """Invoke current engineer role with four registered numerical study tools."""
    from energy_agents.quantum_ml import run_quantum_research_study

    raw = files("enerqit").joinpath("data/adequacy_20261114.json").read_bytes()
    evidence = json.loads(raw)
    inputs = evidence["inputs"]
    units = tuple(CapacityUnit(**u) for u in inputs["units"])
    q = inputs["common_outage_probability"]
    demand = inputs["demand_mw"]
    hours = inputs["hours"]
    states = capacity_states(units, q)
    independent = capacity_states(
        tuple(CapacityUnit(u.capacity_mw, q + (1 - q) * u.outage_probability) for u in units)
    )
    offers = [tuple(v) for v in inputs["offers"]]

    def benchmark(_):
        correlated = window_risk(states, demand, hours=hours)
        return {
            "correlated": correlated,
            "matched_marginal_independence": window_risk(independent, demand, hours=hours),
            "nameplate_shortfall_mwh": max(demand - sum(u.capacity_mw for u in units), 0) * hours,
            "mean_capacity_shortfall_mwh": max(demand - correlated["mean_available_mw"], 0)
            * hours,
            "correlated_procurement": screen_firm_capacity(
                states, demand, hours, offers, inputs["target_eens_mwh"]
            ),
            "independent_procurement": screen_firm_capacity(
                independent, demand, hours, offers, inputs["target_eens_mwh"]
            ),
        }

    def sensitivity(_):
        scaling = []
        for n in (2, 8, 12, 16):
            start = perf_counter()
            s = capacity_states((CapacityUnit(10, 0.1),) * n, 0.1)
            scaling.append(
                {
                    "units": n,
                    "states": len(s),
                    "seconds": perf_counter() - start,
                    "risk": window_risk(s, n * 8, hours=4),
                }
            )
        return {
            "common_probability": [
                {"q": v, **window_risk(capacity_states(units, v), demand, hours=hours)}
                for v in (0, 0.05, 0.1, 0.2)
            ],
            "demand": [
                {"demand_mw": v, **window_risk(states, v, hours=hours)} for v in (80, 100, 120)
            ],
            "scaling": scaling,
        }

    r = run_quantum_research_study(
        {
            "objective": "Screen firm capacity under explicit common-outage dependence",
            "classification": "mixed",
        },
        {
            "inspect_evidence": lambda _: evidence,
            "benchmark_methods": benchmark,
            "assess_sensitivity": sensitivity,
            "prepare_handoff": lambda c: {
                "method": "classical exact state enumeration and finite offer search",
                "quantum_used": False,
                "selected": c["reports"]["benchmark_methods"]["correlated_procurement"][
                    "selected"
                ],
                "next_action": "Calibrate joint outages, chronological weather/load, imports and storage energy; independent adequacy review",
                "limits": "Synthetic four-hour constant-demand window; not annual LOLE, a winter forecast, or realized savings",
            },
        },
    )
    if not r["success"]:
        raise RuntimeError(r["trace"])
    r["environment"] = environment()
    r["fixture_sha256"] = hashlib.sha256(raw).hexdigest()
    r["agent_install"] = json.loads(
        importlib.metadata.distribution("energy-agents").read_text("direct_url.json") or "{}"
    )
    return r


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/adequacy-engineer.json")
    args = parser.parse_args()
    r = run_adequacy_engineer()
    p = Path(args.output)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(r, indent=2, allow_nan=False) + "\n")
    print(json.dumps(r["reports"]["prepare_handoff"], indent=2))


if __name__ == "__main__":
    main()
