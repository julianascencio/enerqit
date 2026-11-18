"""
When battery reserve runs out of energy
=======================================

The `ENTSO-E 13 November 2026 winter outlook
<https://www.entsoe.eu/news/2026/11/13/entso-e-winter-outlook-2026-2027-europe-is-prepared-some-risks-remain-in-specific-areas/>`_
reports growing storage alongside local adequacy risks. This advances the
14 November study's storage-energy gap, not a new observed outage. All numerical
inputs are synthetic; no European system is calibrated here.

Run offline after installation::

    python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
    python -m enerqit.reserve_study
    python docs/examples/plot_reserve_depletion.py

See :doc:`method and limits </reserve_depletion>`.
"""

# %%
# 1. Execute the actual engineer role with four trusted host tools.
import matplotlib.pyplot as plt

from enerqit.reserve_study import run_reserve_study

r = run_reserve_study()
print(r["role"]["id"], r["trace"], r["agent_install"])
print("Fixture SHA256", r["fixture_sha256"])
# %%
# 2. Two equally likely four-hour paths have either two or four hours of 50 MW
# deficit. Both offers are 50 MW; their energy differs: 100 versus 200 MWh DC.
# Ideal efficiency and full initial SOC are explicit engineering assumptions.
print(r["reports"]["inspect_evidence"])
# %%
# 3. Reuse BatteryOffer health, SOC, reserve and export physics. Carry energy
# forward across intervals, with no recharge and no implicit SOC reset.
b = r["reports"]["benchmark_methods"]
fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
for row in b["offers"]:
    run = row["scenarios"][1]
    axes[0].step(range(5), run["remaining_ac_mwh"], where="post", label=row["id"])
    axes[1].step(range(4), run["dispatch_mw"], where="post", label=row["id"])
    print(row["id"], "EENS", row["eens_mwh"], "power-only", row["power_only_eens_mwh"])
axes[0].set(xlabel="Elapsed hours", ylabel="Remaining deliverable AC MWh")
axes[1].set(xlabel="Interval start (elapsed hours)", ylabel="Dispatch MW")
for ax in axes:
    ax.legend()
fig.tight_layout()
# %%
# 4. Independent calculation: short reserve leaves 100 MWh in the long event,
# weighted .5 -> 50 MWh EENS. Long reserve leaves zero. The power-only baseline
# incorrectly assigns zero to both. The assumed limit is 20 MWh per window.
print("Selected", b["selected"]["id"], "fee GBP", b["selected"]["fee_gbp"])
# %%
# 5. Initial-SOC sensitivity and O(T) replay scaling expose dependence on starting
# inventory and horizon. Results do not establish annual reliability or LOLE.
print(r["reports"]["assess_sensitivity"])
# %%
# 6. GBP 1,800 versus 1,000 is hypothetical whole-service expenditure, not energy
# revenue or realized savings. Greedy is optimal only for total unserved energy
# with one battery, constant efficiency, no recharge and equal value per MWh.
print(r["reports"]["prepare_handoff"])
plt.show()
