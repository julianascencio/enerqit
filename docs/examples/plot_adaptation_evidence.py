"""
Did a solver adjustment actually help?
=======================================

The Genesis AiX v0.3 research proposal motivates separating observations,
recommendations, declared authority, effect evidence and measured outcomes.
This example applies that distinction to EnerQit's synthetic PV inventory
problem. It is entirely classical and runs offline.

A scripted policy increases simulated-annealing reads from 1 to 16. Both
configurations use 80 sweeps and the same listed seeds. This **increases compute**;
it is not a matched-budget benchmark or proof of historical-learning value.
The exact small-instance reference remains available as a strong baseline.

Run and persist the full evidence chain::

    python -m enerqit.lineage_study --output results/adaptation-evidence.json
    python docs/examples/plot_adaptation_evidence.py

See :doc:`the study protocol </adaptation_evidence>` for source attribution,
negative controls, witness semantics, and deliberately unimplemented claims.
"""

# %%
# Run eight fixed-seed pairs. The experiment always records every outcome,
# including regressions, no material change and inconclusive comparisons.
import matplotlib.pyplot as plt
import numpy as np

from enerqit.lineage_study import run_lineage_study

report = run_lineage_study()
records = report["records"]
print("Execution:", report["execution_kind"], "Data:", report["data_kind"])
print("Workload:", report["workload_id"])
print("Protocol:", report["comparison_protocol"])
print("Exact baseline seconds:", report["exact_reference"]["elapsed_s"])

# %%
# Plot measured optimization gap separately from measured computational cost.
# A negative cost gap from an infeasible candidate cannot count as improvement;
# the outcome evaluator explicitly checks comparability/feasibility.
fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
x = np.arange(len(records))
for offset, label, stage, color in (
    (-0.18, "Baseline: 1 read", "observation", "#6d8193"),
    (0.18, "Adapted: 16 reads", "post_effect", "#087f8c"),
):
    axes[0].bar(
        x + offset,
        [max(0, r[stage]["energy_gap"]) for r in records],
        width=0.36,
        label=label,
        color=color,
    )
    axes[1].bar(
        x + offset,
        [1000 * r[stage]["result"]["elapsed_s"] for r in records],
        width=0.36,
        label=label,
        color=color,
    )
axes[0].set(
    ylabel="QUBO objective gap", title="Synthetic PV inventory: extra reads, explicit evidence"
)
axes[0].set_yscale("symlog", linthresh=1e-6)
axes[0].axhline(1e-6, color="black", linestyle=":", linewidth=0.8, label="Materiality threshold")
axes[0].legend()
axes[1].set(xlabel="Solver seed", ylabel="Solver wall time (ms)", xticks=x)
fig.tight_layout()

# %%
# Negative controls are evaluated before any local adaptation is eligible. The
# gate is advisory by default and implements no physical dispatch interface.
for name, decision in report["negative_controls"].items():
    print(name, decision["status"], decision["reasons"])
print("Command acceptance alone:", report["acknowledgement_only"])

# %%
# Local metadata provides only a declared W2 readback, never an independent W3
# witness. All differences remain descriptive rather than causal/statistical.
for seed, record in enumerate(records):
    print(
        seed,
        "effect:",
        record["effect"],
        "outcome:",
        record["outcome"],
        "governance ms:",
        1000 * record["governance_path_s"],
    )
print("Serialized evidence bytes:", report["serialized_bytes_without_size_field"])
for limitation in report["limits"]:
    print(limitation)
plt.show()
