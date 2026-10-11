"""
Effective efficiency and thermal derating
=========================================

Use actual DC input for efficiency; independently estimated available power for
thermal limiting. These are different channels and must not be interchanged.
The small continuous fits use constrained classical methods; a QUBO is not needed.
"""

import matplotlib.pyplot as plt
import numpy as np

from enerqit.inverter import efficiency_curve, fit_efficiency
from enerqit.thermal import derating_cap, fit_derating

rng = np.random.default_rng(8)
dc = np.linspace(8000, 90_000, 150)
ac = dc * efficiency_curve(dc, 100_000, [0.004, 0.009, 0.012]) + rng.normal(0, 30, len(dc))
eff = fit_efficiency(dc, ac, rated_power=100_000)
temperature = np.linspace(30, 85, 150)
available = np.full(150, 120_000.0)
thermal_ac = derating_cap(temperature, 100_000, 58, 0.015) + rng.normal(0, 100, 150)
thermal = fit_derating(temperature, thermal_ac, available, rated_power=100_000)
print(eff.to_json())
print(thermal.to_json())
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
axes[0].plot(dc / 1000, ac / dc, ".", label="Synthetic observations")
axes[0].plot(
    dc / 1000, efficiency_curve(dc, 100_000, list(eff.parameters.values())), label="Fitted"
)
axes[0].set(xlabel="Actual DC input (kW)", ylabel="Efficiency", title="Effective field efficiency")
axes[1].plot(temperature, thermal_ac / 1000, ".")
axes[1].plot(temperature, derating_cap(temperature, 100_000, **thermal.parameters) / 1000)
axes[1].set(
    xlabel="Defined inverter temperature (°C)", ylabel="Power cap (kW)", title="Thermal envelope"
)
axes[0].legend()
fig.tight_layout()
