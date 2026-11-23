Terminal water value and horizon bias
============================================

The :doc:`runnable example </gallery/plot_terminal_water_value>` advances the
explicit terminal-water-value backlog in :doc:`hydro_water`. No recent verified
story offered a stronger distinct implementation, so the study reuses the
five-day-old `NVE week-46 report
<https://www.nve.no/media/20550/2026_46_kraftsituasjonen.pdf>`_, published 18 November
2026, covering 9-15 November. It describes price expectations influencing water
use. It is not a dataset calibrating the plant or continuation-value curve.

Method and accounting
------------------------------

``dispatch_reservoir`` now accepts an optional ``TerminalWaterValue``. With
``None``, existing physics and cash-only behavior are retained. The curve has
increasing volume knots beginning at zero and EUR values beginning at zero.
Marginal EUR/m3 values are nonnegative and nonincreasing, so the curve is concave.
The domain must cover usable reservoir capacity; extrapolation is rejected.

For segment slopes m and intercepts b, one additional LP variable z satisfies
``z <= m*S_final + b`` for every segment. Maximizing cash plus z exactly
represents the concave piecewise-linear value. Final value is independently
recomputed by interpolation and audited against the solver objective.
The existing water balance and minimum-release checks remain unchanged.

``gross_value_eur`` is only energy-sale scenario value. ``terminal_value_eur``
is a caller-assumed continuation valuation, not a payment.
``objective_value_eur`` is their sum. All inventory, including volume below a
terminal floor, is valued. The common initial inventory value is omitted because
it cancels in policy comparisons. Discounting and future risk must already be
reflected in the supplied curve; neither is inferred. No profit is calculated.

`PyPSA's water-value example <https://docs.pypsa.org/latest/examples/water-value/>`_
supplies technical context for limited-horizon decisions, not reused code or a
replicated result. The implemented concave LP is classical; no quantum method
is warranted. Complexity adds one variable and one constraint per segment;
limits are 8760 intervals and 1000 knots. Runtime includes construction/solve.

Synthetic results
---------------------------

The same physical inputs and common valuation are used to evaluate all policies:

.. list-table:: Three-hour scenario, not observed revenue
   :header-rows: 1

   * - Policy
     - Gross energy EUR
     - Final m3
     - Common cash + terminal EUR
   * - Cash-only
     - 1373.40
     - 0
     - 1373.40
   * - Fixed 60000 m3 floor
     - 613.125
     - 60000
     - 1913.125
   * - Concave water value
     - 1103.625
     - 40000
     - 2303.625

The curve-aware policy sacrifices current gross value to retain assumed future
value. Its EUR930.225 common-score increase over cash-only is not realized revenue
or savings. Six seeded tiny exhaustive physical references independently verify
optima, including kink points, while regression tests preserve the default API.
Curve multipliers and inflow scenarios expose dependence on uncertain assumptions;
zero valuation recovers cash-only behavior. Scaling reaches 8760 intervals.

Reproduction and practical limits
---------------------------------------

.. code-block:: bash

   python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
   python -m enerqit.water_value_study
   python docs/examples/plot_terminal_water_value.py

All inputs are authored synthetic MIT data, with UTC time semantics and SHA256.
The existing agent at 9a8a56b3be12e734183a0350600bf874bdee8ff0 actually runs its
four callbacks with the scripted planner and retains human-review and no-execution
safeguards. EDI inspected at e72d9d822b442f6392c80ce12dfc62f738f51ddd; no connector
reused. Results include package/install versions and tool trace.

No curve fitting or forecast validation is claimed. The next action is to estimate
continuation values using pre-decision evidence, freeze the model, then evaluate
later unseen inflows/prices. Existing constant-head, unlimited-bypass and known
within-window inputs remain strong assumptions. No operational dispatch, ecological
compliance, bankable valuation or scientific novelty is claimed. AI-authored;
independent human review and field calibration remain outstanding.
