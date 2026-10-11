"""Reproducible small-instance benchmark; no speedup or hardware-advantage claim."""

import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
from time import perf_counter

import numpy as np

from enerqit.datasets import coupled_inventory
from enerqit.solvers import exact, group_exact, simulated_annealing, simulated_bifurcation


def environment():
    """Capture versions and platform without hostnames or credentials."""
    versions = {}
    for name in ("numpy", "scipy", "pandas", "pvlib", "enerqit"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "source-tree"
    return {
        "python": platform.python_version(),
        "platform": platform.system(),
        "machine": platform.machine(),
        "versions": versions,
    }


def run_benchmark(output=None, *, seeds=(0, 1, 2), instance_seeds=(42, 43, 44)):
    """Compare two exact baselines and SA/bSB on three small synthetic instances.

    Fixed heuristic budgets are explicit, not equal-runtime budgets. Same-QUBO
    gap and original signal fit/feasibility are both reported. Results cannot
    establish production benefit, scaling advantage, or statistical superiority.
    """
    records = []
    env = environment()
    for instance_seed in instance_seeds:
        start = perf_counter()
        problem, truth, a, y = coupled_inventory(seed=instance_seed)
        build_s = perf_counter() - start
        digest = hashlib.sha256(
            problem.matrix.tobytes() + np.array(problem.offset).tobytes()
        ).hexdigest()
        optimum = exact(problem)
        native = group_exact(problem)
        runs = [optimum, native]
        for seed in seeds:
            runs.extend(
                [
                    simulated_annealing(problem, seed=seed, reads=32, sweeps=120),
                    simulated_bifurcation(problem, seed=seed, agents=64, steps=800),
                ]
            )
        for result in runs:
            row = result.to_dict()
            row.update(
                {
                    "instance_seed": instance_seed,
                    "n_variables": problem.size,
                    "qubo_sha256": digest,
                    "construction_s": build_s,
                    "absolute_energy_gap": max(0.0, result.energy - optimum.energy),
                    "signal_rmse": float(np.sqrt(np.mean((a @ result.x - y) ** 2))),
                    "true_bits_recovered": bool(np.array_equal(result.x, truth)),
                    "optimum_hit": bool(abs(result.energy - optimum.energy) < 1e-8),
                    "environment": env,
                }
            )
            records.append(row)
    if output is not None:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(r, allow_nan=False) + "\n" for r in records), encoding="utf-8"
        )
    return records
