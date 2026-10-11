"""Interchangeable solvers; each returns a :class:`~enerqit.SolverResult`."""

from enerqit.solvers.bifurcation import simulated_bifurcation
from enerqit.solvers.classical import exact, group_exact, simulated_annealing

__all__ = ["exact", "group_exact", "simulated_annealing", "simulated_bifurcation"]
