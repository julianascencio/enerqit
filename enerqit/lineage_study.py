"""Offline PV solver-adaptation evidence study, with no external control path."""

import argparse
import json
from dataclasses import asdict, replace
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import numpy as np

from enerqit.benchmarking import environment
from enerqit.datasets import coupled_inventory
from enerqit.lineage import (
    Authority,
    EffectWitness,
    ExecutionContext,
    LineageStore,
    Recommendation,
    assess_currentness,
    assess_effect,
    classify_outcome,
    fingerprint,
)
from enerqit.solvers import exact, simulated_annealing


def run_lineage_study() -> dict:
    """Compare explicit 1-read and 16-read classical SA configurations.

    This is a deliberately unequal-compute intervention demonstration, not an
    advantage benchmark or proof that historical evidence improves optimization.
    The evidence clock is synthetic; measured wall times use perf_counter.
    """
    problem, truth, a, y = coupled_inventory(seed=42)
    optimum = exact(problem)
    workload = fingerprint(
        {
            "matrix": problem.matrix.tolist(),
            "offset": float(problem.offset),
            "templates": a.tolist(),
            "observations": y.tolist(),
            "generator": "coupled_inventory(seed=42)",
        }
    )
    context = ExecutionContext(
        workload,
        "local-cpu",
        "enerqit-sa-v1",
        "synthetic-v1",
        "scripted-budget-policy-v1",
        "between-solver-runs",
    )
    proposal = Recommendation(
        "increase-reads",
        "1",
        "local-sa",
        (("reads", 16), ("sweeps", 80)),
        context,
        "baseline-observations",
        1000,
        1000,
        1100,
    )
    authority = Authority("offline-study-owner", "simulation-only-v1", proposal.digest, 1000, 1100)
    kwargs = {"now_s": 1001, "max_evidence_age_s": 30, "simulation": True}
    controls = {
        "current": assess_currentness(proposal, context, authority, **kwargs),
        "stale": assess_currentness(proposal, context, authority, **{**kwargs, "now_s": 1040}),
        "expired": assess_currentness(proposal, context, authority, **{**kwargs, "now_s": 1100}),
        "unknown_state": assess_currentness(proposal, None, authority, **kwargs),
        "changed_calibration": assess_currentness(
            proposal, replace(context, calibration_id="synthetic-v2"), authority, **kwargs
        ),
        "changed_workload": assess_currentness(
            proposal, replace(context, workload_id="another-input"), authority, **kwargs
        ),
        "revoked": assess_currentness(
            proposal, context, replace(authority, active=False), **kwargs
        ),
        "missing_authority": assess_currentness(proposal, context, None, **kwargs),
        "replayed": assess_currentness(
            proposal, context, authority, consumed_ids=frozenset({proposal.id}), **kwargs
        ),
        "incomplete": assess_currentness(
            proposal, context, authority, evidence_complete=False, **kwargs
        ),
        "contradictory": assess_currentness(
            proposal, context, authority, contradictory=True, **kwargs
        ),
        "clock_skew": assess_currentness(
            proposal, context, authority, clock_certain=False, **kwargs
        ),
        "changed_parameters": assess_currentness(
            replace(proposal, parameters=(("reads", 32), ("sweeps", 80))),
            context,
            authority,
            **kwargs,
        ),
    }
    records = []
    for seed in range(8):
        before = simulated_annealing(problem, seed=seed, reads=1, sweeps=80)
        observation = {
            "execution_id": f"baseline-{seed}",
            "sequence": 2 * seed,
            "timestamp_s": 1000,
            "clock": "synthetic-UTC-Unix-seconds",
            "result": before.to_dict(),
            "workload_id": workload,
            "signal_rmse": float(np.sqrt(np.mean((a @ before.x - y) ** 2))),
            "energy_gap": before.energy - optimum.energy,
        }
        rec = replace(proposal, id=f"increase-reads-{seed}", evidence_id=fingerprint(observation))
        auth = replace(authority, recommendation_digest=rec.digest)
        start = perf_counter()
        gate = assess_currentness(rec, context, auth, **kwargs)
        gate_s = perf_counter() - start
        if gate.status != "ELIGIBLE_FOR_SIMULATION":
            raise RuntimeError(gate.reasons)
        # No dispatcher or provider adapter: the experiment invokes a local
        # solver explicitly, using the exact configuration bound above.
        after = simulated_annealing(problem, seed=seed, **{k: int(v) for k, v in rec.parameters})
        request_id = f"local-request-{seed}"
        witness = EffectWitness(
            request_id,
            rec.digest,
            rec.target,
            acknowledged=True,
            readback=tuple((key, after.metadata[key]) for key, _ in rec.parameters),
            readback_source="applying-local-solver-metadata",
            observed_at_s=1002,
        )
        effect = assess_effect(rec, request_id, witness, request_at_s=1001)
        # Feasibility is checked independently of the objective; lower QUBO
        # energy on an infeasible candidate is not counted as a useful outcome.
        comparable = bool(problem.feasible(before.x) and problem.feasible(after.x))
        records.append(
            {
                "observation": observation,
                "interpretation": {
                    "method": "scripted-budget-policy-v1",
                    "claim": "More reads may reduce solution gap; unproven",
                },
                "recommendation": asdict(rec),
                "authority": asdict(auth),
                "gate": asdict(gate),
                "governance_path_s": gate_s,
                "effect_request_id": request_id,
                "witness": asdict(witness),
                "effect": effect,
                "post_effect": {
                    "execution_id": f"adapted-{seed}",
                    "sequence": 2 * seed + 1,
                    "timestamp_s": 1002,
                    "result": after.to_dict(),
                    "signal_rmse": float(np.sqrt(np.mean((a @ after.x - y) ** 2))),
                    "energy_gap": after.energy - optimum.energy,
                    "true_bits_recovered": bool(np.array_equal(after.x, truth)),
                },
                "outcome": classify_outcome(
                    before.energy,
                    after.energy,
                    materiality=1e-6,
                    comparable=comparable,
                    effect_confirmed=effect["confirmed"],
                ),
            }
        )
    ack = EffectWitness("ack-only", proposal.digest, proposal.target, acknowledged=True)
    acknowledgement_only = assess_effect(proposal, "ack-only", ack)
    output = {
        "schema_version": "1.0",
        "study": "genesis-inspired-adaptation-evidence",
        "source": {
            "author": "Genesis AiX, LLC",
            "title": "Hybrid Quantum-Classical Intelligence Architecture",
            "version": "0.3",
            "date": "2026-11",
            "provided_on": "2026-11-13",
            "status": "conceptual research proposal; not empirical validation",
            "sha256": "2f3b9a0f8fef410301cd3764ffa5ef45f534706c9d72a98ec031c05435e01c5a",
            "sections": ["3.5", "5", "6.2", "6.3", "6.4", "7.1", "9.3", "10.1"],
            "public_url": None,
            "pdf_redistributed": False,
        },
        "execution_kind": "classical",
        "data_kind": "synthetic",
        "quantum_hardware_used": False,
        "quantum_advantage_established": False,
        "environment": environment(),
        "workload_id": workload,
        "comparison_protocol": {
            "metric": "QUBO energy",
            "unit": "synthetic objective units",
            "materiality": 1e-6,
            "seeds": list(range(8)),
            "baseline_reads": 1,
            "adapted_reads": 16,
            "sweeps": 80,
            "equal_compute": False,
            "statistical_significance": "NOT_TESTED",
        },
        "exact_reference": optimum.to_dict(),
        "negative_controls": {key: asdict(value) for key, value in controls.items()},
        "acknowledgement_only": acknowledgement_only,
        "records": records,
        "limits": [
            "No hardware execution, AI model, quantum simulation or real-time QEC.",
            "W2 is local self-reported solver metadata, not independent telemetry.",
            "Atomic authorization-to-effect and timing isolation are NOT ESTABLISHED.",
            "More compute is not evidence of architecture value or quantum advantage.",
            "Same-seed pairs do not imply identical random trajectories at different reads.",
            "Single-instance descriptive differences do not establish causality or significance.",
        ],
    }
    output["serialized_bytes_without_size_field"] = len(
        json.dumps(output, allow_nan=False).encode()
    )
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/adaptation-evidence.json")
    parser.add_argument("--store", default="results/adaptation-evidence.sqlite")
    args = parser.parse_args()
    report = run_lineage_study()
    store = LineageStore(args.store)
    run_id = str(uuid4())
    store.append(run_id, {key: value for key, value in report.items() if key != "records"})
    for seed, record in enumerate(report["records"]):
        observation_id = f"{run_id}/observation/{seed}"
        store.append(observation_id, record["observation"], parent_id=run_id)
        store.append(f"{run_id}/adaptation/{seed}", record, parent_id=observation_id)
    report["lineage_run_id"] = run_id
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "outcomes": [r["outcome"]["status"] for r in report["records"]],
                "controls": {k: v["status"] for k, v in report["negative_controls"].items()},
                "output": str(path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
