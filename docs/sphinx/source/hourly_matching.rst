Renewable procurement and temporal matching
==================================================

The `Climate Council release of 19 November 2026
<https://www.climatecouncil.org.au/resources/data-centres-that-could-rival-our-dirtiest-coal-power-stations/>`_
raises the electricity-demand implications of Australian data-centre proposals.
Its scenarios to 2035 are conditional; its policy recommendations are not enacted
requirements. This study addresses one bounded buyer decision: how much of each
renewable profile to contract for a specified simultaneous matching fraction?
No source projection or facility data calibrates the synthetic example.

Physical and commercial contract
--------------------------------------

Contract capacities x multiply available AC MW/MW profiles. Simultaneously matched
power is min(load, contracted generation) in each interval. The constraint sums
matched MWh and requires a chosen fraction of demand MWh. It does not require
that fraction in every individual hour. A 100% target does require all positive
load to be matched. Zero load is defined as fully matched with zero procurement.
The total-energy baseline instead allows surplus in one interval to offset a
shortfall elsewhere, then reports its actual temporal coverage independently.

A sparse HiGHS LP minimizes positive EUR/MW contract costs for the exact supplied
horizon. These are not LCOE or spot prices, and shorter examples are not annual
cost estimates. Procurement is continuous and bounded per resource. Infeasible
targets return explicit status. Capacity, target and objective are independently
audited. Profiles and durations must be aligned by the caller; no timestamps,
resampling or missing values are invented. Existing chronological ingestion can
prepare qualified UTC observations before this array API is used.

No storage, transmission losses, curtailment compensation, grid deliverability,
certificate ownership, additionality, emissions attribution or legal compliance
is inferred. A contract allocation is not a physical power-flow result. Perfect
known profiles are an optimistic screening assumption, not a forecast evaluation.

Benchmark and limits
--------------------------

Two one-hour intervals have 1 MW load each, a solar-like [1,0] profile and a
wind-like [.5,.5] profile. Both profiles are synthetic. Horizon capacity contracts
cost EUR500/MW and EUR1500/MW respectively, with 4 MW available of each.
Total-energy matching buys 2 MW solar for EUR1000 but matches only 50% of load
simultaneously. Temporal matching buys 2 MW wind for EUR3000 and reaches 100%.
A 75% target costs EUR1750 using 0.5 MW solar and 1 MW wind. The EUR2000 premium
for full temporal coverage is hypothetical expenditure, not realized savings.

Independent tests cover the analytic piecewise frontier, three exhaustive tiny
capacity grids (seeds 0..2), unequal durations, impossible dark intervals, zero
load and invalid inputs. Sensitivity covers target and wind cost; runtime scaling
covers 2, 24, 168 and 8760 intervals. Results are numerical validation only,
not a probabilistic reliability claim. Continuous LP is appropriate; no quantum
advantage or physical quantum execution is claimed.

Reproduce and next action
-------------------------------

.. code-block:: bash

   python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
   python -m enerqit.matching_study
   python docs/examples/plot_hourly_matching.py

The :doc:`gallery </gallery/plot_hourly_matching>` executes the existing generic
engineer's four registered callbacks with a scripted planner. The result records
actual agent install revision, input hash and package versions. Inputs are
MIT-authored synthetic fixtures. No third-party dataset is redistributed. Source
response hashes or retrieval limitations are explicit. Evidence dates are UTC;
numerical intervals are elapsed hours. Four dated news candidates are recorded.
Obtain licensed aligned site profiles, load and contract terms, establish attribute
ownership, and seek independent human scientific review before operational use.
This contribution is AI-authored and has automated checks, not field validation.

Energy Data Insights generation contracts were inspected at
``e72d9d822b442f6392c80ce12dfc62f738f51ddd``. Aggregate generation and unit SCADA
alone do not supply this buyer's load, contract availability, prices or attribute
ownership. No connector, separately licensed code or dataset was reused.
