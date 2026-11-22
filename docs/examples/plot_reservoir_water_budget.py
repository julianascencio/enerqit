"""
Reservoir water has timing and retention constraints
========================================================

1. Evidence and decision
----------------------------
NVE's `week 46 report <https://www.nve.no/media/20550/2026_46_kraftsituasjonen.pdf>`_
was published 18 November 2026 and covers 9-15 November. This four-day-old
primary evidence was selected after extending the news search to seven days.
It motivates water-budget allocation, not a calibrated Norwegian plant model.
An operator chooses turbine and bypass releases to maximize gross scenario
energy value while preserving downstream minimum release and terminal water.

2. Offline inputs and preprocessing
--------------------------------------
All numeric inputs are authored synthetic MIT data: three contiguous UTC hours,
cubic metres, flows in m3/s, head in m, prices in EUR/MWh. No measured generation
or national reservoir percentage is converted into plant inflow. The fixture
records provenance and the inspected EDI commit. Generation connectors cannot
supply the missing plant water/head constraints; none is reused.

Run on this contribution's branch::

    python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
    python -m enerqit.hydro_study
    python docs/examples/plot_reservoir_water_budget.py
"""
import matplotlib.pyplot as plt

from enerqit.hydro_study import run_hydro_study

# %%
# 3. Actual agent and reusable method
# --------------------------------------
# The existing generic engineer invokes four registered bounded callbacks,
# using its scripted planner. Numerical implementation is dispatch_reservoir
# in EnerQit. This is actual tool execution, not a live LLM-quality experiment.
r = run_hydro_study()
print('Tool trace:',r['trace'])
print('Agent installation:',r['agent_install'])
b = r['reports']['benchmark_methods']
print('Gross value:',b['baseline_gross_eur'],b['optimized']['gross_value_eur'])

# %%
# 4. Physical benchmark
# --------------------------
# The feasible early-release baseline uses [40000,20000,20000] m3; optimization
# uses [20000,40000,20000], both retaining 20000 m3. Same total water and constant
# conversion, different timing. Independent tiny exhaustive turbine/bypass
# enumeration checks the LP in tests. No quantum approach is warranted.
fig, ax = plt.subplots(figsize=(7,4),constrained_layout=True)
ax.plot(range(4),b['baseline_reservoir_m3'],marker='o',label='Early-release baseline')
ax.plot(range(4),b['optimized']['reservoir_m3'],marker='o',label='Optimized')
ax.axhline(20000,color='gray',linestyle='--',label='Terminal floor')
ax.set(xlabel='Hours from synthetic UTC start',ylabel='Usable reservoir water (m³)',
       title='Same water budget, different release timing')
ax.legend()

# %%
# 5. Economic and sensitivity results
# --------------------------------------
# Gross scenario value rises from EUR833.85 to EUR1226.25 (EUR392.40), with no
# claim of realized revenue or profit. The example excludes costs and future
# water value. Dropping terminal inventory is an ablation, not a fair improvement
# in net value. Increasing the terminal floor to 60000 m3 makes minimum releases
# infeasible. Sensitivities include head, minimum releases and 3..8760 intervals.
print('Sensitivity:',r['reports']['assess_sensitivity'])

# %%
# 6. Limits and next action
# ----------------------------
# Constant head/efficiency, perfect foresight and unlimited bypass are strong
# simplifications. No cascade delays, evaporation, ramps or ecological response
# model. Both release paths count at one assumed downstream compliance point;
# this is not permission to substitute spill for any actual licensed release.
# Obtain plant inflow, stage-volume/head curves, outlet capacities and approved
# constraints, then review terminal water value and uncertain forecasts.
plt.show()
