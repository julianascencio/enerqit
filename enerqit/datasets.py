"""Deterministic synthetic evidence; no real plant or OEM measurements are bundled."""

import numpy as np
import pandas as pd
import pvlib

from enerqit.pvsystem import fixed_ac
from enerqit.qubo import least_squares_qubo


def weather(*, start="2025-06-01", days=5, freq="15min", latitude=35.0, longitude=-5.0):
    """Generate timezone-aware clear-sky weather without a network call."""
    if days <= 0:
        raise ValueError("days must be positive")
    first = pd.Timestamp(start)
    first = first.tz_localize("UTC") if first.tzinfo is None else first.tz_convert("UTC")
    index = pd.date_range(first, first + pd.Timedelta(days=days), freq=freq, inclusive="left")
    site = pvlib.location.Location(latitude, longitude, tz="UTC", altitude=100)
    data = site.get_clearsky(index, model="ineichen", linke_turbidity=3.0)
    data["temp_air"] = 22 + 7 * np.sin(2 * np.pi * (index.hour.to_numpy() - 8) / 24)
    data["wind_speed"] = 2.0
    data.index.name = "timestamp"
    return data


def fixed_array(*, seed=42, days=5, tilt=28.0, azimuth=172.0, noise_w=80.0):
    """Weather and noisy AC power with known 100 kWdc / 90 kWac configuration."""
    frame = weather(days=days)
    expected = fixed_ac(frame, 35, -5, tilt, azimuth)
    noise = np.random.default_rng(seed).normal(0, noise_w, len(frame))
    frame["power_ac"] = np.where(expected > 0, np.maximum(expected + noise, 0), 0)
    return frame, {
        "tilt": tilt,
        "azimuth": azimuth,
        "latitude": 35.0,
        "longitude": -5.0,
        "dc_capacity": 100_000,
        "ac_capacity": 90_000,
        "seed": seed,
    }


def coupled_inventory(*, seed=42, groups=4, choices=3, rows=96, noise=0.002):
    """Synthetic coupled template-selection problem with a known inventory total.

    Templates represent distinct block contributions with slightly different
    daily shapes. This is a controlled combinatorial surrogate, not validated
    multi-block PV plant inference. Dense QUBO size is groups*choices.
    """
    if groups < 1 or choices < 2 or rows < 10:
        raise ValueError("positive groups, at least two choices and ten rows required")
    rng = np.random.default_rng(seed)
    time = np.linspace(-1, 1, rows)
    columns, onehot, inventory = [], [], []
    for g in range(groups):
        members = []
        center = (g - (groups - 1) / 2) * 0.06
        for c in range(choices):
            members.append(len(columns))
            shape = np.maximum(np.cos((time - center) * np.pi / 2), 0) ** (1 + 0.12 * g)
            columns.append(shape * (1 + 0.12 * c) / groups)
            inventory.append(c + 1)
        onehot.append(tuple(members))
    a = np.column_stack(columns)
    truth = np.zeros(len(columns), dtype=np.int8)
    selected = rng.integers(0, choices, groups)
    for g, c in enumerate(selected):
        truth[g * choices + c] = 1
    y = a @ truth + rng.normal(0, noise, rows)
    inventory = np.asarray(inventory, float)
    problem = least_squares_qubo(
        a,
        y,
        weights=np.ones(rows) / rows,
        groups=onehot,
        penalty=2.0,
        equality=(inventory[None, :], [inventory @ truth]),
        equality_penalty=0.2,
    )
    return problem, truth, a, y
