"""Registered engineer study of energy-limited reserve."""

import hashlib
import importlib.metadata
import json
from dataclasses import replace
from importlib.resources import files
from pathlib import Path
from time import perf_counter

from enerqit.benchmarking import environment
from enerqit.reserve_replay import replay_reserve, screen_reserve_offers
from enerqit.storage import BatteryOffer


def run_reserve_study() -> dict:
    from energy_agents.quantum_ml import run_quantum_research_study

    raw = files("enerqit").joinpath("data/reserve_20261116.json").read_bytes()
    data = json.loads(raw)
    offers = [BatteryOffer(**o) for o in data["offers"]]

    def benchmark(_):
        return screen_reserve_offers(
            offers, data["deficits_mw"], data["probabilities"], data["hours"], 20
        )

    def sensitivity(_):
        rows = []
        for n in (4, 24, 168, 8760):
            start = perf_counter()
            r = replay_reserve(offers[0], [50] * n, [1] * n)
            rows.append(
                {
                    "intervals": n,
                    "runtime_s": perf_counter() - start,
                    "unserved_mwh": r["unserved_mwh"],
                }
            )
        return {
            "scaling": rows,
            "start_soc": [
                {
                    "start_soc": s,
                    **screen_reserve_offers(
                        [replace(o, start_soc=s) for o in offers],
                        data["deficits_mw"],
                        data["probabilities"],
                        data["hours"],
                        20,
                    ),
                }
                for s in (0.5, 0.75, 1)
            ],
        }

    r = run_quantum_research_study(
        {
            "objective": "Select deliverable battery reserve under prolonged deficits",
            "classification": "mixed",
        },
        {
            "inspect_evidence": lambda _: data,
            "benchmark_methods": benchmark,
            "assess_sensitivity": sensitivity,
            "prepare_handoff": lambda _: {
                "quantum_used": False,
                "next_action": "Obtain licensed chronological outage and initial SOC observations; independently review reserve contracts",
                "limits": "Synthetic no-recharge single-battery trajectories; no annual or regional risk claim",
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
    p = Path("results/reserve-study.json")
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(run_reserve_study(), indent=2, allow_nan=False) + "\n")
    print(p)
