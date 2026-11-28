"""
Energy hidden between dispatch setpoints
========================================

1. Context and decision
----------------------------------------------------------------------
The `NESO status report dated 26 November 2026
<https://www.neso.energy/document/390646/download>`_ provides current wind,
solar and grid-margin context. Its forecasts extend beyond the publication date;
no chart is digitized here. A flexibility engineer must decide whether a schedule
that meets endpoint demand also delivers sufficient energy while ramping.

2. Offline inputs and semantics
----------------------------------------------------------------------
All numerical inputs are synthetic MIT scenarios: a resource starts at 0 MW and
reaches 40 MW after one elapsed UTC hour against constant 40 MW demand. Its ramp
limit is 40 MW/h. Boundary samples are instantaneous, NOT interval averages.
EDI generation contracts were inspected at the commit in the fixture; no connector
is reused because interval-average MW cannot establish a within-interval path.

Run::

    pip install -e '.[dev,docs]' -r requirements/agent-study.txt
    python -m enerqit.ramp_energy_study
    python docs/examples/plot_continuous_ramp_energy.py
"""
import matplotlib.pyplot as plt

from enerqit.ramp_energy_study import run_ramp_energy_study

# %%
# 3. Actual existing agent invocation
# ----------------------------------------------------------------------
# Four bounded callbacks use the generic QML engineer's scripted planner.
# Numerical code lives in audit_linear_ramps, not inside this plotting script.
r = run_ramp_energy_study()
print(r['trace'])
print(r['fixture_sha256'])
b = r['reports']['benchmark_methods']
print(b)

# %%
# 4. Independent energy reconciliation
# ----------------------------------------------------------------------
# The existing LP correctly reports zero shortage under its documented held-output
# convention. Reinterpreting its endpoint as a continuous ramp delivers 20 MWh,
# not 40 MWh, and leaves 20 MWh unserved. This is a semantics comparison, not a
# claim of a solver error. Positive-part integration splits crossings analytically;
# six seeded tests compare against independent adaptive numerical quadrature.
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot([0,1],[40,40],label='Demand / held-setpoint baseline')
ax.plot([0,1],[0,40],label='Assumed continuous generation')
ax.fill_between([0,1],[0,40],[40,40],alpha=.2,label='20 MWh shortage')
ax.set(xlabel='Elapsed UTC hours',ylabel='MW',title='Synthetic trajectory audit')
ax.legend()

# %%
# 5. Economics, sensitivity and resources
# ----------------------------------------------------------------------
# At assumed EUR50/MWh generation and EUR1000/MWh shortage, continuous accounting
# gives EUR21000 versus EUR2000 for held output. The difference is a scenario
# penalty, not a bill or realized loss. Half-hour delivery violates the assumed
# ramp bound; two-hour delivery is feasible but has 40 MWh shortage.
# Subdivision from 1 to 8760 segments leaves exact energy unchanged. Recorded
# runtime is a single machine-dependent audit timing, not a speedup benchmark.
print(r['reports']['assess_sensitivity'])

# %%
# 6. Next practical action
# ----------------------------------------------------------------------
# Obtain operator-authorized instantaneous telemetry and verify interpolation,
# capacity, startup and network limits. No continuous dispatch optimum is claimed.
# Classical analytic integration suffices: no quantum-inspired, circuit or QPU
# run is warranted. Human review and real-asset validation remain outstanding.
plt.show()
