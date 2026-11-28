"""Existing engineer tools for inter-window recharge economics."""

import hashlib
import importlib.metadata
import json
from importlib.resources import files
from pathlib import Path

from enerqit.benchmarking import environment
from enerqit.recharge import plan_recharge
from enerqit.storage_envelope import ActivationWindow, replay_activation


def run_recharge_study() -> dict:
    from energy_agents.quantum_ml import run_quantum_research_study

    raw = files("enerqit").joinpath("data/recharge_20261128.json").read_bytes()
    data = json.loads(raw)
    a = data["inputs"]

    def bench(_):
        p = tuple(a["discharge_mw"])
        window = ActivationWindow(p, p, tuple(a["hours"]), 2, 1, a["capacity_dc_mwh"], 0.9, 0.9)
        return dict(
            optimized=plan_recharge(**a),
            early_only=plan_recharge(**dict(a, charge_limit_mw=[0, 2, 0, 0])),
            no_recharge=plan_recharge(**dict(a, charge_limit_mw=[0] * 4)),
            no_recharge_replay=replay_activation(window, p, a["initial_dc_mwh"]),
        )

    def sensitivity(_):
        return dict(
            import_limit={
                str(c): plan_recharge(**dict(a, charge_limit_mw=[0, c, c, 0])) for c in (0.5, 1, 2)
            },
            terminal={str(e): plan_recharge(**dict(a, terminal_dc_mwh=e)) for e in (0, 0.5, 1)},
            scaling={
                str(n): {
                    k: v
                    for k, v in plan_recharge(
                        **dict(
                            a,
                            discharge_mw=[1, 0, 0, 1] * (n // 4),
                            charge_limit_mw=[0, 2, 2, 0] * (n // 4),
                            hours=[1] * n,
                            price_eur_mwh=[50, 100, 20, 50] * (n // 4),
                            capacity_dc_mwh=4,
                        )
                    ).items()
                    if k in ("status", "runtime_s", "variables", "cost_eur")
                }
                for n in (4, 24, 168, 8760)
            },
        )

    r = run_quantum_research_study(
        {
            "objective": "Minimum purchase cost to restore battery energy between mandatory services",
            "classification": "synthetic",
        },
        {
            "inspect_evidence": lambda _: data,
            "benchmark_methods": bench,
            "assess_sensitivity": sensitivity,
            "prepare_handoff": lambda _: dict(
                quantum_used=False,
                limits="Known future services, nonnegative prices, explicit import permission, no degradation or network model",
                next_action="Validate service obligations and recharge connection permission before field trial",
            ),
        },
    )
    if not r["success"]:
        raise RuntimeError(r["trace"])
    r.update(
        fixture_sha256=hashlib.sha256(raw).hexdigest(),
        environment=environment(),
        test_seeds=list(range(6)),
        agent_install=json.loads(
            importlib.metadata.distribution("energy-agents").read_text("direct_url.json") or "{}"
        ),
    )
    return r


if __name__ == "__main__":
    p = Path("results/recharge.json")
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(run_recharge_study(), indent=2, allow_nan=False) + "\n")
    print(p)
