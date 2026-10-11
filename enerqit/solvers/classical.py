"""Exhaustive, structure-aware, and stochastic classical baselines."""

from itertools import product
from math import prod
from time import perf_counter

import numpy as np

from enerqit.results import SolverResult


def exact(problem, *, max_variables=22, batch_size=4096):
    """Certify the unconstrained QUBO optimum by exhaustive enumeration.

    If penalties are too weak, the unconstrained optimum can be infeasible.
    Feasibility is reported independently and is never repaired silently.
    """
    if problem.size > max_variables:
        raise ValueError("exact enumeration exceeds max_variables")
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    start = perf_counter()
    best, energy = None, np.inf
    for first in range(0, 2**problem.size, batch_size):
        codes = np.arange(first, min(first + batch_size, 2**problem.size), dtype=np.uint64)
        x = ((codes[:, None] >> np.arange(problem.size, dtype=np.uint64)) & 1).astype(np.int8)
        es = problem.energy(x)
        idx = np.argmin(es)
        if es[idx] < energy:
            best, energy = x[idx].copy(), float(es[idx])
    return SolverResult(
        best,
        energy,
        "exact",
        None,
        perf_counter() - start,
        problem.feasible(best),
        {"certified": True, "evaluations": 2**problem.size},
    )


def group_exact(problem, *, max_combinations=1_000_000):
    """Enumerate one-hot groups and honor all additional equalities exactly.

    This is a native-task classical baseline, not a same-QUBO unconstrained
    solver. The certificate is restricted to the declared feasible domain.
    """
    if sorted(i for g in problem.groups for i in g) != list(range(problem.size)):
        raise ValueError("groups must partition all variables")
    count = prod(len(g) for g in problem.groups)
    if count > max_combinations:
        raise ValueError("too many group combinations")
    start = perf_counter()
    best, energy = None, np.inf
    for selected in product(*problem.groups):
        x = np.zeros(problem.size, dtype=np.int8)
        x[list(selected)] = 1
        if problem.feasible(x):
            e = float(problem.energy(x))
            if e < energy:
                best, energy = x, e
    if best is None:
        raise ValueError("no feasible group configuration")
    return SolverResult(
        best,
        energy,
        "group_exact",
        None,
        perf_counter() - start,
        True,
        {"certified": True, "domain": "declared constraints", "evaluations": count},
    )


def polish(problem, x, *, max_passes=100):
    """Deterministic one-bit descent, shared by all heuristic backends."""
    x = np.asarray(x, dtype=np.int8).copy()
    q = problem.matrix
    for _ in range(max_passes):
        delta = (1 - 2 * x) * (2 * q @ x) + np.diag(q)
        i = int(np.argmin(delta))
        if delta[i] >= -1e-12:
            break
        x[i] = 1 - x[i]
    return x


def simulated_annealing(
    problem,
    *,
    seed=0,
    reads=32,
    sweeps=200,
    temperature=(2.0, 0.01),
    local_polish=True,
    initial=None,
):
    """Metropolis simulated annealing with coefficients scaled consistently.

    ``sweeps`` visits every bit once in random order for every independent read.
    ``temperature`` applies after division by the largest absolute coefficient.
    """
    if reads < 1 or sweeps < 1 or min(temperature) <= 0:
        raise ValueError("reads, sweeps and temperatures must be positive")
    start = perf_counter()
    rng = np.random.default_rng(seed)
    q = problem.matrix / max(np.max(np.abs(problem.matrix)), 1e-12)
    xs = rng.integers(0, 2, (reads, problem.size), dtype=np.int8)
    if initial is not None:
        problem.energy(initial)
        xs[0] = initial
    for temp in np.geomspace(temperature[0], temperature[1], sweeps):
        for i in rng.permutation(problem.size):
            delta = (1 - 2 * xs[:, i]) * (2 * (xs @ q[:, i])) + q[i, i]
            accept = (delta <= 0) | (np.log(rng.random(reads)) < -delta / temp)
            xs[accept, i] = 1 - xs[accept, i]
    raw_min = float(np.min(problem.energy(xs)))
    if local_polish:
        xs = np.array([polish(problem, x) for x in xs])
    energies = problem.energy(xs)
    idx = int(np.argmin(energies))
    x = xs[idx]
    return SolverResult(
        x,
        float(energies[idx]),
        "simulated_annealing",
        seed,
        perf_counter() - start,
        problem.feasible(x),
        {
            "reads": reads,
            "sweeps": sweeps,
            "local_polish": local_polish,
            "raw_best_energy": raw_min,
            "certified": False,
        },
    )
