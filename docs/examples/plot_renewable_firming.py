"""
Does wind complementarity reduce battery size?
===============================================

Ember's `Harnessing the winds
<https://ember-energy.org/latest-insights/harnessing-the-winds/>`_ (article dated
13 November 2026; listing dated 12 November) motivates examining chronological
wind/solar complementarity. This is a small synthetic mechanism test, **not** a
replication of the report's global costs or reliability estimates.

Three profiles deliver the same 6 MWh over four one-hour intervals to a constant
1 MW load: solar alone, a complementary mix, and a coincident mix. The planner
chooses minimum usable DC battery energy at a fixed 2 MW AC rating. No backup or
unserved load is allowed. The horizon repeats; starting energy must be restored.

Install once, then execute offline::

    python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
    python -m enerqit.firming_study
    python docs/examples/plot_renewable_firming.py

See :doc:`the full study </renewable_firming>` for equations and limits.
"""

# %%
# 1. The actual engineer role runs four registered EnerQit callbacks. Its planner
# is scripted/offline. No live LLM, quantum circuit or hardware execution occurs.
import matplotlib.pyplot as plt
import numpy as np

from enerqit.firming_study import run_firming_engineer

run = run_firming_engineer()
evidence = run["reports"]["inspect_evidence"]
print("Role:", run["role"]["id"], "Mode:", run["mode"])
print("Agent:", evidence["agent_revision"])
print("Trace:", [r["tool"] for r in run["trace"]])
print("Input hash:", run["fixture_sha256"])
# %%
# 2. Load the packaged synthetic profiles. Intervals are ordered, equal duration,
# with no implied calendar timestamps. Future observed profiles must align in UTC.
profiles = evidence["inputs"]["profiles"]
fig, ax = plt.subplots(figsize=(8, 3.5))
for name, values in profiles.items():
    ax.plot(range(4), values, marker="o", label=name)
ax.axhline(1, color="black", linestyle="--", label="Demand")
ax.set(
    xlabel="Synthetic interval",
    ylabel="AC power (MW)",
    title="Same renewable energy, different timing",
)
ax.legend(fontsize=8)
fig.tight_layout()
# %%
# 3. Compare no-storage shortfalls, a continuous LP lower bound, and a physical
# MILP with exclusive charge/discharge modes. Independently reconstruct each SOC
# trajectory and energy balance, instead of trusting the solver objective alone.
b = run["reports"]["benchmark_methods"]
for name, row in b.items():
    p = row["physical"]
    print(
        name,
        "no-storage shortfall MWh:",
        row["no_storage_shortfall_mwh"],
        "required DC MWh:",
        p["capacity_mwh"],
        "LP bound:",
        row["lp_lower_bound"]["capacity_mwh"],
        "feasible:",
        p["audit"]["feasible"],
        "solver seconds:",
        p["solver_s"],
    )
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
axes[0].bar(list(b), [row["physical"]["capacity_mwh"] for row in b.values()])
axes[0].set(
    ylabel="Minimum usable DC energy (MWh)", title="Coincident wind provides no timing benefit"
)
axes[0].tick_params(axis="x", rotation=15)
for name, row in b.items():
    axes[1].step(np.arange(5), row["physical"]["energy_mwh"], where="post", label=name)
axes[1].set(
    xlabel="Interval boundary",
    ylabel="Stored DC energy (MWh)",
    title="Cyclic boundary: no net free starting energy",
)
axes[1].legend(fontsize=8)
fig.tight_layout()
# %%
# 4. Analytic independent check: the solar case has two consecutive 1 MWh
# deficits across the cycle boundary, requiring 2/0.9 DC MWh. The complementary
# case needs 0.5/0.9 MWh. Both can replenish in the surplus intervals. A coincident
# profile needs the same battery as solar alone despite its different label.
print("Expected DC MWh:", 2 / 0.9, 0.5 / 0.9)
# %%
# 5. Connect sizing to a bounded business screen. At an ASSUMED 200,000 EUR per
# usable DC MWh, capacity difference implies a battery energy-component difference.
# This excludes wind/PV capex, inverter power, financing, degradation and replacement;
# it is not total project savings, a supplier quotation or annual revenue.
assumed_eur_per_mwh = 200000
for name, row in b.items():
    print(
        name,
        "illustrative energy-component EUR:",
        row["physical"]["capacity_mwh"] * assumed_eur_per_mwh,
    )
# %%
# 6. Test losses, power limits and a joint lull. When total generation is too low,
# extra battery energy cannot rescue the cycle: storage cannot create energy.
s = run["reports"]["assess_sensitivity"]
for section in ("efficiency", "power"):
    print(
        section,
        [
            (r.get("eta", r.get("power_mw")), r["status"], r.get("capacity_mwh"))
            for r in s[section]
        ],
    )
print("Joint lull:", s["lull"]["status"])
for row in s["scaling"]:
    print(
        "Intervals:",
        row["intervals"],
        "seconds:",
        row["solver_s"],
        "matrix bytes:",
        row["matrix_bytes"],
    )
# %%
# 7. Repeated profiles test computational growth, not weather diversity. A real
# decision needs licensed multi-year co-located weather and load, starting-state
# policy, reserves and lifecycle economics. Four synthetic hours cannot establish
# annual uptime, outage probability or replication of the source report.
print(run["reports"]["prepare_handoff"])
plt.show()
