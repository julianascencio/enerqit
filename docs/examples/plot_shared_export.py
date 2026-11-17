"""
Coordinating co-located stored-energy exports
=============================================

EnBW's `Forbach announcement
<https://www.enbw.com/press/green-light-for-enbw-battery-storage-facility-in-forbach.html>`_
was reported on 17 November 2026. Its English and German pages disagree on
battery power (41 versus 46 MW); the primary publication date was not verified.
This generic study does not use either rating or invent a site connection limit.
All numerical inputs are synthetic. See :doc:`method </shared_export>`.

Run offline after installation::

    python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
    python -m enerqit.shared_export_study
    python docs/examples/plot_shared_export.py
"""

# %%
# 1. Execute four registered tools using the actual generic engineer role.
import matplotlib.pyplot as plt
import numpy as np

from enerqit.shared_export_study import run_shared_export_study

r = run_shared_export_study()
print(r["role"]["id"], r["trace"], r["agent_install"])
print("Input SHA256:", r["fixture_sha256"])
# %%
# 2. Two generic resources each offer 50 MW and respectively 50/100 MWh already
# deliverable on the AC side. No efficiency or hydro-head conversion is implied.
# The shared connection permits 50 MW across six consecutive one-hour intervals.
print(r["reports"]["inspect_evidence"]["inputs"])
b = r["reports"]["benchmark_methods"]
# %%
# 3. Independent optimization requests 100 MW at the highest-price hour,
# exceeding the connection by 50 MW. Its EUR 14,500 value is physically infeasible.
# Proportional clipping is feasible but cannot reschedule withheld energy.
print("Independent overload MW:", b["independent_overload_mw"])
print("Requested value:", b["independent_requested"]["gross_value_eur"])
# %%
# 4. Joint classical LP reallocates energy to the next best available interval.
# Independent hand bound: three 50 MWh exports at EUR 100, 90 and 60 per MWh
# yield EUR 12,500. The native LP attains this feasible upper bound.
fig, ax = plt.subplots(figsize=(8, 3.8))
ax.stairs(b["independent_requested"]["export_mw"], range(7), label="Independent request")
ax.stairs(np.array(b["clipped_dispatch_mw"]).sum(axis=0), range(7), label="Clipped baseline")
ax.stairs(b["coordinated"]["export_mw"], range(7), label="Coordinated")
ax.axhline(50, color="black", linestyle="--", label="Connection limit")
ax.set(xlabel="Elapsed hours", ylabel="Export MW")
ax.legend()
fig.tight_layout()
# %%
# 5. EUR 12,500 coordinated versus EUR 9,500 clipped is a EUR 3,000 gross
# scenario difference, before acquisition, charging, degradation, fees or losses.
# It is not realized profit or the economic value of Forbach's actual assets.
print("Coordinated:", b["coordinated"]["gross_value_eur"])
print("Clipped:", b["clipped_gross_value_eur"])
print("Difference:", b["coordination_value_eur"])
# %%
# 6. Connection/energy sensitivities and 6/24/168 interval scaling are recorded.
# Known future prices make this a perfect-price scheduling bound. No forecasts
# are trained, no bids submitted and no equipment controlled.
print(r["reports"]["assess_sensitivity"])
print(r["reports"]["prepare_handoff"])
plt.show()
