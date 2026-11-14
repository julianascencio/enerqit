"""Exact small-fleet adequacy with an explicit fleet-wide common-outage state."""

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import product
from math import isfinite, prod
from time import perf_counter


def _number(value: float, name: str, low: float = 0, high: float = float("inf")) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
        or not low <= value <= high
    ):
        raise ValueError(f"{name} must be finite in [{low}, {high}]")


@dataclass(frozen=True)
class CapacityUnit:
    """MW and outage probability CONDITIONAL on no common outage in the window."""

    capacity_mw: float
    outage_probability: float

    def __post_init__(self) -> None:
        _number(self.capacity_mw, "capacity_mw")
        _number(self.outage_probability, "outage_probability", 0, 1)


def capacity_states(
    units: Sequence[CapacityUnit], common_outage_probability: float = 0
) -> list[dict]:
    """Enumerate independent conditional outages plus one all-units-out state.

    The common event disables every listed unit. Do not include guaranteed
    reserves here. Marginal unit outage is q+(1-q)*p, not p. No repair dynamics,
    temporal dependence, partial deratings or weather distributions are inferred.
    """
    units = tuple(units)
    if not 1 <= len(units) <= 16 or any(not isinstance(u, CapacityUnit) for u in units):
        raise ValueError("Provide 1..16 CapacityUnit objects")
    _number(common_outage_probability, "common_outage_probability", 0, 1)
    q = common_outage_probability
    states = []
    for online in product((False, True), repeat=len(units)):
        probability = (1 - q) * prod(
            (1 - u.outage_probability) if on else u.outage_probability
            for u, on in zip(units, online)
        )
        if probability:
            states.append(
                {
                    "available_mw": sum(u.capacity_mw for u, on in zip(units, online) if on),
                    "probability": probability,
                }
            )
    if q:
        states.append({"available_mw": 0.0, "probability": q})
    return states


def window_risk(
    states: Sequence[dict], demand_mw: float, *, hours: float = 1, firm_mw: float = 0
) -> dict:
    """LOLP, expected shortfall MW, EENS MWh and LOLE hours for one window.

    States describe the entire constant-demand window. Results are NOT annual
    LOLE/EENS and must not be multiplied into a year without a chronology model.
    firm_mw is guaranteed delivered capacity outside the outage model.
    """
    _number(demand_mw, "demand_mw")
    _number(hours, "hours", 1e-12)
    _number(firm_mw, "firm_mw")
    states = tuple(states)
    if not states:
        raise ValueError("States must be nonempty")
    for s in states:
        _number(s["available_mw"], "available_mw")
        _number(s["probability"], "probability", 0, 1)
    mass = sum(s["probability"] for s in states)
    if abs(mass - 1) > 1e-10:
        raise ValueError("State probabilities must sum to one; not normalized silently")
    expected = sum(
        s["probability"] * max(demand_mw - firm_mw - s["available_mw"], 0) for s in states
    )
    lolp = sum(s["probability"] for s in states if s["available_mw"] + firm_mw < demand_mw - 1e-9)
    return {
        "lolp": lolp,
        "expected_shortfall_mw": expected,
        "eens_mwh": expected * hours,
        "lole_hours": lolp * hours,
        "mean_available_mw": sum(s["probability"] * s["available_mw"] for s in states),
        "probability_mass": mass,
    }


def screen_firm_capacity(
    states: Sequence[dict],
    demand_mw: float,
    hours: float,
    offers: Sequence[tuple[float, float]],
    target_eens_mwh: float,
) -> dict:
    """Choose cheapest (guaranteed MW, fixed EUR window fee) meeting EENS target.

    Exhaustive finite offer screen; target and fees are caller assumptions, not a
    regulatory standard or market quotation. Fee is not multiplied by hours.
    """
    _number(target_eens_mwh, "target_eens_mwh")
    offers = tuple(offers)
    if not offers or len(offers) > 1000:
        raise ValueError("Provide 1..1000 offers")
    start = perf_counter()
    rows = []
    for mw, fee in offers:
        _number(fee, "fee_eur")
        r = window_risk(states, demand_mw, hours=hours, firm_mw=mw)
        rows.append(
            {
                "firm_mw": mw,
                "fee_eur": fee,
                "meets_target": r["eens_mwh"] <= target_eens_mwh + 1e-9,
                **r,
            }
        )
    feasible = [r for r in rows if r["meets_target"]]
    return {
        "status": "optimal" if feasible else "infeasible",
        "selected": min(feasible, key=lambda r: (r["fee_eur"], r["firm_mw"]))
        if feasible
        else None,
        "offers": rows,
        "runtime_s": perf_counter() - start,
    }
