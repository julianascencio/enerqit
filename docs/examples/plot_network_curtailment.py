"""
Which grid upgrade actually reduces curtailment?
================================================

Ember's `grid modernisation guide, published 5 November 2026
<https://ember-energy.org/latest-insights/building-a-grid-for-the-age-of-power/>`_
motivates screening grid upgrades. This 10 November study advances the existing
network-model backlog; the source is five days old, not a new event today.

A network planner must decide which line's rating to increase. Does ignoring
passive-network physics change the answer? All network and cost inputs are
**synthetic**, not measurements inferred from the news. The example uses a
classical linear program because this decision is continuous and convex.

Install once (network required), then reproduce completely offline::

    python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
    python docs/examples/plot_network_curtailment.py
    python -m enerqit.network_study --output results/network-engineer.json

See :doc:`the engineering study </network_curtailment>` for equations, dates,
source selection, independent references and practical limits.
"""

# %%
# 1. Acquire the bundled synthetic snapshot and validate units and connectivity.
# Each bus has demand, renewable availability and firm capacity in MW. Each line
# has susceptance in MW/radian and a symmetric rating in MW. One constant interval
# lasts one hour; it is an abstract scenario, not a dated meter reading.
import matplotlib.pyplot as plt
import numpy as np

from enerqit.network_study import network_case, run_network_engineer

case = network_case()
print(case)

# %%
# 2. Invoke the existing Quantum ML Engineer. Its bounded registered tools call
# EnerQit methods. This is the actual scripted offline role runner, not a live
# LLM reasoning session, a QPU job or a script merely relabeled as an agent.
run = run_network_engineer()
print("Role:", run["role"]["id"], "| Mode:", run["mode"])
print("Agent commit:", run["agent_revision"])
print("Trace:", [step["tool"] for step in run["trace"]])
print("Numerical input SHA256:", run["input_sha256"])
print("Evidence fixture SHA256:", run["evidence_sha256"])
bench = run["reports"]["benchmark_methods"]
sensitivity = run["reports"]["assess_sensitivity"]

# %%
# 3. Benchmark three model assumptions with the same cost objective.
# Copperplate ignores lines. Transport respects controllable edge capacities but
# omits Kirchhoff voltage constraints. DC imposes nodal and angle/flow equations.
# Re-solving angles from each dispatch exposes infeasible optimistic baselines.
models = ["copperplate", "transport", "dc"]
costs = [bench[m]["physical"]["firm_energy_cost_eur"] for m in models]
curtailment = [bench[m]["physical"]["curtailed_mwh"] for m in models]
for m in models:
    p = bench[m]["physical"]
    print(
        m,
        "cost EUR:",
        p["firm_energy_cost_eur"],
        "curtailed MWh:",
        p["curtailed_mwh"],
        "physical overload MW:",
        p["max_overload_mw"],
        "DC feasible:",
        p["dc_feasible"],
        "LP runtime s:",
        bench[m]["solver_s"],
    )
fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
axes[0].bar(models, costs, color=["#cc7777", "#ddaa66", "#357da0"])
axes[0].set(
    ylabel="Firm energy cost (EUR / modeled hour)", title="Optimism is not feasible savings"
)
axes[1].bar(models, curtailment, color=["#cc7777", "#ddaa66", "#357da0"])
axes[1].set(
    ylabel="Curtailed renewable energy (MWh)", title="Same inputs, different network models"
)
fig.tight_layout()

# %%
# 4. Check the physical bottleneck. Equal reactances in the triangle split the
# renewable transfer R into R/3 via bus 1 and 2R/3 directly to bus 2. Therefore
# the 40 MW line caps renewable dispatch at 120 MW. This is an analytic reference
# independent of the LP. Its optimal cost is (150-120)*100 = 3000 EUR.
fig, ax = plt.subplots(figsize=(8, 3.6))
x = np.arange(3)
for i, m in enumerate(models):
    ax.bar(x + (i - 1) * 0.23, np.abs(bench[m]["physical"]["line_flows_mw"]), 0.23, label=m)
ax.scatter(
    x, [line.limit_mw for line in case.lines], marker="_", s=400, color="black", label="Rating"
)
ax.set(
    xticks=x,
    xticklabels=["0–1", "0–2", "1–2"],
    ylabel="Absolute physical flow (MW)",
    title="Independent DC audit of every candidate",
)
ax.legend(ncols=4, fontsize=8)
fig.tight_layout()

# %%
# 5. Compare bounded interventions: raise each rating by 10 MW, holding reactance
# fixed. This could represent a rating change; it is not a model of a new line.
# Only line 0–1 removes this bottleneck. No capital cost or annual extrapolation
# is supplied, so the result cannot establish project NPV or realized revenue.
upgrades = sensitivity["upgrades"]
benefits = [costs[-1] - r["physical"]["firm_energy_cost_eur"] for r in upgrades]
fig, ax = plt.subplots(figsize=(7, 3.5))
ax.bar(["0–1", "0–2", "1–2"], benefits, color="#357da0")
ax.set(
    xlabel="Line receiving +10 MW rating",
    ylabel="Avoided modeled cost (EUR / hour)",
    title="Upgrade the binding constraint",
)
fig.tight_layout()
print("Upgrade benefits EUR:", benefits)

# %%
# 6. Inspect uncertainty and resource limits without invented probabilities.
# Renewable availability and firm marginal cost are varied independently.
# Physical scaling preserves angles; radial size tests use 5, 20 and 100 buses.
# These single-run timings are diagnostic, not statistically significant speedups.
for row in sensitivity["renewable_availability"]:
    print("Available MW:", row["available_mw"], "curtailed MWh:", row["physical"]["curtailed_mwh"])
for row in sensitivity["firm_cost_range"]:
    print(
        "Firm EUR/MWh:", row["cost_eur_mwh"], "cost EUR:", row["physical"]["firm_energy_cost_eur"]
    )
for row in sensitivity["size_scaling"]:
    print("Resources:", row["resources"], "solver s:", row["solver_s"])
print("Next action:", run["reports"]["prepare_handoff"]["next_evidence"])

# %%
# The implementation resolves feasibility and modeled upgrade value for these
# supplied assumptions. A deployment needs licensed real topology and hourly
# data, AC power-flow/voltage checks, contingencies, outages and investment costs.
# No quantum-inspired, hybrid or hardware performance is claimed for this LP.
plt.show()
