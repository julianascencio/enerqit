"""
Recharge between repeated reserve services
======================================================================

1. Evidence and operator decision
----------------------------------------------------------------------
The `27 November NESO status report
<https://www.neso.energy/document/390771/download>`_ updates grid conditions.
`NESO's notice explanation
<https://www.neso.energy/electricity-explained/how-do-we-balance-grid/what-are-system-notices>`_
clarifies that margin notices request a larger cushion, not forecast blackouts.
The new question is whether a battery can recover energy between two services,
and what the least-cost permitted recharge would be. These are synthetic service
requests, not observed activations or a reconstruction of the NESO events.

2. Offline inputs and preparation
----------------------------------------------------------------------
Four consecutive one-hour UTC intervals begin 28 November 2026 00:00Z. Discharge
is 1 MW in the first and last intervals. Only the two middle intervals allow
charging, at 2 MW; assumed prices are EUR100 and EUR20/MWh. Initial and usable
capacity are 1/0.9 DC MWh; both efficiencies are 0.9. All inputs are authored MIT
scenarios. EDI's unchanged generation contracts were reused as inspected context;
interval generation does not establish recharge rights. No connector is reused.

Run::

    pip install -e '.[dev,docs]' -r requirements/agent-study.txt
    python -m enerqit.recharge_study
    python docs/examples/plot_reserve_recharge.py
"""
import matplotlib.pyplot as plt

from enerqit.recharge_study import run_recharge_study

# %%
# 3. Existing agent and reusable method
# --------------------------------------------------------------------
# The generic QML engineer runs its four registered callbacks. plan_recharge
# minimizes purchases with a sparse LP; replay_activation independently checks
# DC inventory and AC tracking. No state reset occurs between windows.
r = run_recharge_study()
print(r['agent_install'])
print(r['trace'])
print(r['fixture_sha256'])
b = r['reports']['benchmark_methods']
print(b)

# %%
# 4. Benchmarks and economic interpretation
# --------------------------------------------------------------------
# The optimizer buys 1/0.81 = 1.234568 AC MWh in the cheap interval, costing
# EUR24.6914. Restricting recharge to the early interval costs EUR123.4568.
# The EUR98.7654 difference is conditional scenario purchase cost, not realized
# savings. Without recharge, exact service is infeasible and causal replay misses
# 1 MWh. Infeasibility is not replaced by an apparently successful clipped plan.
fig, ax = plt.subplots(figsize=(7, 4))
for name in ('optimized', 'early_only'):
    ax.plot(range(5), b[name]['energy_dc_mwh'], marker='o', label=name)
ax.set(xlabel='Elapsed UTC hours', ylabel='Usable DC MWh', title='Synthetic recharge policies')
ax.legend()

# %%
# 5. Sensitivity, exact references and resources
# --------------------------------------------------------------------
# Tight import limits can make the service infeasible. A terminal reserve raises
# the recharge requirement and can also cause infeasibility. Six tiny integer
# cases compare LP cost to independent complete enumeration; gap is zero within
# test tolerance. Scaling to 8760 intervals records single-run construction/solve/
# audit time, not a hardware speedup. Classical LP suffices; no quantum execution.
print(r['reports']['assess_sensitivity'])

# %%
# 6. Limits and next action
# --------------------------------------------------------------------
# Known future prices/services, nonnegative prices, fixed efficiencies, no standby
# loss or degradation. Positive discharge and permitted charging cannot overlap;
# mixed intervals must be split. Confirm import permission, service obligations,
# operating reserves and network limits before an independently reviewed trial.
plt.show()
