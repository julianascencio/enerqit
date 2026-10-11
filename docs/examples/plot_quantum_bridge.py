"""
Move the same QUBO toward quantum backends
==========================================

An educational p=1 QAOA statevector calculation uses classical simulation.
Export adapters also support dimod and Qiskit when their optional extra is
installed. Hardware access, embedding, transpilation, shot cost and mitigation
are intentionally not hidden behind this simulation.
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import differential_evolution

from enerqit.qubo import QUBO
from enerqit.solvers import exact
from enerqit.solvers.quantum import ising_payload, qaoa_probabilities

problem = QUBO(np.array([[-1.0, 0.4, 0.2], [0.4, -0.7, -0.3], [0.2, -0.3, 0.5]]))


def objective(angles):
    _, probability, energies = qaoa_probabilities(problem, [angles[0]], [angles[1]])
    return float(probability @ energies)


opt = differential_evolution(objective, [(0, 2 * np.pi), (0, np.pi)], seed=4, maxiter=20)
bits, probability, energies = qaoa_probabilities(problem, [opt.x[0]], [opt.x[1]])
reference = exact(problem)
print("Expected energy:", opt.fun, "Exact minimum:", reference.energy)
print("Ground-state probability:", probability[np.isclose(energies, reference.energy)].sum())
print("Ising export:", ising_payload(problem))
fig, ax = plt.subplots(figsize=(7, 3.5))
ax.bar(["".join(map(str, x)) for x in bits], probability)
ax.set(
    xlabel="Bits in x0,x1,x2 order", ylabel="Probability", title="QAOA p=1, classical simulation"
)
fig.tight_layout()
