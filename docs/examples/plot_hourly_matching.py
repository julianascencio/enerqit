"""
Total energy is not simultaneous renewable matching
========================================================

The Climate Council's `19 November 2026 report release
<https://www.climatecouncil.org.au/resources/data-centres-that-could-rival-our-dirtiest-coal-power-stations/>`_
raises the demand-growth and renewable-procurement question. Its projections are
not calibration inputs and its policy recommendations are not enacted rules.
This example compares two procurement objectives on authored synthetic profiles.

Run offline after installing dependencies::

    python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
    python -m enerqit.matching_study
    python docs/examples/plot_hourly_matching.py

See :doc:`/hourly_matching` for assumptions and next steps.
"""

# %%
# 1. Invoke the current engineer's four registered tools with a scripted planner.
# No remote LLM, credentials or market execution are needed.
import matplotlib.pyplot as plt

from enerqit.matching_study import run_matching_study

r = run_matching_study()
print(r["role"]["id"], r["trace"], r["agent_install"], r["fixture_sha256"])
# %%
# 2. Inspect aligned profiles: solar-like [1,0], wind-like [.5,.5], load [1,1].
# Profiles are MW/MW; two elapsed one-hour intervals. No missing-data imputation.
print(r["reports"]["inspect_evidence"])
b = r["reports"]["benchmark_methods"]
# %%
# 3. Total-energy procurement buys 2 MW solar-like capacity for EUR1000, yet
# only half the load is matched simultaneously. Excess cannot serve the dark hour.
print("Total-energy baseline", b["total_energy"])
# %%
# 4. Temporal matching buys 2 MW wind-like capacity for EUR3000. This is a
# horizon contract-cost premium, not a savings claim or an annual tariff.
print("Interval-aware procurement", b["interval"])
fig, ax = plt.subplots(figsize=(8, 3.5))
ax.stairs([1, 1], range(3), label="Demand", linestyle="--", color="black")
for name in ["total_energy", "interval"]:
    ax.stairs(b[name]["generation_mw"], range(3), label=name)
ax.set(xlabel="Synthetic elapsed hours", ylabel="MW")
ax.legend()
fig.tight_layout()
# %%
# 5. The 75% matching target costs EUR1750 with a mixed portfolio. Vary targets,
# wind contract costs and horizon size; these are sensitivities, not confidence bounds.
print(r["reports"]["assess_sensitivity"])
# %%
# 6. Independent tests check the analytic cost frontier and enumerate a tiny
# capacity grid. No quantum method is warranted for this continuous LP.
print(r["reports"]["prepare_handoff"])
plt.show()
