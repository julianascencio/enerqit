"""Boundary-aware block-coordinate QUBO experiments on classical hardware."""

from time import perf_counter

import numpy as np

from enerqit.qubo import QUBO
from enerqit.results import SolverResult


def conditioned_block(problem, x, indices) -> QUBO:
    """Condition on all outside bits, retaining cross-block couplings and RHS.

    The reduced objective includes the outside constant, so it equals the full
    objective for every reconstructed assignment. This is not independent block
    solving: ignoring boundary terms changes the original problem.
    """
    x = np.asarray(x)
    problem.energy(x)
    ids = np.asarray(indices, dtype=int)
    if x.ndim != 1 or ids.ndim != 1 or len(ids) == 0 or len(set(ids)) != len(ids):
        raise ValueError("Expected one binary vector and distinct block indices")
    if ids.min() < 0 or ids.max() >= problem.size:
        raise ValueError("Block index out of range")
    outside = np.setdiff1d(np.arange(problem.size), ids)
    q = problem.matrix[np.ix_(ids, ids)].copy()
    q += np.diag(2 * problem.matrix[np.ix_(ids, outside)] @ x[outside])
    offset = float(x[outside] @ problem.matrix[np.ix_(outside, outside)] @ x[outside])
    constraints = tuple(
        (c[:, ids], h - c[:, outside] @ x[outside]) for c, h in problem.constraints
    )
    return QUBO(q, problem.offset + offset, constraints)


def block_coordinate(problem, initial, *, block_size=12, passes=4, time_limit_s=1.0, seed=0):
    """Exact small blocks, accepting only feasible non-worsening full candidates.

    Random block order can move coupled decisions between passes. A feasible
    initial point is required. Global constraints may freeze small blocks; this
    is a local heuristic, never a global optimality certificate. A block that
    completes after the deadline is discarded, and the overrun is recorded.
    """
    start = perf_counter()
    if not isinstance(block_size, int) or not 1 <= block_size <= 16:
        raise ValueError("block_size must be in 1..16")
    if not isinstance(passes, int) or passes < 1:
        raise ValueError("passes must be positive")
    if not np.isfinite(time_limit_s) or time_limit_s <= 0:
        raise ValueError("time_limit_s must be finite and positive")
    if not problem.feasible(initial):
        raise ValueError("A feasible initial point is required")
    best = np.asarray(initial, dtype=np.int8).copy()
    rng = np.random.default_rng(seed)
    best_energy = float(problem.energy(best))
    trace = []
    for sweep in range(passes):
        order = rng.permutation(problem.size)
        for first in range(0, problem.size, block_size):
            if perf_counter() - start >= time_limit_s:
                break
            ids = order[first : first + block_size]
            sub = conditioned_block(problem, best, ids)
            codes = np.arange(2 ** len(ids), dtype=np.uint64)
            candidates = ((codes[:, None] >> np.arange(len(ids), dtype=np.uint64)) & 1).astype(
                np.int8
            )
            feasible = np.ones(len(candidates), dtype=bool)
            for c, h in sub.constraints:
                feasible &= np.all(np.isclose(candidates @ c.T, h, atol=1e-7, rtol=0), axis=1)
            candidates = candidates[feasible]
            if len(candidates) == 0:
                continue
            energies = sub.energy(candidates)
            candidate = best.copy()
            candidate[ids] = candidates[np.argmin(energies)]
            value = float(problem.energy(candidate))
            valid = problem.feasible(candidate)
            elapsed = perf_counter() - start
            accepted = elapsed <= time_limit_s and valid and value < best_energy - 1e-10
            if accepted:
                best, best_energy = candidate, value
            trace.append(
                {
                    "pass": sweep,
                    "size": len(ids),
                    "elapsed_s": elapsed,
                    "accepted": bool(accepted),
                    "objective": best_energy,
                }
            )
    return SolverResult(
        best,
        best_energy,
        "block_coordinate",
        seed,
        perf_counter() - start,
        problem.feasible(best),
        {
            "certified": False,
            "trace": trace,
            "block_size": block_size,
            "initial_energy": float(problem.energy(initial)),
            "time_limit_s": time_limit_s,
        },
    )
