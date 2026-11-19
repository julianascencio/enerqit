"""
Capacity is not ramp deliverability
========================================

NESO's `18 November 2026 status report
<https://www.neso.energy/document/390381/download>`_ provides wind forecasts and
system-risk context, not evidence of a realized shortage. This synthetic study
asks whether an online 40 MW resource can meet a 0/40/40 MW residual-demand path.
No NESO forecast values calibrate these inputs. See :doc:`/ramp_deliverability`.

Run after installation::

    python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
    python -m enerqit.ramping_study
    python docs/examples/plot_ramp_deliverability.py
"""

# %%
# 1. Execute the existing engineer's four registered callbacks, with the scripted
# planner. Numerical methods are in EnerQit; no remote model or equipment call.
import matplotlib.pyplot as plt

from enerqit.ramping_study import run_ramping_study

r = run_ramping_study()
print(r["role"]["id"], r["trace"], r["fixture_sha256"])
# %%
# 2. Inspect authored MIT data and source/agent provenance. Energy durations and
# transition budgets are separate: this is discrete setpoint screening, not a
# continuous ramp waveform or forecast-training study.
print(r["reports"]["inspect_evidence"])
# %%
# 3. Compare capacity-only, causal tracking and perfect-foresight sparse LP.
# The baseline has enough capacity but causal tracking leaves 20 MWh unserved.
b = r["reports"]["benchmark_methods"]
print(b)
fig, ax = plt.subplots(figsize=(8, 3.5))
for name in ["capacity_only", "causal", "optimized"]:
    ax.stairs(b[name]["dispatch_mw"], range(4), label=name)
ax.set(xlabel="Synthetic elapsed hours", ylabel="Dispatch MW")
ax.legend()
fig.tight_layout()
# %%
# 4. Pre-positioning costs EUR 5,000, including 20 MWh spilled early. Causal
# tracking costs EUR 23,000 including an assumed EUR 1,000/MWh shortage penalty.
# EUR 18,000 is an avoided model penalty/cost, not revenue or realized savings.
print(
    "Scenario objective reduction EUR",
    b["causal"]["objective_eur"] - b["optimized"]["objective_eur"],
)
# %%
# 5. Vary ramp rate and shortage penalty. A low penalty may rationally leave
# demand unserved in the objective; optimization is not dispatch authorization.
print(r["reports"]["assess_sensitivity"])
# %%
# 6. Independent tests enumerate all tiny feasible dispatch paths. This linear
# model does not warrant QUBO discretization or a quantum advantage claim.
print(r["reports"]["prepare_handoff"])
plt.show()
