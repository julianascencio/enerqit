Bidirectional battery readiness
=====================================

A full battery cannot necessarily absorb energy during low operational demand.
The :doc:`runnable study </gallery/plot_storage_headroom>` computes an admissible
initial inventory for every activation in a declared range, then tests whether
an earlier preparation interval can reach it. This extends the one-directional
:doc:`reserve replay </reserve_depletion>` and empty-start
:doc:`curtailment recovery </curtailment_recovery>` with a robust initial-state
certificate. It does not optimize a periodic renewable plant or market bidding.

Evidence and question
---------------------------

`AEMO's 20 November 2026 release
<https://www.aemo.com.au/newsroom/media-release/aemo-prepares-for-summer-as-energy-supplies-forecast-to-remain-sufficient>`_
expects sufficient supply under forecast conditions for summer 2026-27, while
noting high and low demand preparation needs. This is operator motivation only.
No observed shortage, battery parameters or national results are inferred.
The numerical fixture is entirely authored synthetic MIT data. EDI generation
contracts were inspected at e72d9d822b442f6392c80ce12dfc62f738f51ddd; none are reused.

The decision is an initial usable DC energy and a minimum-movement preparation
step for a two-hour service window. KPIs are admissible DC MWh, missed absorption
and missed discharge AC MWh, reference gap, and preparation time/throughput.
The preparation objective minimizes absolute DC inventory movement; it is not
profit maximization. Service fees and inventory opportunity cost require data.

Model and certificate
---------------------------

For signed AC power ``p`` (positive discharge), duration ``h`` and efficiencies:

.. math::

   S_{t+1}=S_t+h_t(\eta_c\max(-p_t,0)-\max(p_t,0)/\eta_d).

This increment decreases monotonically with power. For the Cartesian product of
interval bounds, cumulative all-upper powers give minimum boundary-energy
increments ``a``; all-lower powers give maximum increments ``b``. Include the
initial zero increment. Necessary and sufficient energy inequalities are:

.. math::

   -\min_t a_t \le S_0 \le E-\max_t b_t.

All activation bounds must also fit the separate charge/discharge MW ratings.
Minimum usable capacity ignoring power is ``max(b)-min(a)``. An empty interval
is infeasible, not a zero-width feasible solution. This exact classical method
uses O(n) time and memory. Recorded envelope timings include array conversion but
exclude window validation/construction; single-run timings are diagnostics, not
a speedup claim. Inputs are capped at 100000 intervals; the exponential LP
reference is capped at eight. No quantum method is warranted. Independent small
LPs use shared initial energy and separate path state variables, checking all
corner trajectories. Interior points follow from monotonicity, not sampling.

Intervals are contiguous piecewise-constant UTC intervals; durations are elapsed
hours, potentially unequal. No date inference/resampling occurs. The fixture
provides a hypothetical UTC start. Usable DC capacity excludes the physical SOC
floor. No simultaneous charging/discharging, standby loss, ramp, temperature,
network, terminal SOC or concurrent reserve obligation is represented.

Results and interpretation
--------------------------------

For a 40 DC-MWh, 30 AC-MW battery with 90% efficiencies, activation is -20..-10 MW
then +10..+20 MW. Initial energy must be 13.2222..22 MWh. Full initial SOC misses
20 AC MWh of absorption on the (-20,+20) probe; half-full and prepared cases
track it. A 30 DC-MWh battery cannot guarantee the complete uncertainty box.
The minimum required capacity is 31.2222 DC MWh. These are synthetic mechanisms,
not Australian system forecasts or asset readiness certification.

Preparation from full to 22 MWh exports 16.2 AC MWh in at least 0.54 hours.
At an assumed EUR5/AC-MWh throughput fee the fee alone is EUR81. It excludes
energy proceeds, inventory value, degradation calibration, tax and service
payments. It is neither a complete cost nor a realized saving. A half-hour
preparation window fails; increasing uncertainty can invalidate every SOC.

Reproduce and review
--------------------------

.. code-block:: bash

   python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
   python -m enerqit.activation_study
   python docs/examples/plot_storage_headroom.py
   python -m pytest tests/test_storage_envelope.py

The existing generic role at f8150df9a4272bf2b97042a61b3b785a92450057 actually
runs four registered callbacks. Its default planner is scripted, and successful
execution leaves human review required and equipment execution unauthorized.
No energy-agents changes are necessary. The result retains the fixture hash,
package/install versions, trace, sensitivities and scaling through 100000 slots.
Methods and documentation are AI-authored; independent human review and field
validation are pending. Next collect licensed activation, SOC and efficiency
evidence, verify preparation import/export rights, test correlated alternatives
and value terminal inventory before a commercial decision.
