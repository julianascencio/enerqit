Curtailment recovery with explicit energy accounting
====================================================

Decision and current evidence
-----------------------------

A renewable operator screens whether a behind-the-meter battery can recover
otherwise-export-limited generation. Wood Mackenzie's `16 November 2026 release
<https://www.woodmac.com/press-releases/spains-renewable-sector-has-lost-140-million-to-grid-constraints-as-curtailment-remains-elevated-since-april-2025-blackout/>`_
reports persistent Spanish constraints from year-to-date analysis using REE data
through October. This is context, not a calibrated site dataset. The current
candidate ledger also compares storage deployment, Greek connection approvals
data-centre power equipment and Norwegian hydro/demand news. This physical recovery ledger is distinct
from pending discharge-only export and reserve studies.

All numerical inputs are authored synthetic MIT fixtures. No external connector
or third-party dataset is reused. Energy Data Insights generation connector
contracts were inspected at fc63c5f97e6513e7f290340ddfdce0b80962644a:
REE supplies system/technology calendar-period generation, not this study's
plant-level available output, export ceiling or charging permission. No code or
data is copied from that separately licensed project. No full articles or proprietary nodal data
are redistributed. Real interval-level evidence remains a prerequisite.

Physical model
--------------

Direct export equals min(generation, ceiling). Surplus above that ceiling may
charge the battery, bounded by charge power and remaining DC capacity. During
later headroom, discharge is bounded by power, available DC energy times
output efficiency and export headroom. Charge and discharge windows are disjoint.
Start empty; do not reset inventory each interval. There is no grid charging.
Existing storage validation conventions are reused; existing cyclic firming and
network APIs remain unchanged because this is a causal export-ceiling replay.

For AC charge C and discharge D, DC inventory changes by eta_c*C*h-D*h/eta_d.
Captured AC energy equals recovered AC export plus conversion losses plus
terminal DC inventory. The ledger explicitly verifies this conservation law.
Stored terminal energy is not counted as delivered export or current revenue.
A generation curtailment order may prohibit charging: this model applies only
where the constraint is net export and on-site charging is permitted.

Benchmark and business interpretation
-------------------------------------

Two hours at 50 MW generation behind a 30 MW ceiling produce 40 MWh surplus.
A 20 MW / 40 MWh DC battery with .9/.9 efficiencies captures 40 MWh, later
exports 32.4 MWh, loses 7.6 MWh and ends empty. No battery recovers zero.
A 20 MWh battery exports 18 MWh; 80 MWh capacity still exports only 32.4 MWh.
With no later export headroom, recovery is zero and 36 MWh remains stored.
At assumed flat EUR 50/MWh, the 40 MWh option yields EUR 1,620 gross additional
export value. Acquisition, degradation, fees and charging permission are excluded;
this is not an investment recommendation or realized savings estimate.

The causal greedy rule is compared against an independent inventory LP on five
seeded variable-duration cases. It uses no price forecasts and does not optimize
market value. Tests include independent hand calculations, physical conservation,
zero capacity, no headroom and invalid inputs. Sensitivity covers battery size,
efficiency and headroom; scaling covers 6/24/168/8760 intervals. Replay is O(T),
with a 100,000-interval input cap. No quantum method is needed.

Reproduce and next action
-------------------------

.. code-block:: bash

   python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
   python -m enerqit.curtailment_study
   python docs/examples/plot_curtailment_recovery.py

The :doc:`gallery </gallery/plot_curtailment_recovery>` executes the generic
engineer's four registered tools. Actual agent revision, package versions, input
hash and results are recorded. Replay is deterministic; independent reference
tests use seeds 0..4. Sources use UTC dates; synthetic intervals are elapsed hours.
No annualization, Spanish grid stability result or field validation is claimed.
Obtain licensed interval data and operator permissions, then independent human
review. Implementation and documentation are AI-generated with automated checks.
