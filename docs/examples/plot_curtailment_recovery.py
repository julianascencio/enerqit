"""
Captured curtailment is not recovered export
============================================

Wood Mackenzie's `16 November 2026 analysis
<https://www.woodmac.com/press-releases/spains-renewable-sector-has-lost-140-million-to-grid-constraints-as-curtailment-remains-elevated-since-april-2025-blackout/>`_
reports persistent Spanish grid constraints using 2026 year-to-date evidence.
This motivates a generic plant-level recovery ledger; no national claim is
reproduced or used to calibrate the synthetic inputs below.

Run offline after installation::

    python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
    python -m enerqit.curtailment_study
    python docs/examples/plot_curtailment_recovery.py

See :doc:`method and limits </curtailment_recovery>`.
"""

# %%
# 1. Run the current engineer role's four registered tools, with an offline
# scripted planner. No model-generated code, trading or plant commands execute.
import matplotlib.pyplot as plt

from enerqit.curtailment_study import run_curtailment_study

r = run_curtailment_study()
print(r["role"]["id"], r["trace"], r["agent_install"])
print("Fixture SHA256", r["fixture_sha256"])
# %%
# The evidence report records five dated candidates and the selected source hash.
# 2. Six sequential one-hour intervals: 50 MW renewable output for two hours,
# then zero. A 30 MW export ceiling leaves 40 MWh otherwise curtailed. Charging
# is explicitly assumed permissible behind the export ceiling.
print(r["reports"]["inspect_evidence"]["inputs"])
rows = r["reports"]["benchmark_methods"]["capacity_cases"]
# %%
# 3. Reusable causal replay charges only surplus and discharges only into spare
# export headroom. Initial energy is zero; there is no grid charging or free SOC.
a = rows["40"]
fig, ax = plt.subplots(figsize=(8, 3.5))
ax.stairs(a["charge_ac_mw"], range(7), label="Charge AC MW")
ax.stairs(a["discharge_ac_mw"], range(7), label="Recovered export MW")
ax.set(xlabel="Elapsed hours", ylabel="MW")
ax.legend()
fig.tight_layout()
# %%
# 4. Independent accounting: 40 MWh charged * .9 * .9 = 32.4 MWh exported.
# The remaining 7.6 MWh is conversion loss. A capture-only valuation would
# overstate recovered energy. With no later headroom, none is recovered at all.
print("40 MWh battery:", a)
print("No later headroom:", r["reports"]["assess_sensitivity"]["no_later_headroom"])
# %%
# 5. Capacity sensitivity compares no battery, 20, 40 and 80 MWh DC. The larger
# battery does not create additional surplus. At an assumed flat EUR 50/MWh,
# 32.4 MWh is EUR 1,620 gross export value before costs, not realized savings.
print(r["reports"]["benchmark_methods"])
# %%
# 6. Inspect efficiency sensitivity and replay timing. Independent tests compare
# total recovery with a separate horizon LP; no quantum algorithm is necessary.
print(r["reports"]["assess_sensitivity"]["scaling"])
print(r["reports"]["prepare_handoff"])
plt.show()
