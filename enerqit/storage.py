"""Duration-aware battery portfolio selection with independently checked physics.

Select fixed-price availability blocks, not energy-market bids. Batteries provide
constant AC power over one interval, without recharge, ramps or network coupling.
"""

from dataclasses import dataclass
from itertools import product
from math import ceil, floor, isfinite
from time import perf_counter

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from enerqit.qubo import QUBO


def _finite(value: float, name: str, minimum: float, maximum: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float, np.number)):
        raise ValueError(f"{name} must be numeric")
    if not isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be finite in {minimum}..{maximum}")


@dataclass(frozen=True)
class BatteryOffer:
    """One synthetic or caller-supplied constant-power availability offer.

    Energy capacity is nominal DC MWh. State of health scales that capacity;
    start/minimum SOC are fractions of the health-adjusted capacity. Reserved
    DC MWh remain unavailable for this service. Grid/export limits are AC MW.
    Cost is a fixed GBP availability fee for activating the offer, not energy
    revenue, degradation cost or a verified market price.
    """

    id: str
    power_mw: float
    energy_mwh: float
    start_soc: float
    minimum_soc: float
    state_of_health: float
    discharge_efficiency: float
    reserved_dc_mwh: float
    export_limit_mw: float
    reservation_cost_gbp: float
    available: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Offer ID must be nonempty")
        for name in ("power_mw", "energy_mwh", "export_limit_mw"):
            _finite(getattr(self, name), name, 0, 1e6)
        if self.energy_mwh <= 0:
            raise ValueError("energy_mwh must be positive")
        for name in ("start_soc", "minimum_soc", "state_of_health", "discharge_efficiency"):
            _finite(getattr(self, name), name, 0, 1)
        if self.state_of_health <= 0 or self.discharge_efficiency <= 0:
            raise ValueError("State of health and efficiency must be positive")
        if self.minimum_soc > self.start_soc:
            raise ValueError("start_soc cannot be below minimum_soc")
        _finite(self.reserved_dc_mwh, "reserved_dc_mwh", 0, 1e6)
        _finite(self.reservation_cost_gbp, "reservation_cost_gbp", 0, 1e9)
        if type(self.available) is not bool:
            raise ValueError("available must be boolean")


def _offers(offers: list[BatteryOffer]) -> None:
    if not 1 <= len(offers) <= 64 or not all(isinstance(o, BatteryOffer) for o in offers):
        raise ValueError("Supply 1..64 BatteryOffer objects")
    if len({o.id for o in offers}) != len(offers):
        raise ValueError("Offer IDs must be unique")


def deliverable_capacity(
    offers: list[BatteryOffer], duration_hours: float, *, soc_haircut: float = 0.0
) -> list[dict]:
    """Compute sustained AC MW from power, export headroom and usable DC energy.

    ``soc_haircut`` removes a deterministic fraction of health-adjusted capacity;
    it is withheld energy, not a probabilistic confidence bound. Ending SOC is
    calculated from reported start SOC, with this extra buffer left unused.
    """
    _offers(offers)
    _finite(duration_hours, "duration_hours", 1e-6, 168)
    _finite(soc_haircut, "soc_haircut", 0, 1)
    rows = []
    for offer in offers:
        effective = offer.energy_mwh * offer.state_of_health
        accessible = max(0.0, effective * (offer.start_soc - offer.minimum_soc - soc_haircut)
                         - offer.reserved_dc_mwh) if offer.available else 0.0
        ac_energy = accessible * offer.discharge_efficiency
        power = min(offer.power_mw, offer.export_limit_mw) if offer.available else 0.0
        rows.append({"id": offer.id, "effective_capacity_dc_mwh": effective,
                     "available_dc_mwh": accessible, "available_ac_mwh": ac_energy,
                     "power_only_mw": power, "deliverable_mw": min(power, ac_energy / duration_hours),
                     "energy_limit_mw": ac_energy / duration_hours})
    return rows


def evaluate_portfolio(
    offers: list[BatteryOffer], selected, target_mw: float, duration_hours: float,
    *, soc_haircut: float = 0.0,
) -> dict:
    """Independently evaluate constant output, ending SOC and a cover shortfall.

    A feasible selected portfolio can be proportionally curtailed to exactly the
    target. An infeasible portfolio delivers at most its capacity; the remaining
    MW and hypothetical block-energy equivalent are reported explicitly.
    """
    rows = deliverable_capacity(offers, duration_hours, soc_haircut=soc_haircut)
    _finite(target_mw, "target_mw", 0, 1e6)
    bits = np.asarray(selected)
    if bits.shape != (len(offers),) or not np.isin(bits, [0, 1]).all():
        raise ValueError("selected must contain one binary value per offer")
    capacities = np.array([r["deliverable_mw"] for r in rows]) * bits
    total = float(capacities.sum())
    ratio = min(1.0, target_mw / total) if total > 0 else 0.0
    dispatch = capacities * ratio
    shortfall = max(0.0, target_mw - total)
    ending = [o.start_soc - p * duration_hours / o.discharge_efficiency /
              (o.energy_mwh * o.state_of_health) for o, p in zip(offers, dispatch)]
    return {"selected_ids": [o.id for o, b in zip(offers, bits) if b],
            "selected": bits.astype(int).tolist(), "feasible": shortfall <= 1e-8,
            "target_mw": float(target_mw), "duration_hours": float(duration_hours),
            "sustained_capacity_mw": total, "delivered_mw": float(dispatch.sum()),
            "shortfall_mw": shortfall, "block_shortfall_equivalent_mwh": shortfall * duration_hours,
            "reservation_cost_gbp": float(sum(float(o.reservation_cost_gbp) * int(b) for o, b in zip(offers, bits))),
            "dispatch_mw": dispatch.tolist(), "ending_soc": ending,
            "scheduled_ac_mwh": (dispatch * duration_hours).tolist()}


def solve_cover_milp(capacities_mw, costs_gbp, target_mw: float) -> dict:
    """Native binary covering model in physical MW, with no discretization.

    HiGHS solves min(cost @ x), capacities @ x >= target, x in {0,1}.
    Only a proven solver-success status is accepted as optimal. An infeasible
    model returns a distinct status and no fabricated portfolio.
    """
    capacities, costs = np.asarray(capacities_mw, float), np.asarray(costs_gbp, float)
    if (capacities.ndim != 1 or not 1 <= len(capacities) <= 64 or capacities.shape != costs.shape
            or not np.isfinite(capacities).all() or not np.isfinite(costs).all()
            or np.any(capacities < 0) or np.any(costs < 0)):
        raise ValueError("Supply matching finite nonnegative capacity and cost vectors")
    _finite(target_mw, "target_mw", 0, 1e6)
    start = perf_counter()
    result = milp(costs, integrality=np.ones(len(costs)), bounds=Bounds(0, 1),
                  constraints=LinearConstraint(capacities[None, :], target_mw, np.inf),
                  options={"time_limit": 30, "mip_rel_gap": 0.0})
    elapsed = perf_counter() - start
    if result.status == 2:
        return {"status": "infeasible", "selected": None, "cost_gbp": None,
                "elapsed_s": elapsed, "optimal": False}
    if not result.success or result.x is None:
        raise RuntimeError(f"MILP not certified; solver status {result.status}")
    bits = np.rint(result.x).astype(int)
    if not np.isin(bits, [0, 1]).all() or capacities @ bits < target_mw - 1e-7:
        raise RuntimeError("MILP solution failed independent coverage check")
    return {"status": "optimal", "selected": bits.tolist(), "cost_gbp": float(costs @ bits),
            "elapsed_s": elapsed, "optimal": True, "mip_gap": float(result.mip_gap)}


def enumerate_cover(capacities_mw, costs_gbp, target_mw: float) -> dict:
    """Independent native enumeration for at most 20 offers; no QUBO is evaluated."""
    capacities, costs = np.asarray(capacities_mw, float), np.asarray(costs_gbp, float)
    if (capacities.ndim != 1 or not 1 <= len(capacities) <= 20 or capacities.shape != costs.shape
            or not np.isfinite(capacities).all() or not np.isfinite(costs).all()
            or np.any(capacities < 0) or np.any(costs < 0)):
        raise ValueError("Supply 1..20 matching finite nonnegative capacities/costs")
    _finite(target_mw, "target_mw", 0, 1e6)
    start = perf_counter()
    best, best_cost = None, np.inf
    for candidate in product((0, 1), repeat=len(costs)):
        if sum(c * b for c, b in zip(capacities, candidate)) >= target_mw - 1e-9:
            cost = sum(c * b for c, b in zip(costs, candidate))
            if cost < best_cost:
                best, best_cost = list(candidate), float(cost)
    return {"selected": best, "cost_gbp": best_cost if best is not None else None,
            "status": "optimal" if best is not None else "infeasible",
            "elapsed_s": perf_counter() - start, "evaluations": 2 ** len(costs)}


def _slack_weights(maximum: int) -> list[int]:
    weights, remaining, power = [], maximum, 1
    while remaining:
        value = min(power, remaining)
        weights.append(value)
        remaining -= value
        power *= 2
    return weights


def portfolio_qubo(
    capacities_mw, costs_gbp, target_mw: float, *, step_mw: float = 5.0
) -> QUBO:
    """Conservative minimum-cost cover as an existing EnerQit symmetric QUBO.

    Round available MW down and required MW up. Encode cover with bounded binary
    surplus slack: a @ selected - w @ slack = ceil(target/step). Cost plus
    lambda times the squared equality uses lambda=sum(costs)+1; with nonnegative
    costs and integer residuals, any feasible solution is cheaper than any
    infeasible one. The discretized feasible set may exclude a physical optimum.
    """
    capacities, costs = np.asarray(capacities_mw, float), np.asarray(costs_gbp, float)
    if (capacities.ndim != 1 or not 1 <= len(capacities) <= 64 or capacities.shape != costs.shape
            or not np.isfinite(capacities).all() or not np.isfinite(costs).all()
            or np.any(capacities < 0) or np.any(costs < 0)):
        raise ValueError("Supply matching finite nonnegative capacities and costs")
    _finite(target_mw, "target_mw", 0, 1e6)
    _finite(step_mw, "step_mw", 1e-3, 1e6)
    if np.any(capacities / step_mw > 1_000_000):
        raise ValueError("Discretization exceeds one million capacity units")
    units = np.array([floor(c / step_mw) for c in capacities], dtype=np.int64)
    required = ceil(target_mw / step_mw)
    surplus = int(units.sum()) - required
    if surplus < 0:
        raise ValueError("Conservative discretized cover is infeasible; reduce step_mw or target")
    if units.sum() > 1_000_000:
        raise ValueError("Discretization exceeds one million capacity units")
    weights = _slack_weights(surplus)
    coefficients = np.r_[units, -np.array(weights, dtype=float)]
    penalty = float(costs.sum()) + 1.0
    diagonal = np.r_[costs, np.zeros(len(weights))] - 2 * penalty * required * coefficients
    matrix = penalty * np.outer(coefficients, coefficients) + np.diag(diagonal)
    return QUBO(matrix, penalty * required**2,
                constraints=((coefficients[None, :], np.array([required])),),
                metadata={"kind": "duration_aware_battery_cover", "asset_count": len(costs),
                          "capacity_units": units.tolist(), "target_units": required,
                          "slack_weights": weights, "penalty_gbp": penalty,
                          "step_mw": float(step_mw),
                          "convention": "full symmetric x.T @ Q @ x + offset",
                          "discretization": "capacity floor; target ceiling"})
