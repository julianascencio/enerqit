"""Renewable capacity procurement with interval versus total-energy matching."""

from collections.abc import Sequence
from time import perf_counter

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, eye, hstack, vstack


def procure_matching(
    profiles: Sequence[Sequence[float]],
    demand_mw: Sequence[float],
    hours: Sequence[float],
    costs_eur_per_mw: Sequence[float],
    capacity_limits_mw: Sequence[float],
    *,
    target_fraction: float = 1.0,
    interval_matching: bool = True,
) -> dict:
    """Minimize fixed horizon procurement cost for a renewable matching target.

    Parameters
    ----------
    profiles : sequence of sequences
        Resource-by-interval AC MW per contracted MW, each value in [0, 1].
    demand_mw, hours : sequence of float
        Nonnegative buyer load and positive elapsed interval durations. Ordered,
        aligned, piecewise constant; timezone alignment belongs to the caller.
    costs_eur_per_mw : sequence of float
        Positive capacity contract costs in EUR/MW for this exact horizon.
        Not LCOE, spot prices, annualized costs or a settlement model.
    capacity_limits_mw : sequence of float
        Nonnegative available capacity per contract in MW.
    target_fraction : float
        Required fraction of total demand energy, in [0, 1].
    interval_matching : bool
        If true, count only simultaneous min(load, generation); otherwise allow
        surplus from any interval to offset deficits elsewhere in the total.

    Returns
    -------
    dict
        Contracted MW, cost EUR, simultaneous matching fraction, excess and
        unmatched MWh, traces and physical audit. Infeasible status is explicit.

    Notes
    -----
    No storage, losses, network deliverability, certificates, additionality,
    emissions attribution or legal compliance claim. Fraction is energy weighted,
    not fraction of hours. A zero-demand horizon has matching fraction 1.
    Bounded to 64 resources, 8760 intervals, MW <=1e6 and hours <=8760.
    """
    p, d, h, c, cap = [
        np.asarray(x, float)
        for x in (profiles, demand_mw, hours, costs_eur_per_mw, capacity_limits_mw)
    ]
    if (
        p.ndim != 2
        or not 1 <= p.shape[0] <= 64
        or d.ndim != 1
        or not 1 <= len(d) <= 8760
        or p.shape[1] != len(d)
        or h.shape != d.shape
        or c.shape != (p.shape[0],)
        or cap.shape != c.shape
        or any(not np.isfinite(x).all() for x in (p, d, h, c, cap))
        or np.any(p < 0)
        or np.any(p > 1)
        or np.any(d < 0)
        or np.any(d > 1e6)
        or np.any(h <= 0)
        or np.any(h > 8760)
        or np.any(c <= 0)
        or np.any(c > 1e9)
        or np.any(cap < 0)
        or np.any(cap > 1e6)
        or not np.isfinite(target_fraction)
        or not 0 <= target_fraction <= 1
        or type(interval_matching) is not bool
    ):
        raise ValueError("Invalid resource/interval arrays, cost, target or mode")
    n, t = p.shape
    total = float(d @ h)
    required = target_fraction * total
    start = perf_counter()
    if interval_matching:
        a = vstack(
            [hstack([-csr_matrix(p.T), eye(t)]), csr_matrix(np.r_[np.zeros(n), -h][None, :])],
            format="csr",
        )
        b = np.r_[np.zeros(t), -required]
        objective = np.r_[c, np.zeros(t)]
        bounds = list(zip(np.zeros(n), cap)) + list(zip(np.zeros(t), d))
    else:
        a = csr_matrix(-(p @ h)[None, :])
        b = [-required]
        objective = c
        bounds = list(zip(np.zeros(n), cap))
    sol = linprog(objective, A_ub=a, b_ub=b, bounds=bounds, method="highs")
    if sol.status == 2:
        return dict(
            feasible=False,
            reason="Target unattainable with supplied profiles/capacity",
            solver="classical HiGHS LP",
        )
    if not sol.success:
        raise RuntimeError(sol.message)
    x = sol.x[:n]
    generation = x @ p
    matched = np.minimum(generation, d)
    match = float(matched @ h)
    produced = float(generation @ h)
    violation = max(
        float(np.max(-x)),
        float(np.max(x - cap)),
        required - (match if interval_matching else produced),
        0.0,
    )
    if violation > 1e-6 or not np.isclose(c @ x, sol.fun, rtol=1e-8, atol=1e-6):
        raise RuntimeError("Physical or objective audit failed")
    return dict(
        feasible=True,
        capacity_mw=x.tolist(),
        generation_mw=generation.tolist(),
        matched_mw=matched.tolist(),
        cost_eur=float(c @ x),
        matched_mwh=match,
        unmatched_mwh=total - match,
        excess_mwh=produced - match,
        total_generation_mwh=produced,
        demand_mwh=total,
        matching_fraction=match / total if total else 1.0,
        max_violation=violation,
        runtime_s=perf_counter() - start,
        solver="classical HiGHS LP",
    )
