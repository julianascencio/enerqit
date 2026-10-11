"""Quadratic binary models using the full symmetric ``x.T @ Q @ x`` convention.

Off-diagonal entries in an upper-triangular exporter must be doubled.
The objective constant is preserved, including in Ising conversion.
"""

from dataclasses import dataclass, field

import numpy as np


@dataclass
class QUBO:
    """Binary quadratic objective and separately checked equality constraints.

    Parameters
    ----------
    matrix : array-like, shape (n, n)
        Full matrix; symmetrized without changing the quadratic objective.
    offset : float
        Additive objective constant.
    constraints : tuple of (matrix, target), optional
        Linear equalities used to report feasibility. Penalties must already
        be included in ``matrix`` if an unconstrained solver should honor them.
    groups : tuple of tuple of int
        Disjoint one-hot groups, for specialized classical enumeration.
    """

    matrix: np.ndarray
    offset: float = 0.0
    constraints: tuple = ()
    groups: tuple = ()
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        q = np.asarray(self.matrix, dtype=float)
        if q.ndim != 2 or q.shape[0] != q.shape[1] or q.shape[0] == 0:
            raise ValueError("matrix must be nonempty and square")
        if not np.isfinite(q).all() or not np.isfinite(self.offset):
            raise ValueError("QUBO coefficients must be finite")
        self.matrix = (q + q.T) / 2
        checked = []
        for matrix, target in self.constraints:
            matrix, target = (
                np.atleast_2d(matrix).astype(float),
                np.atleast_1d(target).astype(float),
            )
            if matrix.shape != (len(target), len(q)):
                raise ValueError("constraint dimensions do not match QUBO")
            if not np.isfinite(matrix).all() or not np.isfinite(target).all():
                raise ValueError("constraint coefficients must be finite")
            checked.append((matrix, target))
        self.constraints = tuple(checked)
        flat = [i for group in self.groups for i in group]
        if len(flat) != len(set(flat)) or any(i < 0 or i >= len(q) for i in flat):
            raise ValueError("groups must be disjoint and contain valid indices")
        if any(not group for group in self.groups):
            raise ValueError("empty group")

    @property
    def size(self):
        return self.matrix.shape[0]

    def energy(self, x):
        """Evaluate one vector or a batch with final dimension ``size``."""
        x = np.asarray(x)
        if x.shape[-1] != self.size or not np.isin(x, [0, 1]).all():
            raise ValueError("x must contain binary values with matching size")
        return np.einsum("...i,ij,...j->...", x, self.matrix, x) + self.offset

    def feasible(self, x, atol=1e-7):
        x = np.asarray(x)
        self.energy(x)
        if x.ndim != 1:
            raise ValueError("feasible accepts one candidate")
        return all(np.allclose(c @ x, h, atol=atol, rtol=0) for c, h in self.constraints)

    def to_ising(self):
        """Return h, J, offset for ``.5*s.T@J@s + h@s + offset``.

        The convention is ``x=(s+1)/2``. J is symmetric with zero diagonal.
        """
        q = self.matrix
        j = q / 2
        j = j.copy()
        np.fill_diagonal(j, 0)
        h = q.sum(axis=1) / 2
        offset = self.offset + (q.sum() + np.trace(q)) / 4
        return h, j, float(offset)

    def to_upper(self):
        """Return an upper-triangular QUBO dictionary including nonzero terms."""
        return {
            (i, j): float(self.matrix[i, j] * (1 if i == j else 2))
            for i in range(self.size)
            for j in range(i, self.size)
            if self.matrix[i, j] != 0
        }


def least_squares_qubo(
    templates,
    observations,
    *,
    weights=None,
    groups=(),
    penalty=10.0,
    equality=None,
    equality_penalty=None,
):
    """Encode template least squares plus one-hot and optional inventory penalties.

    Parameters
    ----------
    templates : array-like, shape (n_observations, n_candidates)
        Contributions whose weighted sum represents the observations. Normalize
        physical channels before construction (for example V/Vnom and I/Inom).
    observations : array-like, shape (n_observations,)
        Observed values in the same units as templates.
    weights : array-like, optional
        Nonnegative observation weights. This encodes weighted squared error,
        not a robust loss or an arbitrary nonlinear physical model.
    groups : sequence of index sequences
        Candidate groups, each selecting exactly one member.
    penalty : float
        One-hot penalty. Must be tuned; no universal feasibility guarantee.
    equality : (matrix, target), optional
        Additional linear constraints, for example total installed string count.
    equality_penalty : float, optional
        Inventory penalty; defaults to ``penalty``.
    """
    a, y = np.asarray(templates, float), np.asarray(observations, float)
    if a.ndim != 2 or y.shape != (len(a),) or not np.isfinite(a).all() or not np.isfinite(y).all():
        raise ValueError("finite templates (rows, candidates) and matching observations required")
    w = np.ones(len(y)) if weights is None else np.asarray(weights, float)
    if w.shape != y.shape or not np.isfinite(w).all() or np.any(w < 0) or not np.any(w > 0):
        raise ValueError("weights must be finite, nonnegative, and nonzero")
    if not np.isfinite(penalty) or penalty <= 0:
        raise ValueError("penalty must be positive")
    q = a.T @ (w[:, None] * a)
    q += np.diag(-2 * a.T @ (w * y))
    offset = float(y @ (w * y))
    constraints = []
    groups = tuple(tuple(g) for g in groups)
    if groups:
        c = np.zeros((len(groups), a.shape[1]))
        for row, group in enumerate(groups):
            c[row, list(group)] = 1
        constraints.append((c, np.ones(len(groups)), penalty))
    if equality is not None:
        lam = penalty if equality_penalty is None else equality_penalty
        if not np.isfinite(lam) or lam <= 0:
            raise ValueError("equality_penalty must be positive")
        c, h = np.atleast_2d(equality[0]).astype(float), np.atleast_1d(equality[1]).astype(float)
        if c.shape != (len(h), a.shape[1]):
            raise ValueError("invalid equality dimensions")
        constraints.append((c, h, lam))
    for c, h, lam in constraints:
        q += lam * c.T @ c + np.diag(-2 * lam * c.T @ h)
        offset += float(lam * h @ h)
    return QUBO(
        q,
        offset,
        tuple((c, h) for c, h, _ in constraints),
        groups,
        {"kind": "weighted_template_least_squares", "penalty": penalty},
    )
