"""A transparent NumPy ballistic simulated-bifurcation reference implementation.

Uses classical oscillator dynamics with inelastic walls. This is a research
reference, not Toshiba's implementation and not a quantum hardware simulation.
See Goto et al. (2021), https://doi.org/10.1126/sciadv.abe7953.
"""

from time import perf_counter

import numpy as np

from enerqit.results import SolverResult
from enerqit.solvers.classical import polish


def simulated_bifurcation(
    problem, *, seed=0, agents=64, steps=1000, dt=0.1, coupling=0.5, local_polish=True
):
    """Minimize a QUBO with ballistic oscillator dynamics and an auxiliary spin.

    The Ising convention is ``E=.5*s.T@J@s + h@s``. A free reference spin
    converts linear fields to pair interactions. Dynamics are
    ``dy/dt=-(1-pump)*x-coupling*J_scaled@x`` and ``dx/dt=y``.
    Pump increases from zero to one. At ``abs(x)>1``, x is clipped and momentum zeroed.
    Both oscillators and momenta are entirely classical floating-point arrays.

    Parameters
    ----------
    problem : enerqit.qubo.QUBO
        Full symmetric QUBO and independent feasibility constraints.
    seed : int
        Deterministic initialization seed.
    agents, steps : int
        Number of independent oscillator trajectories and integration steps.
    dt, coupling : float
        Integrator step and coupling strength; sensitivity must be benchmarked.
    local_polish : bool
        Apply the same one-bit descent available to simulated annealing.

    Returns
    -------
    SolverResult
        Best observed candidate, including before-polish objective and feasibility.
    """
    if agents < 1 or steps < 1 or not 0 < dt <= 1 or coupling <= 0:
        raise ValueError("invalid agents, steps, dt or coupling")
    start = perf_counter()
    rng = np.random.default_rng(seed)
    h, j, _ = problem.to_ising()
    augmented = np.zeros((problem.size + 1, problem.size + 1))
    augmented[:-1, :-1] = j
    augmented[:-1, -1] = augmented[-1, :-1] = h
    scale = max(np.max(np.sum(np.abs(augmented), axis=1)), 1e-12)
    augmented /= scale
    positions = rng.normal(0, 0.1, (agents, problem.size + 1))
    momenta = rng.normal(0, 0.1, positions.shape)
    candidates = []
    for step in range(steps):
        pump = (step + 1) / steps
        momenta += dt * (-(1 - pump) * positions - coupling * (positions @ augmented))
        positions += dt * momenta
        wall = np.abs(positions) > 1
        positions = np.clip(positions, -1, 1)
        momenta[wall] = 0
        if step == steps - 1 or (step + 1) % max(1, steps // 5) == 0:
            signs = np.where(positions >= 0, 1, -1)
            spins = signs[:, :-1] * signs[:, -1, None]
            candidates.append(((spins + 1) // 2).astype(np.int8))
    xs = np.concatenate(candidates)
    raw_min = float(np.min(problem.energy(xs)))
    if local_polish:
        xs = np.array([polish(problem, x) for x in xs])
    energies = problem.energy(xs)
    idx = int(np.argmin(energies))
    x = xs[idx]
    return SolverResult(
        x,
        float(energies[idx]),
        "ballistic_simulated_bifurcation",
        seed,
        perf_counter() - start,
        problem.feasible(x),
        {
            "agents": agents,
            "steps": steps,
            "dt": dt,
            "coupling": coupling,
            "local_polish": local_polish,
            "raw_best_energy": raw_min,
            "coefficient_scale": scale,
            "certified": False,
            "implementation": "NumPy reference; classical hardware",
        },
    )
