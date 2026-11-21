"""Exact initial-energy envelopes for uncertain signed battery activation."""

from collections.abc import Sequence
from dataclasses import dataclass
from time import perf_counter

import numpy as np


@dataclass(frozen=True)
class ActivationWindow:
    """Consecutive piecewise-constant intervals; signed AC MW and elapsed hours.

    Positive activation exports/discharges; negative activation imports/charges.
    Every path in the Cartesian product of interval bounds must be tracked.
    Bounds are declared engineering assumptions, not fitted confidence intervals.
    Energy is usable DC MWh above the physical minimum SOC. No standby loss,
    ramping, thermal dynamics, terminal target or other commitments are included.
    """

    lower_mw: tuple[float, ...]
    upper_mw: tuple[float, ...]
    hours: tuple[float, ...]
    charge_mw: float
    discharge_mw: float
    capacity_dc_mwh: float
    charge_efficiency: float = 0.9
    discharge_efficiency: float = 0.9

    def __post_init__(self) -> None:
        for k in ("lower_mw", "upper_mw", "hours"):
            a = np.asarray(getattr(self, k), float)
            if a.ndim != 1 or not 1 <= len(a) <= 100000 or not np.isfinite(a).all():
                raise ValueError("Need 1..100000 finite interval values")
            object.__setattr__(self, k, tuple(a.tolist()))
        if not len(self.lower_mw) == len(self.upper_mw) == len(self.hours):
            raise ValueError("Activation bounds and durations must align")
        if np.any(np.array(self.lower_mw) > self.upper_mw) or min(self.hours) <= 0:
            raise ValueError("Require lower <= upper MW and positive elapsed hours")
        for k in ("charge_mw", "discharge_mw", "capacity_dc_mwh",
                  "charge_efficiency", "discharge_efficiency"):
            v = getattr(self, k)
            if isinstance(v, (bool, np.bool_)) or not np.isscalar(v) or not np.isfinite(v):
                raise ValueError(f"{k} must be a finite scalar")
            if not 0 <= v <= 1e9:
                raise ValueError(f"{k} outside supported range")
        if not all(1e-6 <= e <= 1 for e in (self.charge_efficiency, self.discharge_efficiency)):
            raise ValueError("Efficiencies must be in [1e-6, 1]")


def initial_energy_envelope(case: ActivationWindow) -> dict:
    """Find all initial DC MWh guaranteeing exact tracking of every allowed path.

    For signed power p, the DC increment is h*(eta_c*max(-p,0)-max(p,0)/eta_d).
    This is monotone decreasing in p. Cumulative all-upper and all-lower paths
    therefore bound every boundary state, including initial energy. Intersecting
    these inequalities gives a necessary and sufficient initial-energy interval.
    This is O(n) time/memory, with no enumeration, optimizer or quantum execution.

    Returns status, lower/upper admissible initial DC MWh (None if infeasible),
    minimum required usable DC capacity ignoring power limits, binding boundary
    indices (0 is initial), power feasibility and runtime. Negative interval width
    is retained as a diagnostic; it is not silently clipped into feasibility.
    """
    start = perf_counter()
    lo, hi, h = map(np.asarray, (case.lower_mw, case.upper_mw, case.hours))

    def cumulative(p):
        return np.r_[0.0, np.cumsum(h * (
            case.charge_efficiency * np.maximum(-p, 0)
            - np.maximum(p, 0) / case.discharge_efficiency
        ))]

    low, high = cumulative(hi), cumulative(lo)
    if not np.isfinite(low).all() or not np.isfinite(high).all():
        raise ValueError("Cumulative energy overflow; rescale inputs")
    lower = float(-low.min())
    upper = float(case.capacity_dc_mwh - high.max())
    power = bool(lo.min() >= -case.charge_mw and hi.max() <= case.discharge_mw)
    feasible = power and lower <= upper
    return {
        "status": "feasible" if feasible else "infeasible",
        "initial_lower_dc_mwh": lower if feasible else None,
        "initial_upper_dc_mwh": upper if feasible else None,
        "energy_interval_width_mwh": upper - lower,
        "required_capacity_dc_mwh": float(high.max() - low.min()),
        "lower_binding_boundary": int(np.argmin(low)),
        "upper_binding_boundary": int(np.argmax(high)),
        "power_feasible": power,
        "runtime_s": perf_counter() - start,
    }


def replay_activation(
    case: ActivationWindow, activation_mw: Sequence[float], initial_dc_mwh: float
) -> dict:
    """Causally clip a declared in-envelope request to AC power and DC energy limits.

    Clipping is a diagnostic fallback, not successful service. Report missed
    absorption and discharge separately in AC MWh; a zero sum of signed tracking
    errors would conceal failures. Final inventory is preserved, not reset.
    """
    p = np.asarray(activation_mw, float)
    if (p.shape != (len(case.hours),) or not np.isfinite(p).all()
            or np.any(p < case.lower_mw) or np.any(p > case.upper_mw)):
        raise ValueError("Requests must lie inside the declared activation bounds")
    if (isinstance(initial_dc_mwh, (bool, np.bool_)) or not np.isscalar(initial_dc_mwh)
            or not np.isfinite(initial_dc_mwh)
            or not 0 <= initial_dc_mwh <= case.capacity_dc_mwh):
        raise ValueError("Initial usable DC energy must lie inside capacity")
    s = float(initial_dc_mwh)
    states, delivered = [s], []
    for request, dt in zip(p, case.hours):
        if request >= 0:
            actual = min(request, case.discharge_mw, s * case.discharge_efficiency / dt)
            s -= actual * dt / case.discharge_efficiency
        else:
            actual = -min(-request, case.charge_mw,
                          (case.capacity_dc_mwh - s) / (dt * case.charge_efficiency))
            s -= actual * dt * case.charge_efficiency
        s = float(np.clip(s, 0, case.capacity_dc_mwh))
        delivered.append(float(actual))
        states.append(s)
    q, h = np.array(delivered), np.array(case.hours)
    c, d = np.maximum(-q, 0), np.maximum(q, 0)
    residual = np.diff(states) - h * (c * case.charge_efficiency - d / case.discharge_efficiency)
    if np.max(abs(residual)) > 1e-7:
        raise RuntimeError("DC energy conservation audit failed")
    return {
        "actual_ac_mw": delivered,
        "energy_dc_mwh": states,
        "missed_absorption_ac_mwh": float(np.maximum(q - p, 0) @ h),
        "missed_discharge_ac_mwh": float(np.maximum(p - q, 0) @ h),
        "conversion_loss_mwh": float((c * (1 - case.charge_efficiency)
                                      + d * (1 / case.discharge_efficiency - 1)) @ h),
        "max_balance_residual_mwh": float(np.max(abs(residual))),
    }


def prepare_activation(
    case: ActivationWindow, initial_dc_mwh: float, preparation_hours: float
) -> dict:
    """Minimize absolute DC inventory movement into the admissible interval.

    Preparation is a separate earlier interval with the same AC power limits and
    efficiencies, unconstrained energy availability/export permission, and no
    competing commitments. Return AC import/export MWh, minimum duration and
    feasibility within the caller's duration. No price or terminal value assumed.
    """
    # Reuse initial-energy validation without altering the requested activation.
    if (isinstance(initial_dc_mwh, (bool, np.bool_)) or not np.isscalar(initial_dc_mwh)
            or not np.isfinite(initial_dc_mwh)
            or not 0 <= initial_dc_mwh <= case.capacity_dc_mwh):
        raise ValueError("Initial usable DC energy must lie inside capacity")
    if (isinstance(preparation_hours, (bool, np.bool_)) or not np.isscalar(preparation_hours)
            or not np.isfinite(preparation_hours) or preparation_hours < 0):
        raise ValueError("Preparation hours must be finite and nonnegative")
    envelope = initial_energy_envelope(case)
    if envelope["status"] != "feasible":
        return {"status": "activation_infeasible", "envelope": envelope}
    target = float(np.clip(initial_dc_mwh, envelope["initial_lower_dc_mwh"],
                           envelope["initial_upper_dc_mwh"]))
    delta = target - initial_dc_mwh
    imported = max(delta, 0) / case.charge_efficiency
    exported = max(-delta, 0) * case.discharge_efficiency
    if (imported > 0 and case.charge_mw == 0) or (exported > 0 and case.discharge_mw == 0):
        return {"status": "preparation_infeasible", "target_dc_mwh": target,
                "minimum_hours": None, "import_ac_mwh": imported, "export_ac_mwh": exported}
    duration = ((imported / case.charge_mw if imported else 0)
                + (exported / case.discharge_mw if exported else 0))
    return {"status": "feasible" if duration <= preparation_hours else "preparation_infeasible",
            "target_dc_mwh": target, "minimum_hours": duration,
            "import_ac_mwh": imported, "export_ac_mwh": exported}
