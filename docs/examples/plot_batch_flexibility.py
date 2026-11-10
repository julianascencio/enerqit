"""
Flexible demand without a rebound overload
==========================================

The IEA's `5 November 2026 review of Spain
<https://www.iea.org/news/accelerating-electrification-can-unlock-the-full-benefits-of-spains-renewables-leadership>`_
highlights electrification, grid modernisation and flexibility. Here an industrial
operator asks whether jobs can move into cheap hours **without creating a new
peak or missing their completion deadlines**.

All jobs, profiles, tariffs and grid limits below are synthetic. The news supplies
context, not calibration or measured market prices. This example calls the actual
Quantum ML Engineer from ``energy-agents`` through EnerQit-owned numerical tools.
The default planner is scripted and offline; no LLM API or quantum device is used.

From the repository root::

    python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
    python docs/examples/plot_batch_flexibility.py
    python -m enerqit.flexibility_study --output results/flexibility-engineer.json

See :doc:`the complete engineering study </batch_flexibility>` for equations,
source selection, baseline comparisons, validation and scope.
"""

# %%
# 1. Load the packaged fixture, validate its physical contract, and call the agent.
# It runs evidence inspection → benchmarking → sensitivity → handoff → finish.
# Dates and hashes for source facts remain separate from synthetic model inputs.
import matplotlib.pyplot as plt
import numpy as np

from enerqit.flexibility_study import flexibility_case, problem_from_case, run_flexibility_engineer

case = flexibility_case()
problem = problem_from_case(case)
run = run_flexibility_engineer(case)
benchmark = run["reports"]["benchmark_methods"]
sensitivity = run["reports"]["assess_sensitivity"]
print("Role:", run["role"]["id"], "| Mode:", run["mode"])
print("Agent revision:", benchmark["environment"]["agent_source_revision"])
print("Trace:", [step["tool"] for step in run["trace"]])
print("Case SHA256:", run["reports"]["inspect_evidence"]["case_sha256"])
print("Synthetic operational inputs; sourced news context only.")

# %%
# 2. Compare price-only and nominal-only planning against a shared schedule that
# respects both declared baseline-load scenarios. Every case processes 9 MWh of
# fixed work. No workload is silently dropped to make the peak look smaller.
solutions = {
    "Price only": benchmark["price_only"]["physical"],
    "Nominal only": benchmark["nominal_only"]["evaluated_on_all_scenarios"],
    "Both scenarios": benchmark["native_milp"]["physical"],
}
for label, result in solutions.items():
    print(label, "EUR:", result["energy_charge_eur"], "work MWh:", result["work_energy_mwh"],
          "max violation MW:", result["max_violation_mw"], "starts:", result["starts"])

hours = np.arange(problem.horizon) + 9  # Fixture starts at 09:00 UTC; slot starts.
colors = ["#bd574b", "#bd8d28", "#167d9a"]
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained", sharey=True)
for index, ax in enumerate(axes):
    scenario = problem.scenarios[index]
    ax.stairs(scenario.import_limit_mw, np.arange(7)+9, color="#263848", linestyle="--",
              linewidth=2, label="Grid import ceiling", baseline=None)
    for (label, result), color in zip(solutions.items(), colors):
        ax.stairs(result["scenarios"][index]["grid_import_mw"], np.arange(7)+9,
                  label=label, color=color, linewidth=2, baseline=None)
    ax.set(title=scenario.name.replace("_", " "), xlabel="UTC hour", ylabel="Site AC import (MW)",
           xticks=np.arange(9, 16), ylim=(0, 12))
    ax.grid(alpha=.2)
axes[0].legend(frameon=False, fontsize=9)
fig.suptitle("Synthetic site: cheap-hour clustering can violate the grid ceiling")

# %%
# 3. Inspect the winning schedule against release and completion boundaries.
# A batch runs contiguously with its given profile. These four illustrative jobs
# are not thermal/process models or validated factory equipment profiles.
selected = solutions["Both scenarios"]["starts"]
fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
for row, (job, start) in enumerate(zip(problem.jobs, selected)):
    ax.barh(row, job.deadline_slot-job.release_slot, left=9+job.release_slot,
            color="#e4e8ee", height=.65)
    ax.barh(row, len(job.profile_mw), left=9+start, color="#167d9a", height=.42)
    for k, power in enumerate(job.profile_mw):
        ax.text(9+start+k+.5, row, f"{power:g} MW", ha="center", va="center", color="white")
ax.set(yticks=range(len(problem.jobs)), yticklabels=[j.id for j in problem.jobs],
       xlabel="UTC hour; light bars show allowed windows", xticks=np.arange(9, 16),
       title="Robust native MILP: all four batches complete within their windows")
ax.invert_yaxis()

# %%
# 4. Compare native/exact references with every predeclared stochastic seed.
# Native enumeration checks 144 real schedules. Exact QUBO checks 65,536 encoded
# states. Feasible physical cost and penalized energy are separate quantities.
print("Native combinations:", benchmark["native_enumeration"]["combinations"],
      "| QUBO bits:", benchmark["qubo"]["variables"])
for row in benchmark["records"]:
    print(row["method"], "seed", row["seed"], "encoded feasible", row["encoded_feasible"],
          "physical feasible", row["physical_feasible"], "native gap EUR", row["native_cost_gap_eur"],
          "construction + solver seconds", round(row["total_s"], 5))

# %%
# 5. Stress assumptions before presenting an operational claim. More baseline
# load raises the required scheduling cost; a sufficiently tight deadline makes
# the work impossible. Coarse power discretization can exclude a cheaper schedule.
fig, axes = plt.subplots(1, 3, figsize=(12, 4.2), layout="constrained")
settings = [("baseline_margin", "extra_baseline_mw", "Extra baseline demand (MW)"),
            ("deadline", "batch_c_deadline_slot", "Batch C completion boundary (slot)"),
            ("discretization", "step_mw", "Conservative MW step")]
for ax, (key, field, label) in zip(axes, settings):
    rows = sensitivity[key]
    x = [r[field] for r in rows]
    cost = [r["physical"]["energy_charge_eur"]
            if r.get("physical") and r.get("encoded_feasible", True)
            and r["physical"]["feasible"] else np.nan for r in rows]
    ax.plot(x, cost, "o-", color="#167d9a")
    for value, price in zip(x, cost):
        if np.isnan(price):
            ax.annotate("infeasible", (value, 200), ha="center", color="#bd574b", fontsize=9)
    ax.set(xlabel=label, ylabel="Synthetic batch energy cost (EUR)", ylim=(0, 900))
    margin = max((max(x)-min(x))*.15, .05)
    ax.set_xlim(min(x)-margin, max(x)+margin)
    ax.grid(alpha=.2)
fig.suptitle("Sensitivity is deterministic; no confidence level is implied")

# %%
# 6. Repeated cohorts expose resource growth and imperfect heuristic outcomes.
# This is a small implementation benchmark, not evidence of general scaling
# superiority. Budgets are fixed by iterations/trajectories, not matched runtime.
fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
scaling = sensitivity["scaling"]
sizes = [r["jobs"] for r in scaling]
for index, name in enumerate(["SA", "bSB"]):
    gaps = [r["heuristics"][index]["native_cost_gap_eur"] for r in scaling]
    axes[0].plot(sizes, [np.nan if v is None else v for v in gaps], "o-", label=name)
    times = [r["heuristics"][index]["total_s"] for r in scaling]
    axes[1].plot(sizes, times, "o-", label=name)
axes[1].plot(sizes, [r["native_milp"]["construction_s"]+r["native_milp"]["solver_s"]
                    for r in scaling], "o-", label="Native MILP")
axes[0].set(xlabel="Jobs in replicated cohorts", ylabel="Gap to native optimum (EUR)",
            title="All returned candidates retained")
axes[1].set(xlabel="Jobs in replicated cohorts", ylabel="Construction + solver time (s)",
            yscale="log", title="Measured on this machine; unequal budgets")
for ax in axes:
    ax.set_xticks(sizes)
    ax.legend(frameon=False)
    ax.grid(alpha=.2)
print("Recommended method:", run["reports"]["prepare_handoff"]["recommended_method"])
print("Next evidence:", run["reports"]["prepare_handoff"]["next_evidence"])
plt.show()
