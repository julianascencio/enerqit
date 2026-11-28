Recharge between reserve services
====================================

The :doc:`worked example </gallery/plot_reserve_recharge>` extends the documented
no-recharge reserve replay with least-cost recovery between mandatory services.
``plan_recharge`` uses known piecewise-constant AC discharge, permitted import
limits, elapsed UTC hours and nonnegative scenario EUR/MWh. Usable DC inventory
excludes minimum SOC and other reservations. A terminal lower bound is enforced.
Charging and mandatory discharge cannot occupy the same interval.

A sparse linear program minimizes sum(price * charge MW * hours), subject to
``state_next = state + eta_charge * charge * hours - discharge * hours / eta_discharge``.
Capacity, discharge power and import limits are explicit. The existing
``replay_activation`` independently checks tracking and states, with no reset.
An infeasible service returns an explicit status rather than partial success.

The 27 November NESO report is context, not calibration. Notices request margin;
they do not imply blackouts or actual battery activation. All model inputs are
synthetic MIT scenarios. In the four-hour case, optimized recharge costs
EUR24.6914 versus EUR123.4568 when only early recharge is permitted. Both buy
1.234568 AC MWh to replenish 1.111111 DC MWh. No recharge misses 1 AC MWh in causal
replay and cannot satisfy the exact-service optimization. No realized savings or
quantum advantage is claimed. This continuous LP needs no binary/QUBO encoding.

Six independent finite enumerations test tiny integral cases; physical replay
covers lossy cases. Sensitivity varies import limits and terminal reserve.
Scaling reports construction, solve and audit timing through 8760 intervals.
The actual generic QML engineer runs four bounded tools at the installed commit
recorded with versions, fixture hash and trace in the benchmark JSON.

Reproduce with ``python -m enerqit.recharge_study`` after installing the project
and ``requirements/agent-study.txt``. See the gallery for source links and figure.
No forecast training, learned policy or field validation is claimed. Known future
service and prices, fixed efficiency, no degradation, standby loss, network or
ramp constraints limit transfer. Next validate service obligations and connection
permissions on approved evidence. AI-authored; independent review remains needed.

.. automodule:: enerqit.recharge
   :members:
