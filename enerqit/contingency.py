"""Preventive DC dispatch for explicit, non-islanding single-line outages."""

from collections.abc import Sequence
from dataclasses import replace
from time import perf_counter

import numpy as np
from scipy.optimize import linprog

from enerqit.network import DispatchCase, evaluate_dispatch, network_matrices


def outage_cases(
    case: DispatchCase, outages: Sequence[int] | None = None
) -> list[tuple[int | None, DispatchCase]]:
    """Base topology plus requested outages; reject islands rather than omit them.

    None means every line. An empty sequence is an explicit base-only ablation.
    Line IDs are zero-based positions in the original case, including parallel lines.
    """
    ids = list(range(len(case.lines))) if outages is None else list(outages)
    if any(type(i) is not int or not 0 <= i < len(case.lines) for i in ids):
        raise ValueError("Invalid outage index")
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate outage index")
    if len(ids) > 50:
        raise ValueError("At most 50 contingencies supported by this dense prototype")
    result = [(None, case)]
    for i in ids:
        try:
            changed = replace(case, lines=tuple(v for j, v in enumerate(case.lines) if j != i))
        except ValueError as exc:
            raise ValueError(
                f"Outage {i} disconnects the modeled network; island analysis required"
            ) from exc
        result.append((i, changed))
    return result


def audit_outages(
    case: DispatchCase,
    renewable_mw: Sequence[float],
    firm_mw: Sequence[float],
    outages: Sequence[int] | None = None,
) -> dict:
    """Hold injections fixed and independently re-solve every selected topology."""
    rows = [
        {"outage_index": i, **evaluate_dispatch(p, renewable_mw, firm_mw)}
        for i, p in outage_cases(case, outages)
    ]
    return {
        "secure_for_selected_outages": all(r["dc_feasible"] for r in rows),
        "worst_overload_mw": max(r["max_overload_mw"] for r in rows),
        "states": rows,
    }


def solve_preventive_dispatch(case: DispatchCase, outages: Sequence[int] | None = None) -> dict:
    """Minimize one-interval firm EUR cost with common injections in every state.

    Uses reduced nodal flow sensitivities, not post-outage corrective redispatch.
    Bounds, MW/MWh semantics and lossless assumptions follow DispatchCase.
    No generator outages, emergency ratings, probabilities or load shedding.
    """
    start = perf_counter()
    states = outage_cases(case, outages)
    n = len(case.demand_mw)
    rows, rhs = [], []
    for _, p in states:
        h, lap = network_matrices(p)
        # Solve rather than invert; column zero is the reference injection.
        transfer = np.zeros((len(p.lines), n))
        transfer[:, 1:] = np.linalg.solve(lap[1:, 1:].T, h[:, 1:].T).T
        block = np.c_[transfer, transfer]
        load = transfer @ np.array(case.demand_mw)
        ratings = np.array([line.limit_mw for line in p.lines])
        rows.extend([block, -block])
        rhs.extend([ratings + load, ratings - load])
    a, b = np.vstack(rows), np.concatenate(rhs)
    costs = np.r_[np.zeros(n), np.array(case.firm_cost_eur_mwh) * case.hours]
    construction = perf_counter() - start
    start = perf_counter()
    result = linprog(
        costs,
        A_ub=a,
        b_ub=b,
        A_eq=np.ones((1, 2 * n)),
        b_eq=[sum(case.demand_mw)],
        bounds=[(0, v) for v in (*case.renewable_mw, *case.firm_capacity_mw)],
        method="highs",
    )
    resource = {
        "construction_s": construction,
        "solver_s": perf_counter() - start,
        "variables": 2 * n,
        "inequality_rows": len(b),
        "matrix_bytes": a.nbytes,
        "outages": [i for i, _ in states[1:]],
    }
    if result.status == 2:
        return {"status": "infeasible", "audit": None, **resource}
    if not result.success:
        raise RuntimeError(f"LP failed: {result.status}")
    audit = audit_outages(case, result.x[:n], result.x[n:], resource["outages"])
    if not audit["secure_for_selected_outages"]:
        raise RuntimeError("Preventive dispatch failed independent audit")
    return {"status": "optimal", "cost_eur": float(costs @ result.x), "audit": audit, **resource}
