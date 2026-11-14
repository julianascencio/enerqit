"""Sparse exact binary-product linearization through classical HiGHS MILP."""

from time import perf_counter

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix


def native_milp(problem, *, time_limit_s=30.0) -> dict:
    """Minimize the QUBO on its declared feasible domain with native equalities.

    For every nonzero pair introduce y=x_i*x_j, with the three McCormick
    inequalities and 0<=y<=1. Binary x makes this linearization exact. The
    certificate concerns the constrained native domain, not infeasible penalized
    minima. The deadline includes construction; solver overruns are reported.
    """
    if not np.isfinite(time_limit_s) or time_limit_s <= 0:
        raise ValueError("time_limit_s must be finite and positive")
    start = perf_counter()
    n = problem.size
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n) if problem.matrix[i, j] != 0]
    size = n + len(pairs)
    objective = np.r_[np.diag(problem.matrix), [2 * problem.matrix[i, j] for i, j in pairs]]
    row, col, values, lo, hi = [], [], [], [], []

    def add(entries, lower, upper):
        for j, v in entries.items():
            row.append(len(lo))
            col.append(j)
            values.append(v)
        lo.append(lower)
        hi.append(upper)

    for k, (i, j) in enumerate(pairs, n):
        add({k: 1, i: -1}, -np.inf, 0)
        add({k: 1, j: -1}, -np.inf, 0)
        add({k: -1, i: 1, j: 1}, -np.inf, 1)
    for matrix, target in problem.constraints:
        for coefficients, rhs in zip(matrix, target):
            add({j: v for j, v in enumerate(coefficients) if v}, rhs, rhs)
    matrix = coo_matrix((values, (row, col)), shape=(len(lo), size)).tocsc()
    construction_s = perf_counter() - start
    info = {
        "construction_s": construction_s,
        "variables": size,
        "matrix_bytes": matrix.data.nbytes + matrix.indices.nbytes + matrix.indptr.nbytes,
        "matrix_nnz": matrix.nnz,
    }
    remaining = time_limit_s - construction_s
    if remaining <= 0:
        return {"status": "timeout", "x": None, "solver_s": 0.0, **info}
    solve_start = perf_counter()
    result = milp(
        objective,
        integrality=np.r_[np.ones(n), np.zeros(len(pairs))],
        bounds=Bounds(np.zeros(size), np.ones(size)),
        constraints=LinearConstraint(matrix, lo, hi),
        options={"time_limit": remaining, "mip_rel_gap": 1e-9},
    )
    info["solver_s"] = perf_counter() - solve_start
    info["elapsed_s"] = perf_counter() - start
    info["message"] = result.message
    gap = getattr(result, "mip_gap", None)
    info["mip_relative_gap"] = float(gap) if gap is not None and np.isfinite(gap) else None
    bound = getattr(result, "mip_dual_bound", None)
    info["lower_bound"] = (
        float(bound + problem.offset) if bound is not None and np.isfinite(bound) else None
    )
    x = None if result.x is None else np.rint(result.x[:n]).astype(np.int8)
    feasible = x is not None and problem.feasible(x)
    return {
        "status": {0: "optimal", 1: "timeout", 2: "infeasible"}.get(result.status, "failed"),
        "x": x if feasible else None,
        "energy": float(problem.energy(x)) if feasible else None,
        "feasible": bool(feasible),
        **info,
    }
