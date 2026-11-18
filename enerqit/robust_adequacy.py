"""Finite-support total-variation robustness for window adequacy."""

from collections.abc import Sequence
from time import perf_counter

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import bmat, csr_matrix, eye

from enerqit.adequacy import _number, window_risk


def worst_case_eens(
    states: Sequence[dict],
    demand_mw: float,
    *,
    hours: float = 1,
    firm_mw: float = 0,
    radius: float = 0,
) -> dict:
    """Maximize window EENS over probabilities within total variation ``radius``.

    Support capacities stay fixed; probabilities may vary, including zero-mass
    supplied states. No omitted capacity states are invented. Radius is in [0,1]
    and is an engineering assumption, not a confidence level. Sparse LP uses
    2*n variables and 2*n+1 inequalities, capped at 4096 supplied states.
    """
    states = tuple(states)
    if not 1 <= len(states) <= 4096:
        raise ValueError("Provide 1..4096 states")
    _number(radius, "radius", 0, 1)
    nominal = window_risk(states, demand_mw, hours=hours, firm_mw=firm_mw)
    p = np.array([s["probability"] for s in states], dtype=float)
    losses = np.array([max(demand_mw - firm_mw - s["available_mw"], 0) * hours for s in states])
    n = len(p)
    ident = eye(n, format="csr")
    constraints = bmat(
        [[ident, -ident], [-ident, -ident], [csr_matrix((1, n)), csr_matrix(np.ones((1, n)))]],
        format="csr",
    )
    start = perf_counter()
    result = linprog(
        np.r_[-losses, np.zeros(n)],
        A_ub=constraints,
        b_ub=np.r_[p, -p, 2 * radius],
        A_eq=csr_matrix(np.r_[np.ones(n), np.zeros(n)][None, :]),
        b_eq=[1.0],
        bounds=(0, 1),
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"Worst-case LP failed: {result.message}")
    q = result.x[:n]
    tv = float(np.abs(q - p).sum() / 2)
    mass_error = float(abs(q.sum() - 1))
    if mass_error > 1e-7 or tv > radius + 1e-7 or q.min() < -1e-7:
        raise RuntimeError("LP probability audit failed")
    return {
        "nominal_eens_mwh": nominal["eens_mwh"],
        "worst_eens_mwh": float(q @ losses),
        "worst_probabilities": q.tolist(),
        "total_variation": tv,
        "probability_mass_error": mass_error,
        "runtime_s": perf_counter() - start,
        "solver": "classical HiGHS LP",
    }


def robust_capacity_offers(
    states: Sequence[dict],
    demand_mw: float,
    hours: float,
    offers: Sequence[tuple[float, float]],
    target_eens_mwh: float,
    radius: float,
) -> dict:
    """Cheapest fixed-EUR window offer satisfying worst-case EENS, MW capacity.

    Capacity is guaranteed outside modeled failures. Search is exhaustive over
    supplied offers only. Infeasibility is retained rather than relaxing target.
    """
    states, offers = tuple(states), tuple(offers)
    _number(target_eens_mwh, "target_eens_mwh")
    if not 1 <= len(offers) <= 100:
        raise ValueError("Provide 1..100 offers")
    rows = []
    for mw, fee in offers:
        _number(fee, "fee_eur")
        r = worst_case_eens(states, demand_mw, hours=hours, firm_mw=mw, radius=radius)
        rows.append(
            {
                "firm_mw": mw,
                "fee_eur": fee,
                **r,
                "feasible": r["worst_eens_mwh"] <= target_eens_mwh + 1e-7,
            }
        )
    feasible = [r for r in rows if r["feasible"]]
    return {
        "offers": rows,
        "selected": min(feasible, key=lambda r: (r["fee_eur"], r["firm_mw"]))
        if feasible
        else None,
        "status": "optimal" if feasible else "infeasible",
    }
