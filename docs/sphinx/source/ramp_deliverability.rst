Ramp deliverability and pre-positioning
============================================

A flexibility planner needs timely output, not just installed MW. The primary
`NESO report of 18 November 2026 <https://www.neso.energy/document/390381/download>`_
contains current wind forecasts and risk indicators. It motivates this generic
screen; it does not establish a shortage, resource ramp rate or investment return.
The dated candidate ledger compares this case with Spanish curtailment (already
implemented), US storage deployment and data-centre power conversion.

Model and decision
-----------------------

``plan_ramping`` minimizes generation cost plus unserved-energy penalty. Output
is bounded by online capacity and symmetric changes between consecutive
setpoints, including the initial output. Nonnegative shortage closes demand;
excess generation is explicitly spilled. Energy durations and transition budgets
are distinct hour arrays. This is a discrete setpoint approximation: ramping
trajectory energy is not integrated. No startup, minimum output, fuel budget,
network, storage or inertia model is claimed. Spill must be physically permitted.

The sparse HiGHS LP uses two variables per interval, up to 8760 intervals.
A separate audit checks ramp/capacity bounds and recomputes objective accounting.
Capacity-only output can violate ramps; causal tracking is feasible but lacks
foresight. Independent tests enumerate feasible tiny integer paths to validate
LP costs, plus variable-duration, downward-ramp, zero-capacity and invalid cases.
No quantum method is warranted for this continuous linear problem.

Synthetic benchmark
------------------------

The three one-hour residual demands are 0, 40, 40 MW. Online capacity is 40 MW,
initial output zero, and each transition permits 20 MW change. Generation costs
an assumed EUR 50/MWh and shortage carries EUR 1000/MWh penalty. Capacity-only
screening reports zero shortage. Causal tracking produces 0/20/40 MW, leaves
20 MWh unserved and costs EUR 23000. The optimal 20/40/40 MW path spills 20 MWh
but avoids shortage and costs EUR 5000. The EUR 18000 difference is hypothetical
avoided modeled cost, not profit or a measured system saving.

Sensitivity varies ramp rates and penalty assumptions; it is not a probabilistic
confidence interval. Perfect demand foresight is an optimistic information
assumption. Next steps are operator-approved ramp envelopes, forecast vintages,
spill permissions, transition-energy treatment and independent human review.
All numeric inputs are authored synthetic MIT data. No external connector or
provider observations are reused. The source report body is not redistributed;
its response hash or retrieval failure is recorded separately from fixture hash.

Reproduce
--------------

.. code-block:: bash

   python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
   python -m enerqit.ramping_study
   python docs/examples/plot_ramp_deliverability.py

The :doc:`gallery </gallery/plot_ramp_deliverability>` invokes the generic
engineer's actual registered tools. Agent revision, source/input provenance,
package versions and results are preserved in the benchmark record. Replay uses
no randomness; enumeration tests use seeds 0..4. Dates use UTC and synthetic
intervals use elapsed hours. AI-authored, automated validation only; no physical
quantum execution, operational dispatch or field validation.

Energy Data Insights generation contracts inspected at
``e72d9d822b442f6392c80ce12dfc62f738f51ddd`` describe observations, not operator
ramp envelopes or forecast vintages. No connector or separately licensed code
was reused. Resource parameters require independent operational evidence.
