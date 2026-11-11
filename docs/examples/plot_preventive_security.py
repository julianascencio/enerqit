"""
Can a cheap transfer survive a line outage?
===========================================

Ember's `10 November 2026 interconnection report
<https://ember-energy.org/latest-insights/turkiye-generated-500-million-in-exports-through-interconnections-in-20-months/>`_
examines historical electricity trade. It motivates checking usable transfer,
but this example is **not a model of Türkiye**, nor a revenue forecast.
All numerical network, demand and cost inputs are synthetic.

A planner chooses a fixed dispatch before knowing which specified line may fail.
We compare ordinary DC dispatch, a 70% rating-margin heuristic, and preventive
security-constrained LP. No corrective redispatch is allowed after the outage.

Install once, then run offline::

    python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
    python docs/examples/plot_preventive_security.py
    python -m enerqit.contingency_study

See :doc:`the full study </preventive_security>` for model scope and references.
"""

# %%
# 1. Reuse the packaged triangle and validate its MW, MW/radian and hour inputs.
# No resampling or fabricated observations: one synthetic constant-power hour.
import matplotlib.pyplot as plt

from enerqit.contingency_study import run_contingency_engineer
from enerqit.network_study import network_case

print(network_case())
# %%
# 2. Invoke the actual existing role with four registered EnerQit callbacks.
# The planner is scripted/offline, not a live LLM or quantum processor.
run = run_contingency_engineer()
print("Agent commit:", run["agent_revision"])
print("Role:", run["role"]["id"], "Mode:", run["mode"])
print("Trace:", [v["tool"] for v in run["trace"]])
print("Input hash:", run["numerical_fixture_sha256"])
b = run["reports"]["benchmark_methods"]
s = run["reports"]["assess_sensitivity"]
# %%
# 3. Audit identical injections after removing each line, with fresh DC solves.
# Base dispatch transfers 120 MW. Losing direct line 0-2 reroutes all 120 MW
# through the 40 MW edge: 80 MW overload. The 70% heuristic still overloads it.
names = ["Base DC", "70% margin", "Preventive LP"]
costs = [
    b["base"]["firm_energy_cost_eur"],
    b["margin_70_percent"]["firm_energy_cost_eur"],
    b["preventive"]["cost_eur"],
]
audits = [b["base_audit"], b["margin_audit"], b["preventive"]["audit"]]
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
axes[0].bar(names, costs)
axes[0].set(ylabel="Modeled generation cost (EUR/hour)", title="Security has an operating cost")
axes[1].bar(names, [a["worst_overload_mw"] for a in audits])
axes[1].set(
    ylabel="Worst selected-outage overload (MW)", title="A blanket margin is not a guarantee"
)
fig.tight_layout()
for name, cost, audit in zip(names, costs, audits):
    print(name, cost, audit["worst_overload_mw"], audit["secure_for_selected_outages"])
# %%
# 4. Independent reference: direct-line loss leaves a series path capped at
# 40 MW. Thus 110 MW local firm supply is necessary, costing 11,000 EUR/hour.
# A 40 MW transfer passes every remaining outage, proving attainability.
# Its 8,000 EUR premium over the base solution is not an outage probability,
# expected loss, insurance price or realized saving.
print("Handoff:", run["reports"]["prepare_handoff"])
# %%
# 5. Remove individual outage constraints to see which one binds. An empty
# set reproduces the base-case optimum; omitted outages are not certified safe.
rows = s["outage_ablations"]
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.bar([str(r["outages"]) for r in rows], [r["cost_eur"] for r in rows])
ax.set(
    xlabel="Included outage indices (base always included)",
    ylabel="Cost (EUR/hour)",
    title="Outage-set ablation",
)
fig.tight_layout()
# %%
# 6. Vary the bottleneck rating and assumed firm cost independently. These are
# uncertainty scenarios, not calibrated statistical confidence intervals.
for r in s["rating_sweep"]:
    print("Rating MW", r["rating_mw"], "secure cost EUR", r["cost_eur"])
for r in s["cost_sweep"]:
    print("Firm EUR/MWh", r["firm_eur_mwh"], "secure cost EUR", r["cost_eur"])
for r in s["size_scaling"]:
    print("Ring scaling:", r)
# %%
# 7. Next: obtain licensed topology, emergency ratings and contingency lists.
# Validate AC voltage, stability, generator outages and corrective response.
# Islands are explicitly rejected, not silently skipped. This remains a small
# lossless DC screening tool; no plant operation or quantum execution occurs.
plt.show()
