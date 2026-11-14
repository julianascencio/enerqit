"""
Can outage dependence change a firm-capacity decision?
======================================================

The `ENTSO-E Winter Outlook release, 13 November 2026
<https://www.entsoe.eu/news/2026/11/13/entso-e-winter-outlook-2026-2027-europe-is-prepared-some-risks-remain-in-specific-areas/>`_
finds broadly favourable adequacy with local risks. This motivates testing how
capacity availability assumptions affect a planning decision. This example is
**not an ENTSO-E forecast**, regional calibration or prediction of blackouts.

All capacities, outage probabilities, demand, targets and offer fees below are
synthetic. They describe one constant-demand four-hour window, not a year.

Install once, then run offline::

    python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
    python -m enerqit.adequacy_study
    python docs/examples/plot_adequacy_risk.py

See :doc:`the full study </adequacy_risk>` for equations and limitations.
"""

# %%
# 1. Invoke the actual generic engineer role. Four host-registered tools inspect
# evidence, benchmark risk, assess sensitivity and prepare a handoff. This is
# scripted offline orchestration; no live LLM, quantum device or plant command.
import matplotlib.pyplot as plt

from enerqit.adequacy import CapacityUnit, capacity_states, window_risk
from enerqit.adequacy_study import run_adequacy_engineer

run = run_adequacy_engineer()
print("Role:", run["role"]["id"], "mode:", run["mode"])
print("Trace:", [r["tool"] for r in run["trace"]])
print("Agent revision:", run["reports"]["inspect_evidence"]["agent_revision"])
print("Installed source:", run["agent_install"])
print("Fixture SHA256:", run["fixture_sha256"])
b = run["reports"]["benchmark_methods"]
# %%
# 2. Separate conditional and marginal outage probabilities. Each 60 MW unit has
# conditional outage probability 0.1 when the common event is absent. A common
# outage with probability 0.1 disables BOTH. Each marginal outage is therefore
# 0.1 + 0.9*0.1 = 0.19. The independent comparator preserves this same marginal.
# Renewable/weather contributions are not inferred from nameplate capacity.
states = capacity_states((CapacityUnit(60, 0.1),) * 2, 0.1)
print("Explicit states:", states)
print("Correlated:", b["correlated"])
print("Matched independent:", b["matched_marginal_independence"])
# %%
# 3. Compare nameplate, mean-capacity and full probability-weighted estimates.
# The mean-capacity screen loses the tail of the distribution. Neither it nor
# the nameplate screen is an adequacy probability model.
names = ["Nameplate", "Mean capacity", "Independent", "Common outage"]
values = [
    b["nameplate_shortfall_mwh"],
    b["mean_capacity_shortfall_mwh"],
    b["matched_marginal_independence"]["eens_mwh"],
    b["correlated"]["eens_mwh"],
]
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.bar(names, values)
ax.set(
    ylabel="Four-hour shortfall estimate / EENS (MWh)",
    title="Equal mean capacity does not imply equal tail risk",
)
fig.tight_layout()
# %%
# 4. Independent hand calculation. Available capacity probabilities are
# 120 MW: 0.729; 60 MW: 0.162; 0 MW: 0.109. With 100 MW demand,
# EENS = 4*(0.162*40 + 0.109*100) = 69.52 MWh. LOLE = 4*0.271 hours.
# Common outages can raise severity while reducing shortage probability compared
# with independence. Do not assume that every risk metric moves together.
print("Analytic EENS:", 4 * (0.162 * 40 + 0.109 * 100))
# %%
# 5. Enumerate hypothetical guaranteed-capacity offers. Target EENS <= 20 MWh
# is an authored engineering criterion, not a regulatory standard. EUR 100/MW
# is a fixed fee for this entire window; it is not an hourly tariff or market bid.
fig, ax = plt.subplots(figsize=(8, 3.6))
for key, label in [
    ("independent_procurement", "Independent"),
    ("correlated_procurement", "Common outage"),
]:
    rows = b[key]["offers"]
    ax.plot([r["firm_mw"] for r in rows], [r["eens_mwh"] for r in rows], marker="o", label=label)
    print(label, "selected:", b[key]["selected"])
ax.axhline(20, color="black", linestyle="--", label="Assumed EENS target")
ax.set(
    xlabel="Guaranteed capacity outside outage model (MW)",
    ylabel="Window EENS (MWh)",
    title="Dependence changes the qualifying offer",
)
ax.legend()
fig.tight_layout()
# %%
# 6. Re-evaluate the independence-selected offer against the correlated model.
# Its 40 MW choice misses the target: 26.16 MWh. The 60 MW choice meets it at
# 17.44 MWh. The extra EUR 2,000 is a hypothetical procurement premium, not saved
# revenue or monetized outage damage. Guaranteed reserve availability is itself
# an assumption needing evidence.
chosen = b["independent_procurement"]["selected"]["firm_mw"]
print("Independent choice under common outage:", window_risk(states, 100, hours=4, firm_mw=chosen))
# %%
# 7. Sensitivity varies common-event probability and demand without inventing
# confidence intervals. Scaling enumerates 2/8/12/16-unit fleets, exponentially.
# Full state enumeration avoids sampling error, but not uncertainty in the inputs.
s = run["reports"]["assess_sensitivity"]
print("Common event sensitivity:", s["common_probability"])
print("Demand sensitivity:", s["demand"])
print("Resource scaling:", s["scaling"])
print("Next action:", run["reports"]["prepare_handoff"]["next_action"])
# %%
# This screen excludes storage energy, hydro constraints, imports, repairs,
# chronological weather and network flows. Do not multiply these window metrics
# into annual LOLE/EENS. Obtain licensed joint outage and chronological data before
# using the method in a procurement or operational decision.
plt.show()
