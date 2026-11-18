"""Causal recovery of otherwise-curtailed renewable energy, with AC/DC accounting."""

from collections.abc import Sequence

import numpy as np

from enerqit.storage import _finite


def recover_curtailment(
    renewable_mw: Sequence[float],
    export_limit_mw: Sequence[float],
    hours: Sequence[float],
    *,
    power_mw: float,
    energy_dc_mwh: float,
    charge_efficiency: float = 0.9,
    discharge_efficiency: float = 0.9,
) -> dict:
    """Replay surplus-only charging and headroom-only discharge from empty SOC.

    Parameters
    ----------
    renewable_mw, export_limit_mw : sequence of float
        Available AC renewable generation and permitted net AC export ceiling,
        in MW, for 1..100000 ordered, contiguous intervals. Both nonnegative.
    hours : sequence of float
        Positive duration of each interval in elapsed hours. Inputs must share
        identical ordering and lengths. No resampling or timezone inference.
    power_mw : float
        Symmetric AC battery charge/discharge rating in MW (0..1e6).
    energy_dc_mwh : float
        Usable DC battery energy capacity in MWh (0..1e9).
    charge_efficiency, discharge_efficiency : float
        Constant conversion efficiencies in [1e-6, 1].

    Returns
    -------
    dict
        AC power traces (MW), boundary DC state of charge (MWh, initial zero
        included), baseline export and curtailment, captured AC energy,
        recovered export, remaining curtailment, conversion loss, terminal DC
        energy and conservation residual (all aggregate energies in MWh).

    Notes
    -----
    Piecewise-constant sequential intervals; no grid charging, foresight, fees,
    initial free energy, self-discharge or terminal sale. Limits apply to net AC
    export, not a command prohibiting generation/charging. Do not use this model
    where the operator's curtailment instruction prohibits on-site charging.
    """
    g, limit, h = [np.asarray(v, float) for v in (renewable_mw, export_limit_mw, hours)]
    if (
        g.ndim != 1
        or not 1 <= len(g) <= 100000
        or limit.shape != g.shape
        or h.shape != g.shape
        or any(not np.isfinite(v).all() for v in (g, limit, h))
        or np.any(g < 0)
        or np.any(limit < 0)
        or np.any(h <= 0)
    ):
        raise ValueError("Matching finite generation/limits >=0 MW and durations >0 h required")
    _finite(power_mw, "power_mw", 0, 1e6)
    _finite(energy_dc_mwh, "energy_dc_mwh", 0, 1e9)
    _finite(charge_efficiency, "charge_efficiency", 1e-6, 1)
    _finite(discharge_efficiency, "discharge_efficiency", 1e-6, 1)
    direct = np.minimum(g, limit)
    surplus = g - direct
    headroom = limit - direct
    state = 0.0
    soc = [0.0]
    charge = []
    discharge = []
    for s, room, dt in zip(surplus, headroom, h):
        c = min(s, power_mw, max(0.0, energy_dc_mwh - state) / (charge_efficiency * dt))
        d = min(room, power_mw, state * discharge_efficiency / dt)
        state += c * charge_efficiency * dt - d * dt / discharge_efficiency
        charge.append(c)
        discharge.append(d)
        soc.append(state)
    c, d = np.array(charge), np.array(discharge)
    captured = float(c @ h)
    recovered = float(d @ h)
    losses = float((c * (1 - charge_efficiency) + d * (1 / discharge_efficiency - 1)) @ h)
    residual = captured - recovered - losses - state
    if abs(residual) > 1e-6 or min(soc) < -1e-7 or max(soc) > energy_dc_mwh + 1e-7:
        raise RuntimeError("Energy accounting audit failed")
    return {
        "charge_ac_mw": c.tolist(),
        "discharge_ac_mw": d.tolist(),
        "soc_dc_mwh": soc,
        "export_mw": (direct + d).tolist(),
        "baseline_export_mwh": float(direct @ h),
        "baseline_curtailment_mwh": float(surplus @ h),
        "captured_ac_mwh": captured,
        "recovered_export_mwh": recovered,
        "remaining_curtailment_mwh": float((surplus - c) @ h),
        "conversion_loss_mwh": losses,
        "terminal_dc_mwh": state,
        "balance_residual_mwh": residual,
    }
