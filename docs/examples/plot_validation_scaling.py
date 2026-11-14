"""
Matched budgets and boundary-aware decomposition
================================================

Compare 12, 24 and 48-bit synthetic configuration problems under the same search
wall allowance. Each method receives the same constraint-only feasible start.
Late batches are discarded and recorded; native solver time limits are not hard
OS preemption. Targets exist only when a separate MILP reference proves its
optimum. A missing target is not a zero optimality gap.

The block method preserves outside couplings and constraints, solves small exact
subproblems and audits the reconstructed full candidate. It is a local heuristic.
This small single-seed example illustrates the protocol, not solver superiority.
"""

import matplotlib.pyplot as plt
import numpy as np

from enerqit.scaling import run_scaling_benchmark

records = run_scaling_benchmark(
    groups=(4, 8, 16), seeds=(0,), instance_seeds=(42,), seconds=0.05, reference_seconds=0.5
)
methods = sorted({r["method"] for r in records})
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for method in methods:
    subset = [r for r in records if r["method"] == method]
    bits = [r["metrics"]["variables"] for r in subset]
    axes[0].plot(bits, [r["metrics"]["signal_rmse"] for r in subset], "o-", label=method)
    axes[1].plot(bits, [r["timings_s"]["search"] for r in subset], "o-", label=method)
axes[0].set(
    xlabel="Binary variables", ylabel="Original signal RMSE", title="Audited feasible candidates"
)
axes[1].axhline(0.05, color="black", linestyle="--", label="Candidate admission deadline")
axes[1].set(
    xlabel="Binary variables", ylabel="Measured search seconds", title="Overruns remain visible"
)
axes[0].legend(fontsize=7)
axes[1].legend(fontsize=7)
fig.tight_layout()
assert all(r["feasible"] and np.isfinite(r["objective"]) for r in records)
print(
    {
        "runs": len(records),
        "certified_reference_runs": sum(r["metrics"]["certified_reference"] for r in records),
        "failed_runs": sum(r["status"] == "failed" for r in records),
    }
)

plt.show()
