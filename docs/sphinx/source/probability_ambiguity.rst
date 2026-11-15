Probability ambiguity in reserve procurement
============================================

Problem and evidence
--------------------

A capacity planner chooses the cheapest guaranteed-MW offer meeting an EENS
limit over one four-hour constant-demand window. The 14 November nominal
adequacy study leaves calibrated joint-outage probabilities unresolved. This
15 November contribution advances that one-day-old backlog rather than claiming
a new outage event. NESO's `14 November report
<https://www.neso.energy/document/390236/download>`_ and ENTSO-E's
`13 November outlook
<https://www.entsoe.eu/news/2026/11/13/entso-e-winter-outlook-2026-2027-europe-is-prepared-some-risks-remain-in-specific-areas/>`_
provide current context, not numerical calibration. Candidates and dates are
preserved in the packaged fixture. No external connector or third-party dataset
is reused. All numerical inputs are authored synthetic MIT data.

Method
------

For fixed available-capacity support A, nominal probabilities p, reserve F,
demand D and hours h, solve the finite-support linear program

.. math::

   \max_q \sum_i q_i h\max(D-F-A_i,0),\quad
   q\ge0,\ \sum_i q_i=1,\ \frac12\sum_i|q_i-p_i|\le\rho.

Auxiliary variables linearize absolute deviations. SciPy's
`HiGHS linprog <https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html>`_
solves the sparse LP; a separate audit checks probability mass and total variation.
Each offer gets its own worst distribution. Exhaustive outer search certifies
minimum cost only within supplied offers, up to numerical feasibility tolerances.
Radius is dimensionless and is not a statistical confidence level. This set
allows marginal unit probabilities to change; it is more general than varying
only the common-outage parameter. No probability is silently normalized.

Synthetic result and decision
-----------------------------

Support 0/60/120 MW has probabilities .109/.162/.729; demand is 100 MW.
Target EENS is 20 MWh, and fixed whole-window fees are 100 EUR per reserve MW.
At radius zero, 60 MW at EUR 6,000 meets the target with 17.44 MWh EENS.
At radius .05 its worst EENS is 25.44 MWh, so 80 MW at EUR 8,000 is required
and yields 12.72 MWh. Extra expenditure is hypothetical, not realized savings.
No-load and full-reserve cases have zero losses. At radius one the model may
concentrate all mass on the largest loss in the supplied support.

The classical nominal baseline is radius zero. Exact two-state formulas and a
three-state simplex lattice independently check the LP. No quantum-inspired,
circuit or hardware algorithm is forced into this convex inner problem.
Sensitivity covers radius 0 through 1; scaling covers 2/16/128 states. The method
caps support at 4096 states and offers at 100. Matrix storage is sparse O(n);
LP solve time depends on the instance and is not guaranteed linear.

Reproduction and limits
-----------------------

.. code-block:: bash

   python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
   python -m enerqit.robust_adequacy_study
   python docs/examples/plot_probability_ambiguity.py

The existing engineer role executes evidence, benchmark, sensitivity and handoff
callbacks. Its current revision and actual installation metadata, environment,
input hash and tool trace accompany the result. No random seed is needed for
this deterministic LP. UTC dates identify sources; synthetic elapsed hours
are not observed timestamps. The :doc:`gallery </gallery/plot_probability_ambiguity>`
shows the full workflow. Numerical APIs reside in EnerQit, not energy-agents.

The model cannot discover missing failure states. Include plausible zero-mass
states explicitly if probability can move there. Guaranteed capacity outside
modeled failures, fixed demand and no chronology are strong assumptions.
No annual LOLE, regional reliability, storage-energy adequacy, network feasibility
or confidence coverage is established. Calibrate support/radius with licensed
joint outages and chronological evidence, then obtain independent human review.
AI-generated implementation and automated checks do not replace that review.
