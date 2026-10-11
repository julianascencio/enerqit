"""Quantum-ready exports. These functions never submit a remote computation."""

import numpy as np


def ising_payload(problem):
    """Return serializable pair coefficients using x=(s+1)/2.

    An annealer using classical spins may use this convention directly. Qiskit
    computational bits use Z=1-2*x, so ``to_qiskit`` reverses linear signs.
    """
    h, j, offset = problem.to_ising()
    return {
        "linear": h.tolist(),
        "quadratic": [
            [i, k, float(j[i, k])]
            for i in range(len(h))
            for k in range(i + 1, len(h))
            if j[i, k] != 0
        ],
        "offset": offset,
        "binary_mapping": "x=(s+1)/2",
    }


def to_dimod(problem):
    """Create a local dimod BQM. Install the optional ``quantum`` extra."""
    try:
        import dimod
    except ImportError as exc:
        raise ImportError("Install enerqit[quantum] for dimod export") from exc
    model = dimod.BinaryQuadraticModel.from_qubo(problem.to_upper(), offset=problem.offset)
    for i in range(problem.size):
        model.add_variable(i, 0)
    return model


def to_qiskit(problem):
    """Return SparsePauliOp with <bitstring|H|bitstring> equal to QUBO energy.

    Logical variable i maps to qubit i (rightmost label character is qubit 0).
    Ancillas, hardware routing and QAOA execution are outside this exporter.
    """
    try:
        from qiskit.quantum_info import SparsePauliOp
    except ImportError as exc:
        raise ImportError("Install enerqit[quantum] for Qiskit export") from exc
    h, j, offset = problem.to_ising()
    n = problem.size
    terms = [("I" * n, complex(offset))]
    for i in range(n):
        label = ["I"] * n
        label[n - 1 - i] = "Z"
        if h[i]:
            terms.append(("".join(label), complex(-h[i])))
        for k in range(i + 1, n):
            if j[i, k]:
                pair = label.copy()
                pair[n - 1 - k] = "Z"
                terms.append(("".join(pair), complex(j[i, k])))
    return SparsePauliOp.from_list(terms).simplify()


def qaoa_probabilities(problem, gammas, betas):
    """Small exact-statevector QAOA demonstrator, limited to 16 logical bits.

    This is a classical simulator with exponential memory, not a scalable solver
    or evidence of quantum advantage. Energies are scaled by max absolute matrix
    coefficient. Angles are caller-supplied; no silent optimizer or QPU call.
    """
    if problem.size > 16:
        raise ValueError("statevector demonstrator limited to 16 variables")
    gammas, betas = np.asarray(gammas, float), np.asarray(betas, float)
    if gammas.ndim != 1 or gammas.shape != betas.shape or not len(gammas):
        raise ValueError("matching nonempty angle vectors required")
    if not np.isfinite(gammas).all() or not np.isfinite(betas).all():
        raise ValueError("angles must be finite")
    codes = np.arange(2**problem.size)
    bits = ((codes[:, None] >> np.arange(problem.size)) & 1).astype(np.int8)
    energies = problem.energy(bits)
    scaled = (energies - problem.offset) / max(np.max(np.abs(problem.matrix)), 1e-12)
    state = np.ones(len(codes), complex) / np.sqrt(len(codes))
    for gamma, beta in zip(gammas, betas, strict=True):
        state *= np.exp(-1j * gamma * scaled)
        for i in range(problem.size):
            a = codes[(codes & (1 << i)) == 0]
            b = a | (1 << i)
            old_a, old_b = state[a].copy(), state[b].copy()
            state[a] = np.cos(beta) * old_a - 1j * np.sin(beta) * old_b
            state[b] = np.cos(beta) * old_b - 1j * np.sin(beta) * old_a
    return bits, np.abs(state) ** 2, energies
