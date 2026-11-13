"""Strict chronological holdouts, causal battery replay and explicit cost scenarios."""

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from enerqit.experiments import fingerprint
from enerqit.storage_sizing import FirmingCase, minimum_storage

OPSD_COLUMNS = {
    "utc_timestamp": "timestamp",
    "DE_solar_generation_actual": "solar_mw",
    "DE_wind_generation_actual": "wind_mw",
    "DE_load_actual_entsoe_transparency": "demand_mw",
}


def validate_profiles(frame) -> pd.DataFrame:
    """Require increasing, unique, regular UTC timestamps and finite MW data.

    No resampling, interpolation, sorting or timezone guessing happens silently.
    These are power averages over intervals starting at each timestamp.
    """
    result = frame.copy()
    if not isinstance(result.index, pd.DatetimeIndex) or result.index.tz is None:
        raise ValueError("Profiles need timezone-aware timestamps")
    result.index = result.index.tz_convert("UTC")
    if (
        len(result) < 2
        or result.index.hasnans
        or not result.index.is_unique
        or not result.index.is_monotonic_increasing
    ):
        raise ValueError("Need at least two ordered unique timestamps")
    delta = np.diff(result.index.asi8)
    if not np.all(delta == delta[0]) or delta[0] <= 0:
        raise ValueError("Missing or irregular intervals must be resolved explicitly")
    columns = ["solar_mw", "wind_mw", "demand_mw"]
    if not all(c in result for c in columns):
        raise ValueError(f"Required columns: {columns}")
    values = result[columns].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any() or result.demand_mw.sum() <= 0:
        raise ValueError("MW values must be finite, nonnegative, with positive demand")
    return result[columns].astype(float)


def read_profiles(path, *, columns=None, start=None, end=None):
    """Read explicit column mapping, returning validated data and source hashes.

    ``columns`` maps original names to timestamp/solar_mw/wind_mw/demand_mw.
    ``end`` is exclusive. A complete file hash identifies the source; the used
    slice has a separate hash. Source rights remain those of the data provider.
    """
    path = Path(path)
    mapping = columns or {c: c for c in ("timestamp", "solar_mw", "wind_mw", "demand_mw")}
    if set(mapping.values()) != {"timestamp", "solar_mw", "wind_mw", "demand_mw"}:
        raise ValueError("Column mapping must cover the four canonical fields exactly")
    frame = pd.read_csv(path, usecols=list(mapping)).rename(columns=mapping)
    if not frame.timestamp.astype(str).str.contains(r"(?:Z|[+-]\d{2}:?\d{2})$", regex=True).all():
        raise ValueError("CSV timestamps must contain an explicit timezone offset")
    frame.index = pd.to_datetime(frame.pop("timestamp"), utc=True, errors="raise")
    if start is not None:
        frame = frame.loc[frame.index >= pd.Timestamp(start)]
    if end is not None:
        frame = frame.loc[frame.index < pd.Timestamp(end)]
    frame = validate_profiles(frame)
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return frame, {
        "source_sha256": digest.hexdigest(),
        "slice_sha256": hashlib.sha256(frame.to_csv().encode()).hexdigest(),
        "columns": mapping,
        "start": frame.index[0].isoformat(),
        "last_interval_start": frame.index[-1].isoformat(),
        "intervals": len(frame),
    }


def replay_storage(case, capacity_mwh, *, initial_soc_fraction=0.5, reserve_fraction=0.0):
    """Causal greedy dispatch with fixed capacity, no backup and no future data.

    Charge on surplus, discharge on deficit; retain unserved energy rather than
    relaxing physics. Initial inventory is supplied explicitly, final inventory
    is reported and never reset mid-horizon. This is a replay, not an optimizer.
    """
    if not np.isfinite(capacity_mwh) or capacity_mwh < 0 or capacity_mwh > case.max_energy_mwh:
        raise ValueError("Capacity must be within the declared search bound")
    if not 0 <= reserve_fraction <= initial_soc_fraction <= 1:
        raise ValueError("Require 0 <= reserve <= initial SOC <= 1")
    n = len(case.demand_mw)
    c, d, shortfall, spill = (np.zeros(n) for _ in range(4))
    s = np.zeros(n + 1)
    s[0] = initial_soc_fraction * capacity_mwh
    floor = reserve_fraction * capacity_mwh
    for t, (r, load) in enumerate(zip(case.renewable_mw, case.demand_mw)):
        if r >= load:
            c[t] = min(
                r - load,
                case.power_mw,
                max(0, capacity_mwh - s[t]) / (case.hours * case.charge_efficiency),
            )
        else:
            d[t] = min(
                load - r,
                case.power_mw,
                max(0, s[t] - floor) * case.discharge_efficiency / case.hours,
            )
        s[t + 1] = s[t] + case.hours * (
            case.charge_efficiency * c[t] - d[t] / case.discharge_efficiency
        )
        balance = r + d[t] - c[t] - load
        shortfall[t], spill[t] = max(0, -balance), max(0, balance)
    residual = np.diff(s) - case.hours * (
        case.charge_efficiency * c - d / case.discharge_efficiency
    )
    balance = np.asarray(case.renewable_mw) + d - c + shortfall - spill - case.demand_mw
    physical = bool(
        np.max(abs(residual)) < 1e-7
        and np.max(abs(balance)) < 1e-7
        and s.min() >= floor - 1e-7
        and s.max() <= capacity_mwh + 1e-7
        and max(c.max(), d.max()) <= case.power_mw + 1e-7
        and np.max(np.minimum(c, d)) <= 1e-7
    )
    unserved = float(shortfall.sum() * case.hours)
    return {
        "physical_feasible": physical,
        "full_load_served": unserved <= 1e-7,
        "unserved_mwh": unserved,
        "served_mwh": float(sum(case.demand_mw) * case.hours - unserved),
        "shortfall_hours": float(np.count_nonzero(shortfall > 1e-7) * case.hours),
        "spill_mwh": float(spill.sum() * case.hours),
        "capacity_mwh": capacity_mwh,
        "initial_energy_mwh": float(s[0]),
        "final_energy_mwh": float(s[-1]),
        "max_balance_residual_mw": float(np.max(abs(balance))),
        "max_energy_residual_mwh": float(np.max(abs(residual))),
        "charge_mw": c.tolist(),
        "discharge_mw": d.tolist(),
        "energy_mwh": s.tolist(),
    }


@dataclass(frozen=True)
class LifecycleCosts:
    """User-supplied EUR cost scenario, not market prices or a bankable appraisal.

    Values cover the configured assets only. Annual opex and other initial costs
    let users include land, grid and engineering. Financing is represented only
    by the discount rate; tax, inflation and salvage are excluded explicitly.
    Replacement years are end-of-year cash flows, before the project ends.
    """

    energy_eur_per_mwh: float
    power_eur_per_mw: float
    renewable_capex_eur: float
    other_initial_eur: float
    annual_opex_eur: float
    years: int = 20
    discount_rate: float = 0.06
    replacement_years: tuple[int, ...] = (10,)
    replacement_energy_fraction: float = 0.7

    def __post_init__(self):
        for k in (
            "energy_eur_per_mwh",
            "power_eur_per_mw",
            "renewable_capex_eur",
            "other_initial_eur",
            "annual_opex_eur",
            "discount_rate",
            "replacement_energy_fraction",
        ):
            value = getattr(self, k)
            if isinstance(value, bool) or not np.isfinite(value) or value < 0:
                raise ValueError(f"{k} must be finite and nonnegative")
        if type(self.years) is not int or self.years < 1:
            raise ValueError("years must be a positive integer")
        if len(set(self.replacement_years)) != len(self.replacement_years) or any(
            type(y) is not int or not 1 <= y < self.years for y in self.replacement_years
        ):
            raise ValueError("Replacement years must be distinct and inside the project horizon")

    def evaluate(self, capacity_mwh, power_mw) -> dict:
        """Discount itemized costs, without assuming revenue or annual reliability."""
        if not all(np.isfinite(v) and v >= 0 for v in (capacity_mwh, power_mw)):
            raise ValueError("Capacity and power must be nonnegative")
        battery_energy = capacity_mwh * self.energy_eur_per_mwh
        initial = (
            battery_energy
            + power_mw * self.power_eur_per_mw
            + self.renewable_capex_eur
            + self.other_initial_eur
        )
        flows = [
            {
                "year": 0,
                "capital_eur": initial,
                "opex_eur": 0.0,
                "replacement_eur": 0.0,
                "present_eur": initial,
            }
        ]
        for year in range(1, self.years + 1):
            replacement = (
                battery_energy * self.replacement_energy_fraction
                if year in self.replacement_years
                else 0
            )
            flows.append(
                {
                    "year": year,
                    "capital_eur": 0.0,
                    "opex_eur": self.annual_opex_eur,
                    "replacement_eur": replacement,
                    "present_eur": (replacement + self.annual_opex_eur)
                    / (1 + self.discount_rate) ** year,
                }
            )
        return {
            "assumptions": asdict(self),
            "cashflows": flows,
            "net_present_cost_eur": sum(row["present_eur"] for row in flows),
            "excluded": ["tax", "inflation", "salvage", "revenue", "unconfigured costs"],
        }


def run_chronological_study(
    frame,
    *,
    split_at,
    provenance,
    renewable_multiple=1.7,
    wind_share=0.5,
    power_mw=3.0,
    max_energy_mwh=10000.0,
    initial_soc_fraction=0.5,
    reserve_fraction=0.0,
    annual_capacity_fade=0.02,
    aging_years=10,
    costs=None,
    time_limit_s=30.0,
) -> dict:
    """Fit scaling and size only on training data; freeze them for later replay.

    The mix uses observed aggregate shapes scaled by training means. It is a
    hypothetical supply system, not an actual co-located plant. Aging is an
    explicit calendar-capacity stress scenario, not an electrochemical model.
    The test horizon is replayed at beginning and end of the specified aging
    period; it is not repeated and mislabeled as multi-year observed weather.
    """
    frame = validate_profiles(frame)
    split = pd.Timestamp(split_at)
    if split.tzinfo is None:
        raise ValueError("split_at must be timezone-aware")
    if not np.isfinite(renewable_multiple) or renewable_multiple <= 0 or not 0 <= wind_share <= 1:
        raise ValueError("Positive renewable multiple and wind_share in [0,1] required")
    if not 0 <= annual_capacity_fade < 1 or type(aging_years) is not int or aging_years < 0:
        raise ValueError("Invalid calendar fade scenario")
    training = frame.loc[frame.index < split]
    holdout = frame.loc[frame.index >= split]
    if min(len(training), len(holdout)) < 2:
        raise ValueError("Both chronological partitions need at least two intervals")
    means = training.mean()
    if (means <= 0).any():
        raise ValueError("Training means must be positive for shape normalization")
    hours = (frame.index[1] - frame.index[0]).total_seconds() / 3600

    def case(part):
        renewable = renewable_multiple * (
            (1 - wind_share) * part.solar_mw / means.solar_mw
            + wind_share * part.wind_mw / means.wind_mw
        )
        return FirmingCase(
            tuple(renewable),
            tuple(part.demand_mw / means.demand_mw),
            power_mw,
            max_energy_mwh,
            hours=hours,
        )

    train_case, test_case = case(training), case(holdout)
    frozen = {
        "training_means_mw": means.to_dict(),
        "renewable_multiple": renewable_multiple,
        "wind_share": wind_share,
        "power_mw": power_mw,
        "split_at": split.isoformat(),
        "max_energy_mwh": max_energy_mwh,
        "hours": hours,
        "charge_efficiency": train_case.charge_efficiency,
        "discharge_efficiency": train_case.discharge_efficiency,
        "initial_soc_fraction": initial_soc_fraction,
        "reserve_fraction": reserve_fraction,
        "annual_capacity_fade": annual_capacity_fade,
        "aging_years": aging_years,
        "cost_assumptions": None if costs is None else asdict(costs),
        "time_limit_s": time_limit_s,
        "sizing_model": "physical net-balance LP",
    }
    sizing = minimum_storage(
        train_case, time_limit_s=time_limit_s, net_balance_modes=True, allow_incomplete=True
    )
    result = {
        "provenance": provenance,
        "frozen_parameters": frozen,
        "training_intervals": len(training),
        "holdout_intervals": len(holdout),
        "input_sha256": fingerprint(
            {"data": hashlib.sha256(frame.to_csv().encode()).hexdigest(), "parameters": frozen}
        ),
        "training": sizing,
        "holdout": None,
        "aged_holdout": None,
        "interpretation": "Observed aggregate profiles; hypothetical scaled assets; no site validation",
    }
    if sizing["status"] != "optimal":
        return result
    capacity = sizing["capacity_mwh"]
    result["holdout"] = replay_storage(
        test_case,
        capacity,
        initial_soc_fraction=initial_soc_fraction,
        reserve_fraction=reserve_fraction,
    )
    retention = (1 - annual_capacity_fade) ** aging_years
    result["aged_holdout"] = replay_storage(
        test_case,
        capacity * retention,
        initial_soc_fraction=initial_soc_fraction,
        reserve_fraction=reserve_fraction,
    )
    result["aging_assumption"] = {
        "years": aging_years,
        "annual_capacity_fade": annual_capacity_fade,
        "capacity_retention": retention,
        "model": "calendar-only sensitivity",
    }
    result["economics"] = None if costs is None else costs.evaluate(capacity, power_mw)
    return result
