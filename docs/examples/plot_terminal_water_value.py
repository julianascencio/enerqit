"""
Avoiding end-of-horizon reservoir depletion
================================================

1. Evidence and decision
----------------------------
NVE's `18 November 2026 report
<https://www.nve.no/media/20550/2026_46_kraftsituasjonen.pdf>`_ covers 9-15 November.
It discusses water use responding to prices and future expectations. This is a
five-day-old source backing an unresolved repository problem, not fresh news or
plant calibration. A reservoir operator must compare selling water now with its
assumed value after the scheduling horizon. The existing terminal floor remains
available; an optional concave value curve adds an economic decision.

2. Offline preparation
---------------------------
Every numeric input and terminal value is synthetic, MIT-licensed. The fixture
uses three consecutive UTC hours, AC MWh, usable m3 and EUR. No resampling or
provider data is used. Generation connectors in EDI cannot determine future water
value; their contracts were inspected at the recorded commit, with no reuse.

Run from the PR branch::

    python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
    python -m enerqit.water_value_study
    python docs/examples/plot_terminal_water_value.py
"""
import matplotlib.pyplot as plt

from enerqit.water_value_study import run_water_value_study

# %%
# 3. Existing agent and reusable API
# -------------------------------------
# run_quantum_research_study executes four registered tools using its scripted
# planner. The numerical implementation extends dispatch_reservoir with
# TerminalWaterValue, preserving the default cash-only objective. No new role
# or agent adapter is needed. Success is execution evidence, not scientific approval.
r = run_water_value_study()
print('Agent install:', r['agent_install'])
print('Actual tool trace:', r['trace'])
b = r['reports']['benchmark_methods']

# %%
# 4. Same valuation for all policies
# --------------------------------------
# Scores must use one curve for every policy, including the cash-only baseline.
# Otherwise a larger objective could simply reflect different accounting.
# The assumed curve values the first 40000 m3 at EUR0.03/m3, then EUR0.005/m3.
# The independent tests enumerate physical release/bypass schedules for tiny
# integer cases, including the concave valuation, and test legacy behavior.
for name, row in b.items():
    print(name, 'cash EUR', row['gross_value_eur'], 'terminal m3', row['reservoir_m3'][-1],
          'common score EUR', row['common_score_eur'])
fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
for name, row in b.items():
    axes[0].plot(range(4), row['reservoir_m3'], marker='o', label=name)
axes[0].set(xlabel='Elapsed hours', ylabel='Usable water (m³)', title='Synthetic release policies')
axes[0].legend()
names = list(b)
cash = [b[n]['gross_value_eur'] for n in names]
book = [b[n]['common_valuation_eur'] for n in names]
axes[1].bar(names, cash, label='Gross energy value')
axes[1].bar(names, book, bottom=cash, label='Assumed terminal valuation')
axes[1].set(ylabel='Scenario EUR, not realized revenue', title='Common valuation comparison')
axes[1].legend()

# %%
# 5. Sensitivity and economic interpretation
# --------------------------------------------
# Cash-only drains the reservoir and earns EUR1373.40. The curve-aware policy
# earns EUR1103.625 and retains 40000 m3 valued at EUR1200: common score EUR2303.625.
# A 60000 m3 hard floor gives EUR613.125 cash plus EUR1300 terminal valuation.
# The score improvement is conditional on the curve, not realized profit. A zero
# value curve recovers the cash-only model. Scale/inflow scenarios are assumptions,
# not calibrated confidence bounds. Classical LP suffices; no quantum execution.
print('Sensitivity:', r['reports']['assess_sensitivity'])

# %%
# 6. Next practical action and limits
# --------------------------------------
# Fit continuation values only on information available before the decision,
# freeze them, and validate on untouched later prices/inflows. This example does
# not fit a curve, perform rolling-horizon ML, or claim forecast skill. Constant
# head, perfect foresight within the window and unlimited bypass remain limits.
# Review hydraulic constraints, terminal discounting and economics independently.
plt.show()
