"""
Recover IV curves from sweeps and MPPT evidence
===============================================

The sweep estimator fits five parameters. The operational estimator fits two
parameters with the other values fixed. Neither produces a certified OEM curve.
"""

from dataclasses import replace

import matplotlib.pyplot as plt
import numpy as np

from enerqit.ivtools import ModuleParameters, fit_iv, fit_mpp, iv_current, operating_points
from enerqit.topology import fit_string_counts

truth = ModuleParameters(photocurrent=9.1, resistance_series=0.42)
v = np.tile(np.linspace(0, 38, 60), 3)
g, t = np.repeat([400, 750, 1000], 60), np.repeat([15, 35, 50], 60)
current = iv_current(v, g, t, truth)
sweep_fit = fit_iv(v, current, g, t, initial=replace(truth, resistance_series=0.3))
g_mpp, t_mpp = np.linspace(250, 1000, 40), np.linspace(20, 55, 40)
mpp = operating_points(g_mpp, t_mpp, truth)
operational_fit = fit_mpp(mpp["v_mp"], mpp["i_mp"], g_mpp, t_mpp)
print("Sweep fit", sweep_fit.to_json())
print("Operational fit", operational_fit.to_json())
counts = fit_string_counts(20 * mpp["v_mp"], 6 * mpp["i_mp"], g_mpp, t_mpp, module=truth)
print("Conditional topology", counts.to_json())
fitted = ModuleParameters(**operational_fit.parameters)
voltage = np.linspace(0, 38, 200)
fig, ax = plt.subplots(figsize=(7, 4))
for irradiance in (400, 750, 1000):
    ax.plot(voltage, iv_current(voltage, irradiance, 25, truth), label=f"Truth {irradiance} W/m²")
    ax.plot(voltage[::8], iv_current(voltage[::8], irradiance, 25, fitted), "k.")
ax.set(
    xlabel="Module voltage (V)",
    ylabel="Current (A)",
    ylim=(0, 10),
    title="Conditional IV reconstruction; black points are the MPPT-derived model",
)
ax.legend()
fig.tight_layout()
