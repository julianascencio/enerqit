Chronological renewable firming and storage size
================================================

A renewable project planner needs to know whether complementary wind output
reduces battery energy requirements at fixed AC power. This study answers that
question for supplied chronological profiles with full load served and a repeated
cycle. It does not estimate a location's annual reliability or optimize wind/PV
investment. Unlike the earlier availability-portfolio example, it models charging,
discharging, energy inventory, conversion losses and cycle boundaries.

Evidence and selection
-----------------------

`Harnessing the winds <https://ember-energy.org/latest-insights/harnessing-the-winds/>`_
examines wind/solar/storage complementarity. The primary article indexed text is
dated 13 November 2026, while Ember's listing showed 12 November; this discrepancy
is preserved. It analyzes historical weather, not an event on publication day.
Direct retrieval returned HTTP 403; primary indexed text was read via web search.
No raw-page hash or replication claim is invented.

Alternatives were Japan electrification (article dated 11 November) and the IEA
`Renewables 2026 <https://www.iea.org/reports/renewables-2026>`_ (6 November).
The packaged evidence compares impact, technical importance, evidence, tractability,
novelty and method fit. The first 72-hour search covered renewables, storage,
hydro, grids, demand and data centres; older sources were dated explicitly.
The selected current story motivates a specific unimplemented storage-roadmap
capability rather than repeating merged network security work.

Energy Data Insights was inspected at
``53f47b87fe9a6213e85a7fe60d4cf2599ec26658``. Its REE battery screen is a one-cycle
cost calculation, not a co-located weather series. No code or connector is copied.
All numeric profiles, parameters and unit costs here are authored synthetic
assumptions under MIT. No full article or third-party dataset is redistributed.

Model
------

For AC charging c, AC discharge d, usable DC inventory s and capacity E, minimize
E at fixed power P. For each interval of duration h:

.. math::

   s_{t+1}=s_t+h(\eta_c c_t-d_t/\eta_d),\quad
   r_t+d_t-c_t\ge L_t,\quad 0\le s_t\le E.

A binary mode z enforces c <= P z and d <= P(1-z). Initial inventory is optimized
subject to s_0 = s_T: a periodic steady-state assumption, not free net energy or
a cold-start guarantee. Excess renewable supply is curtailed. There is no backup,
load shedding, export revenue or grid charging. E is bounded by the supplied
maximum; infeasibility may indicate that bound, a power bottleneck, or insufficient
renewable energy. The solver does not silently relax constraints.

The LP relaxation supplies a lower bound by relaxing mode integrality. Its dispatch
is still audited for simultaneous operation; an LP bound is not automatically a
physical schedule. HiGHS MILP is classical. QUBO, simulated annealing, simulated
bifurcation, circuit simulation and quantum hardware are not used or claimed.

The evaluator reconstructs SOC increments, cycle residual, shortfall, power and
capacity bounds, simultaneous operation, curtailment and conversion losses.
Background: `PyPSA storage equations
<https://docs.pypsa.org/latest/user-guide/optimization/storage/>`_. PyPSA is not a
runtime dependency or a claim of cross-package validation.

Independent benchmark and economics
------------------------------------

All profiles deliver 6 MWh over four one-hour intervals to 1 MW constant load,
with 2 MW battery power, 10 MWh capacity search bound and 0.9 efficiency each way.

.. list-table:: Synthetic reference
   :header-rows: 1

   * - Profile (MW)
     - No-storage shortfall (MWh)
     - Required usable DC MWh
   * - Solar: 0, 3, 3, 0
     - 2
     - 2.222222
   * - Complementary mix: 0.75, 2.25, 2.25, 0.75
     - 0.5
     - 0.555556
   * - Coincident mix: 0, 3, 3, 0
     - 2
     - 2.222222

Two consecutive deficits cross the cycle boundary. Their DC requirements are
2/0.9 and 0.5/0.9 MWh. Surplus intervals can replenish these amounts within the
power constraint, proving both a lower bound and attainability independent of
optimization matrices. MILP matches the references, and LP bounds match capacity.
Coincident output is a timing ablation: changing the technology label alone gives
no benefit. Cyclic rotations test against artificial boundary advantages.

At an explicitly assumed 200,000 EUR per usable DC MWh, the energy-component
screen is 444,444 EUR versus 111,111 EUR. The 333,333 EUR difference excludes
additional wind/PV cost, power electronics, financing, aging and replacement.
It is not total project savings, a market quote, LCOE or realized revenue.

Efficiency sensitivity 0.8/0.9/1 gives complementary-case capacity
0.625/0.555556/0.5 MWh. A 0.2 MW battery cannot cover a 0.25 MW shortfall; a joint
50% renewable lull is infeasible regardless of timing because energy is inadequate.
These are scenario ranges, not probabilistic confidence intervals. Repeating the
same cycle to 24/96 intervals measures runtime and dense matrix growth, not new
weather evidence. Inputs are limited to 168 intervals; solver time limit is
30 seconds and failure to prove optimality is reported rather than accepted.

Agent and reproduction
-----------------------

The actual generic ``career_quantum_ml_engineer`` and its 13-skill contract at
``e077b5f240852c7fe28c4de2ed530a52f65e8347`` run four bounded EnerQit callbacks.
The existing registered-study adapter needs no energy-agents PR. Its planner is
scripted/offline, not a live LLM. Numerical methods stay in ``storage_sizing``.

.. code-block:: bash

   python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
   python -m enerqit.firming_study
   python docs/examples/plot_renewable_firming.py

The :doc:`gallery </gallery/plot_renewable_firming>` includes actual tool trace,
figures and benchmark. Packaged JSON inputs and metadata have a SHA256 in the
results record, alongside environment and actual installed agent revision.
There is no stochastic sampling (seed null). Synthetic time is ordered elapsed
hours, not a claimed calendar observation; future measurements must use UTC.

Next practical step: obtain licensed multi-year co-located generation and load,
validate chronological holdouts, and model initial-state policy, joint lulls,
reserves, degradation and full lifecycle costs. Do not infer annual uptime from
this example. Code and documentation are AI-generated and automatically tested;
human scientific review and field validation remain outstanding.
