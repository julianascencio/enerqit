"""Causal, no-recharge battery reserve replay over sequential deficit intervals."""

from collections.abc import Sequence

import numpy as np

from enerqit.storage import BatteryOffer, deliverable_capacity


def replay_reserve(
    offer: BatteryOffer, deficit_mw: Sequence[float], interval_hours: Sequence[float]
) -> dict:
    """Serve AC deficits greedily without recharge; return MW/MWh and DC SOC.

    All intervals are consecutive and piecewise constant. Initial SOC applies
    once, never resets between intervals. Greedy minimizes total unserved MWh
    for this single-device, constant-efficiency, no-recharge model only. It does
    not minimize shortage hours or account for time-dependent outage costs.
    """
    d, h = np.asarray(deficit_mw, float), np.asarray(interval_hours, float)
    if (
        d.ndim != 1
        or not 1 <= len(d) <= 100000
        or h.shape != d.shape
        or not np.isfinite(d).all()
        or not np.isfinite(h).all()
        or np.any(d < 0)
        or np.any(h <= 0)
    ):
        raise ValueError("Provide matching finite deficits >=0 MW and durations >0 hours")
    physics = deliverable_capacity([offer], 1)[0]
    remaining = physics["available_ac_mwh"]
    power = physics["power_only_mw"]
    delivered, energy = [], [remaining]
    for demand, hours in zip(d, h):
        dispatch = min(float(demand), power, remaining / float(hours))
        remaining = max(0.0, remaining - dispatch * float(hours))
        delivered.append(dispatch)
        energy.append(remaining)
    delivered = np.array(delivered)
    used = np.cumsum(delivered * h)
    soc = offer.start_soc - used / (
        offer.discharge_efficiency * physics["effective_capacity_dc_mwh"]
    )
    return {
        "dispatch_mw": delivered.tolist(),
        "remaining_ac_mwh": energy,
        "soc_after": soc.tolist(),
        "unserved_mwh": float((d - delivered) @ h),
        "power_only_unserved_mwh": float(np.maximum(d - power, 0) @ h),
        "delivered_mwh": float(used[-1]),
        "analytic_max_delivery_mwh": min(
            physics["available_ac_mwh"], float(np.minimum(d, power) @ h)
        ),
    }


def screen_reserve_offers(
    offers: Sequence[BatteryOffer],
    deficits_mw: Sequence[Sequence[float]],
    probabilities: Sequence[float],
    interval_hours: Sequence[float],
    target_eens_mwh: float,
) -> dict:
    """Choose one minimum fixed-GBP offer meeting scenario-weighted window EENS.

    Scenarios are mutually exclusive trajectories, each starting at initial SOC.
    No annualization or probability estimation. Cost is the existing BatteryOffer
    whole-service reservation fee; not multiplied by time or expected dispatch.
    """
    p = np.asarray(probabilities, float)
    offers, scenarios = tuple(offers), tuple(deficits_mw)
    if (
        not 1 <= len(offers) <= 100
        or len({o.id for o in offers}) != len(offers)
        or p.ndim != 1
        or len(p) != len(scenarios)
        or not 1 <= len(p) <= 100
        or not np.isfinite(p).all()
        or np.any(p < 0)
        or abs(p.sum() - 1) > 1e-10
        or not np.isfinite(target_eens_mwh)
        or target_eens_mwh < 0
    ):
        raise ValueError("Invalid offers, scenario probability mass or EENS target")
    rows = []
    for offer in offers:
        runs = [replay_reserve(offer, d, interval_hours) for d in scenarios]
        eens = float(p @ [r["unserved_mwh"] for r in runs])
        rows.append(
            {
                "id": offer.id,
                "fee_gbp": offer.reservation_cost_gbp,
                "eens_mwh": eens,
                "power_only_eens_mwh": float(p @ [r["power_only_unserved_mwh"] for r in runs]),
                "feasible": eens <= target_eens_mwh + 1e-8,
                "scenarios": runs,
            }
        )
    feasible = [r for r in rows if r["feasible"]]
    return {
        "offers": rows,
        "selected": min(feasible, key=lambda r: (r["fee_gbp"], r["id"])) if feasible else None,
        "status": "optimal" if feasible else "infeasible",
    }
