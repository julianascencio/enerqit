from itertools import product

import numpy as np
import pytest

from enerqit.qubo import QUBO, least_squares_qubo
from enerqit.solvers import exact, group_exact, simulated_annealing, simulated_bifurcation
from enerqit.solvers.quantum import qaoa_probabilities, to_dimod, to_qiskit


def test_all_energy_conventions():
    rng = np.random.default_rng(1)
    a, y = rng.normal(size=(8, 4)), rng.normal(size=8)
    weights = rng.uniform(size=8)
    q = least_squares_qubo(a, y, weights=weights, groups=((0, 1), (2, 3)), penalty=3)
    h, j, offset = q.to_ising()
    for values in product((0, 1), repeat=4):
        x = np.array(values)
        s = 2 * x - 1
        expected = np.sum(weights * (a @ x - y) ** 2) + 3 * (
            (x[:2].sum() - 1) ** 2 + (x[2:].sum() - 1) ** 2
        )
        upper = sum(v * x[i] * x[k] for (i, k), v in q.to_upper().items()) + q.offset
        assert q.energy(x) == pytest.approx(expected)
        assert upper == pytest.approx(expected)
        assert 0.5 * s @ j @ s + h @ s + offset == pytest.approx(expected)


@pytest.mark.parametrize("solver", [simulated_annealing, simulated_bifurcation])
def test_seeded_solvers_recover_easy_ground_state(solver):
    q = QUBO(np.diag([-1.0, 2.0, -3.0, 4.0]))
    a, b = solver(q, seed=16), solver(q, seed=16)
    np.testing.assert_array_equal(a.x, [1, 0, 1, 0])
    np.testing.assert_array_equal(a.x, b.x)
    assert a.energy == pytest.approx(exact(q).energy)
    assert a.energy == pytest.approx(q.energy(a.x))


def test_native_constraints_and_weak_penalties():
    q = least_squares_qubo([[1, 1]], [2], groups=((0, 1),), penalty=0.01)
    assert not exact(q).feasible
    assert group_exact(q).feasible
    assert group_exact(q).energy > exact(q).energy


def test_invalid_qubo_and_limits():
    with pytest.raises(ValueError):
        QUBO(np.zeros((2, 3)))
    with pytest.raises(ValueError):
        exact(QUBO(np.eye(23)))
    with pytest.raises(ValueError):
        least_squares_qubo([[1, 2]], [1], weights=[-1])
    with pytest.raises(ValueError):
        QUBO(np.eye(2)).energy([0, 0.4])


def test_qaoa_unitary_and_zero_angles():
    q = QUBO(np.array([[-1, 0.3], [0.3, 0.5]]), 3.2)
    bits, p, energies = qaoa_probabilities(q, [0], [0])
    np.testing.assert_allclose(p, 0.25)
    np.testing.assert_allclose(q.energy(bits), energies)
    _, p, _ = qaoa_probabilities(q, [0.9, 0.3], [0.2, 0.7])
    assert p.sum() == pytest.approx(1)
    assert (p >= 0).all()


def test_dimod_export():
    pytest.importorskip("dimod")
    q = QUBO(np.array([[-1, 0.3], [0.3, 0.5]]), 3.2)
    bqm = to_dimod(q)
    for x in product((0, 1), repeat=2):
        assert bqm.energy(dict(enumerate(x))) == pytest.approx(q.energy(x))


def test_qiskit_export():
    pytest.importorskip("qiskit")
    q = QUBO(np.array([[-1, 0.3], [0.3, 0.5]]), 3.2)
    diagonal = np.real(np.diag(to_qiskit(q).to_matrix()))
    for code in range(4):
        x = [(code >> i) & 1 for i in range(2)]
        assert diagonal[code] == pytest.approx(q.energy(x))
