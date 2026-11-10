Network-aware curtailment and upgrade screening
===============================================

Decision and evidence
---------------------

A grid planner chooses which existing line rating to increase for one constant
hour of renewable transfer. The KPI is physically feasible renewable MWh;
the objective is minimum firm generation cost in EUR. Baselines share the same
inputs and cost accounting. Load must be served; there is no hidden shedding.

The `Ember guide published 5 November 2026
<https://ember-energy.org/latest-insights/building-a-grid-for-the-age-of-power/>`_
motivates grid modernisation, but supplies no topology calibration. Selection on
10 November first searched 72 hours, then seven days; this advances a five-day-old
source-backed backlog item. Alternatives were the IEA's 6 November renewables
outlook and Banque de France's 4 November data-centre commentary. The packaged
``network_research_20261110.json`` compares economic importance, evidence,
tractability, novelty and method fit; ``research/news-ledger.json`` preserves
prior selection history and unresolved data needs.

All numerical inputs are independently authored synthetic assumptions under MIT.
Only source metadata, links and summaries are redistributed; source response
hashes are preserved from the earlier same-day research pass. News is not
calibration evidence. Energy Data Insights was inspected at
``b5ae10d43619155519a56ab3a30cb6660db8ca55``: its REE adjustment/BESS workflow
provides aggregate costs, not this model's bus topology and reactances. No
unverified connector or purported real network was constructed.

Model and independent reference
--------------------------------

``DispatchCase`` stores bus-aligned MW vectors, nonnegative firm costs in EUR/MWh,
positive line susceptance in MW/radian, symmetric ratings in MW and duration in
hours. Duration is a constant-power interval, not a timestamp. Telemetry must
be aligned in UTC before constructing cases; this example has no observed dates.
Inputs reject nonfinite values, negative capacity, invalid endpoints and islands.

For incidence matrix A (positive at the sending bus), diagonal susceptance D,
renewable generation r, firm generation g and demand d, DC dispatch solves:

.. math::

   \min_{r,g,\theta}\; h c^T g
   \quad\text{subject to}\quad r+g-d = A D A^T\theta,

.. math::

   0\le r\le \bar r,\quad 0\le g\le\bar g,\quad
   -\bar f\le D A^T\theta\le\bar f,\quad\theta_0=0.

HiGHS solves this continuous LP. Copperplate removes line constraints; the
transport relaxation imposes nodal balance and edge bounds but omits the
passive-network angle relation. Neither relaxation is automatically a feasible
AC-grid schedule. ``evaluate_dispatch`` independently solves the reduced nodal
Laplacian from injections, checks balance, generation bounds and line overloads.
It rejects unbalanced generation rather than silently adding slack-bus supply.

In the equal-reactance triangle, renewable transfer R splits into R/3 on 0–1 and
1–2, and 2R/3 on 0–2. With ratings 40, 100, 100 MW, feasible transfer is at most
120 MW. Demand is 150 MW, so at least 30 MW of local firm generation is needed.
Its assumed 100 EUR/MWh cost makes the independently derived optimum 3,000 EUR
for one hour. The LP attains it: zero gap to this analytic small-instance reference.

.. list-table:: Actual synthetic benchmark
   :header-rows: 1

   * - Model
     - Cost (EUR/hour)
     - Curtailed (MWh)
     - DC overload (MW)
   * - Copperplate
     - 0
     - 0
     - 10
   * - Transport relaxation
     - 1,000
     - 10
     - 6.6667
   * - DC LP
     - 3,000
     - 30
     - 0

Increasing the 0–1 rating by 10 MW permits all 150 MW renewable generation and
avoids 3,000 EUR of modeled firm cost in this hour. Increasing either other
rating alone yields zero benefit. This is a rating intervention at unchanged
reactance, not a simulated new line or an investment recommendation. There are
no capex, reliability, annual hours or market settlement assumptions.

Sensitivity, resource limits and method selection
-------------------------------------------------

Availability 50/100/150/200 MW yields curtailment 0/0/30/80 MWh. Firm costs
50/100/200 EUR/MWh yield baseline costs 1,500/3,000/6,000 EUR. These are scenario
ranges, not calibrated confidence intervals or probabilities. Uniform physical
scaling by 0.1/1/10 preserves angles and scales energy/cost. Radial chains of
5/20/100 buses independently require 110 MW firm supply at their 40 MW cut;
recorded construction/solver times and dense matrix bytes describe actual runs.

The API bounds studies to 100 buses and 300 lines; it uses dense matrices and is
not a transmission-scale engine. No performance extrapolation follows from a
single timing. The problem is convex: classical LP is appropriate. Ordinary SA,
simulated bifurcation, circuit simulation and QPU execution are all **unused**;
there is no quantum or hybrid advantage claim. An integer expansion decision
would be a different study requiring a MILP baseline and investment data.

Agent, reproduction and validation
-----------------------------------

The actual generic ``career_quantum_ml_engineer`` is used at commit
``832f4117f95ac3137c63eace389e56cdc2c075fe`` with its current role/13-skill contract.
Its existing registered-study tool adapter needs no change. Four bounded callbacks
inspect evidence, benchmark methods, assess sensitivity and prepare a handoff,
then finish. The planner is scripted and offline, with no LLM or dispatch authority.
All numerical methods remain in EnerQit.

.. code-block:: bash

   python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
   python -m enerqit.network_study --output results/network-engineer.json
   python docs/examples/plot_network_curtailment.py

The :doc:`step-by-step gallery </gallery/plot_network_curtailment>` includes the
actual trace, figures and handoff. Packaged inputs, canonical input hash, evidence
hash, actual installed agent source and environment versions accompany the run.
No randomness is used (seed is null, not an unstated random seed).
``benchmarks/results/network-engineer-20261110.json`` records results and
``research/network-validation-20261110.md`` records executed checks.

Tests use the independent triangle derivation, radial equivalence, reversed line
orientation, Kirchhoff cycle balance, shortage infeasibility, bad inputs and
duration/physical scaling. These validate the stated DC model, not real assets.
The work is AI-generated and reviewed through these automated physical checks;
human scientific review and operational validation remain outstanding.

Next practical action
----------------------

Obtain openly licensed bus/branch topology, reactances, ratings, hourly injections,
outages and marginal costs. Calibrate against measured flows, then validate AC
voltage/reactive power, losses and contingencies. DC screening here omits all of
those, plus ramping, storage, unit commitment and cross-hour coupling. Do not
annualize the one-hour benefit without a representative chronology and capex.

Technical background: `PyPSA power-flow constraints
<https://docs.pypsa.org/latest/user-guide/optimization/power-flow/>`_ describe nodal
and cycle constraints. PyPSA is a methodological reference, not a runtime dependency
or a claim of cross-tool numerical validation.
