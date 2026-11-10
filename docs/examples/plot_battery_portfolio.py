"""
Battery portfolios: energy availability matters
================================================

Run the Quantum ML Engineer from ``energy-agents`` against EnerQit's reusable
storage methods. The offline fixture combines dated factual GB margin-notice
metadata with **entirely synthetic** battery offers and fees. This is an
availability-block study, not reconstructed GB dispatch or an outage estimate.

Install the optional agent from the repository root before running this file::

    python -m pip install -e '.[docs]'
    python -m pip install -r requirements/agent-study.txt
    python docs/examples/plot_battery_portfolio.py

For assumptions, equations, source selection and limitations, read
:doc:`the engineering study </battery_portfolio>`. The default planner follows a
scripted tool sequence: evidence, benchmark, sensitivity, handoff. It invokes
the actual Quantum ML Engineer role; it makes no LLM inference or API request.
"""

# %%
# 1. Load the case and execute the registered EnerQit tools through the agent.
# Numerical work remains in EnerQit; energy-agents supplies orchestration.
import matplotlib.pyplot as plt
import numpy as np

from enerqit.storage_study import battery_portfolio_case, run_battery_engineer

case = battery_portfolio_case()
run = run_battery_engineer(case)
assert run["success"]
benchmark = run["reports"]["benchmark_methods"]
sensitivity = run["reports"]["assess_sensitivity"]
print("Role:", run["role"]["id"], "| Mode:", run["mode"])
print("Stages:", [event["tool"] for event in run["trace"]])
print("Evidence: real dated margin-notice facts; optimization inputs: synthetic")
for event in case["evidence"]["events"]:
    print(event["published_at"], event["status"], event["indicated_margin_shortfall_mw"])

# %%
# 2. Derive sustained capacity from usable DC MWh, efficiency and AC limits.
# The target is deliberately a constructed 180 MW / 3 h block, not any observed
# notice level. Proportional output allocation satisfies the selected block.
capacities = benchmark["capacities"]
ids = [row["id"].replace("Fictional-", "") for row in capacities]
x = np.arange(len(ids))
fig, ax = plt.subplots(figsize=(10, 4.5), layout="constrained")
ax.bar(x - .2, [row["power_only_mw"] for row in capacities], .4,
       label="AC power/export limit", color="#93a5bc")
ax.bar(x + .2, [row["deliverable_mw"] for row in capacities], .4,
       label="Sustainable for 3 h", color="#167d9a")
ax.set(xticks=x, xticklabels=ids, ylabel="AC power (MW)", xlabel="Fictional battery offer",
       title="Synthetic offers: power ratings overstate 3-hour availability")
ax.legend(frameon=False)

# %%
# 3. Compare a power-only procurement rule with native physical optimization.
# Fixed availability fees are assumptions, not market prices or realized savings.
# Every solver candidate is checked against the original physical model.
for name in ("power_only_baseline", "native_milp"):
    result = benchmark[name]["physical"]
    print(name, "selected:", result["selected_ids"],
          "fee GBP:", result["reservation_cost_gbp"],
          "sustained MW:", round(result["sustained_capacity_mw"], 3),
          "shortfall MW:", round(result["shortfall_mw"], 3))
print("Encoded bits:", benchmark["qubo"]["variables"],
      "| Exact states:", benchmark["qubo"]["states"])
for row in benchmark["records"]:
    print(row["method"], "seed:", row["seed"], "encoded feasible:", row["encoded_feasible"],
          "physical feasible:", row["physical_feasible"],
          "gap to native optimum GBP:", row["native_cost_gap_gbp"])

labels = ["Power-only", "MILP", "Exact QUBO"] + [
    ("SA" if r["method"] == "simulated_annealing" else "bSB") + f" s{r['seed']}"
    for r in benchmark["records"][1:]]
physical = [benchmark[name]["physical"] for name in ("power_only_baseline", "native_milp")]
physical += [row["physical"] for row in benchmark["records"]]
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained")
colors = ["#b34b4b" if not p["feasible"] else "#167d9a" for p in physical]
axes[0].barh(labels, [p["reservation_cost_gbp"] / 1000 for p in physical], color=colors)
axes[0].set(xlabel="Synthetic block fee (£ thousand)", title="Cost alone hides infeasibility")
axes[0].invert_yaxis()
axes[1].barh(labels, [p["sustained_capacity_mw"] for p in physical], color=colors)
axes[1].axvline(case["target_mw"], color="#263848", linestyle="--", label="180 MW requirement")
axes[1].set(xlabel="Sustainable AC power for 3 h (MW)", title="Independent physical check")
axes[1].invert_yaxis()
axes[1].legend(frameon=False)

# %%
# 4. Re-optimize over duration, withheld SOC energy and conservative MW steps.
# Longer durations reduce deliverable capacity. Here 12 hours is infeasible even
# with all eight offers. Fees are kept fixed to isolate physical sensitivity.
fig, axes = plt.subplots(1, 3, figsize=(12, 4), layout="constrained")
for ax, key, field, xlabel in zip(axes, ["duration", "soc_buffer", "discretization"],
                                ["duration_hours", "withheld_soc_fraction", "step_mw"],
                                ["Block duration (h)", "Additional SOC buffer (fraction)",
                                 "Conservative capacity step (MW)"]):
    rows = sensitivity[key]
    ax.plot([r[field] for r in rows],
            [r["cost_gbp"] / 1000 if r["status"] == "optimal" else np.nan for r in rows],
            "o-", color="#167d9a")
    for row in rows:
        if row["status"] != "optimal":
            ax.annotate("infeasible", (row[field], 30), ha="right", color="#b34b4b")
    ax.set(xlabel=xlabel, ylabel="Minimum synthetic fee (£ thousand)")
    values = [r[field] for r in rows]
    margin = max((max(values) - min(values)) * .06, .005)
    ax.set_xlim(min(values) - margin, max(values) + margin)
    ax.grid(alpha=.2)
fig.suptitle("Physical and encoding sensitivity; fixed synthetic quotes")

# %%
# 5. Inspect the handoff. These small-instance results do not establish scaling
# benefit, business savings, quantum advantage, service compliance or field validity.
# The standalone CLI saves all evidence and timings as JSON::
#
#     python -m enerqit.storage_study --output results/battery-engineer.json
print("Recommended method:", run["reports"]["prepare_handoff"]["recommended_method"])
print("Required next evidence:", run["reports"]["prepare_handoff"]["next_evidence"])
print("No operational execution authorized:", not run["execution_authorized"])
plt.show()
