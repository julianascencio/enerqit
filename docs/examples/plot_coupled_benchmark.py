"""
Classical versus quantum-inspired coupled inference
===================================================

Multiple template groups share an inventory constraint. Both unconstrained
QUBO enumeration and native constrained enumeration are used as references.
The chart includes construction-independent solver wall time and original
signal error. A few small instances do not demonstrate a quantum advantage.
"""

import matplotlib.pyplot as plt
import pandas as pd

from enerqit.benchmarking import run_benchmark

records = pd.DataFrame(run_benchmark(seeds=(0, 1, 2), instance_seeds=(42, 43, 44)))
summary = records.groupby("method").agg(
    median_seconds=("elapsed_s", "median"),
    feasible_rate=("feasible", "mean"),
    optimum_hit_rate=("optimum_hit", "mean"),
    mean_signal_rmse=("signal_rmse", "mean"),
)
print(summary.to_string())
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
summary.median_seconds.plot.barh(ax=axes[0], logx=True, color="#357E9B")
summary.mean_signal_rmse.plot.barh(ax=axes[1], color="#C47D32")
axes[0].set(xlabel="Median solver seconds (log scale)", ylabel="")
axes[1].set(xlabel="Mean original signal RMSE", ylabel="")
fig.suptitle("Synthetic microbenchmark: fixed budgets, no speedup claim")
fig.tight_layout()
