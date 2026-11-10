Duration-aware battery portfolio engineering
============================================

The 10 November 2026 engineering run asks: **which set of battery availability
offers can sustain a constant-power block at minimum fixed cost?** A power-only
selection can look cheap while lacking enough usable energy. The runnable
:doc:`gallery study <gallery/plot_battery_portfolio>` uses the Quantum ML Engineer
from ``energy-agents`` to execute methods owned by EnerQit.

News, evidence and case selection
---------------------------------

The official Elexon SYSWARN feed records GB margin notices published at
19:17 UTC on 8 November and 04:20 and 08:24 UTC on 9 November, indicating
1,388, 500 and 200 MW respectively. The last notice was cancelled at 09:11 UTC.
The initial event window was 06:00–11:00 UTC; later revisions concerned
08:00–11:00 UTC. These are sequential market signals, **not additive deficits,
measured outages or evidence of unserved demand**. Publication and message-issue
timestamps are stored separately. Cancellation has a null shortfall, not an
invented zero measurement.

The packaged ``enerqit/data/battery_portfolio_20261110.json`` preserves factual
metadata, source URL, retrieval date and SHA-256 of the fetched response. It
contains no copied news article or warning text. Sources examined:

* `Elexon Insights SYSWARN query
  <https://data.elexon.co.uk/bmrs/api/v1/system/warnings?publishDateTimeFrom=2026-11-08T00%3A00%3A00Z&publishDateTimeTo=2026-11-10T00%3A00%3A00Z&format=json>`_
  supplies the dated event revisions and cancellation.
* `NESO explanation of electricity margin notices
  <https://www.neso.energy/news/energy-explained-blog-electricity-margin-notice-240626>`_
  supplies interpretation of the market signal.
* `NESO GC0166 implementation update
  <https://www.neso.energy/news/gc0166-goes-live-enabling-smarter-use-limited-duration-assets>`_
  describes the MDO/MDB rollout and 5 November 2026 implementation deadline.
  Energy visibility motivates this model; this is **not** a Grid Code MDO/MDB
  calculation or compliance tool.
* `Endeavour Energy's NSW emergency-backstop rollout
  <https://www.endeavourenergy.com.au/our-network/resilience-and-emergency-planning/nsw-emergency-backstop-mechanism>`_
  was a second problem candidate. It remains a future PV flexibility study.

The GB case was selected qualitatively for recency, primary evidence,
a testable economic decision and fit to existing optimization methods. No
claim is made that it is the globally most important energy problem.
All eight assets, their fees, SOC values and the **180 MW for 3 h request are
synthetic assumptions**, deliberately distinct from the observed notice values.
No fleet was inferred from the news.

Existing work and ownership
----------------------------

``energy-data-insights`` at revision
``b5ae10d43619155519a56ab3a30cb6660db8ca55`` already contains
``docs/uk-low-wind-margin-2026.md`` and a single-battery margin-relief sensitivity.
Its inspected Elexon connector retrieves B1610 generation, which does not provide
battery SOC or SYSWARN events. This contribution adds multi-asset minimum-cost
cover, native MILP, QUBO encoding and solver comparison in EnerQit. It does not
copy that existing single-battery example or invent SCADA telemetry.

The agent uses the existing ``career_quantum_ml_engineer`` identity and its 13
research skills. A small registered-study runner in
`energy-agents PR 19 <https://github.com/julianascencio/energy-agents/pull/19>`_
lets the same agent call EnerQit's evidence, benchmark, sensitivity and handoff
tools. The default planner is a deterministic script; no LLM intelligence,
autonomous web research or quantum execution is implied by the runnable example.
The news research for this dated case was performed separately and frozen.

Reproduce
---------

From the repository root:

.. code-block:: bash

   python -m pip install -e '.[dev,docs]'
   python -m pip install -r requirements/agent-study.txt
   python -m enerqit.storage_study --output results/battery-engineer.json
   MPLBACKEND=Agg python docs/examples/plot_battery_portfolio.py
   python -m pytest tests/test_storage.py

The optional agent requirement pins an immutable Git revision, including while
the linked PR remains open. The core storage methods require only EnerQit's
normal dependencies. All runtime inputs are offline, packaged fixtures; no
credentials, paid services or operational writes are needed. To use your own
offers, construct ``BatteryOffer`` objects or replace the case dictionary, and
correct its provenance and classification. The convenience benchmark is limited
to 20 assets and 22 encoded bits for its exact certificates; the native MILP
accepts up to 64 assets. Exceeding a cap fails explicitly.

Physical model and units
-------------------------

For each asset :math:`i`, let :math:`E_i` be nominal DC MWh, :math:`h_i` state of
health, :math:`s_i` reported start SOC, :math:`s_i^{min}` minimum SOC,
:math:`r_i` reserved DC MWh, :math:`\eta_i` discharge efficiency, :math:`P_i`
AC power rating and :math:`G_i` available AC export headroom. For duration
:math:`T` hours and optional additional SOC buffer :math:`b`:

.. math::

   U_i = \max(0, E_i h_i(s_i-s_i^{min}-b)-r_i), \qquad
   a_i(T) = \min(P_i,G_i,\eta_i U_i/T).

Unavailable assets have zero capacity. The buffer withholds energy; it is not a
calibrated confidence interval. Ending SOC is calculated from reported start SOC,
so withheld energy remains unused. Capacity is health-adjusted before applying
SOC fractions. This avoids applying round-trip efficiency to discharge twice.

Selecting :math:`x_i\in\{0,1\}` incurs the whole fixed availability fee :math:`c_i`;
partial dispatch is allowed after activation. The native model is:

.. math::

   \min_x \sum_i c_i x_i \quad \text{subject to}\quad
   \sum_i a_i(T)x_i \ge P_{request}.

SciPy's HiGHS MILP solves this model with zero relative gap. A separate asset
subset enumeration verifies its optimum on the example. Physical evaluation
then allocates output proportionally to available capacity, capped at the target,
and reports ending SOC, dispatched AC MWh and any block shortfall. A hypothetical
shortfall-energy equivalent is **not** an observed energy-not-served metric.

Conservative QUBO
------------------

With MW step :math:`\Delta`, define :math:`A_i=\lfloor a_i/\Delta\rfloor` and
:math:`R=\lceil P_{request}/\Delta\rceil`. Bounded binary slack weights :math:`w`
represent every integer from zero to :math:`\sum A_i-R`. The objective is:

.. math::

   E(x,z)=c^T x+\lambda(A^T x-w^T z-R)^2,
   \qquad \lambda=\sum_i c_i+1.

Costs are nonnegative and residuals integer. Therefore any feasible encoded
solution costs less than the penalty of any infeasible encoded state. This
establishes an exact-optimization property, **not** heuristic convergence.
Rounding is conservative: encoded feasibility implies physical coverage;
physical feasibility need not imply encoded feasibility. Coarse steps can raise
the minimum fee or make the encoded problem infeasible. Exact QUBO certification
is limited to the discretized feasible set.

EnerQit uses a full symmetric matrix :math:`v^TQv+offset`. The upper-triangular
export doubles off-diagonal entries. Tests exhaust every state of a small model
against the original equation, including the constant, and cross-check twelve
seeded random native problems against independent MILP and QUBO enumeration.

Measured result and interpretation
----------------------------------

On the provided fixture:

.. list-table:: Synthetic 180 MW, 3 h block
   :header-rows: 1
   :widths: 28 26 23 23

   * - Method
     - Selected offers
     - Fixed fee (GBP)
     - Sustainable MW
   * - Power-only baseline
     - A, G
     - 7,000
     - 22.127; infeasible
   * - Native MILP and native enumeration
     - B, E, H
     - 25,000
     - 180.167; feasible
   * - Exact QUBO, 5 MW step
     - B, E, H
     - 25,000
     - 180.167; feasible

The baseline misses 157.873 MW of the synthetic request. This is not an estimate
of what happened in GB. Three ballistic simulated-bifurcation runs reached the
same optimum; annealing seed 0 reached it, while seeds 1 and 2 were £2,000 and
£3,000 above it. These are outcomes on one small, intentionally illustrative
instance, not evidence of general solver superiority.

The QUBO has 14 variables and 16,384 exact states versus 256 native asset subsets.
Budgets are 32 annealing reads × 150 sweeps and 64 bSB trajectories × 800 steps,
with the same one-bit polish. Seeds are 0, 1 and 2. Budgets are **not** matched by
runtime. Results retain construction and solver time, before-polish metadata,
encoding hash, versions, physical feasibility, encoded feasibility and native
cost gap; an infeasible candidate has no valid cost-gap comparison. No silent
repair or cherry-picking of seeds is performed.

Increasing the SOC buffer to 0.05 raises the optimum to £26,000; a 20 MW encoding
step also raises it to £26,000. A 12 h request is physically infeasible for this
fleet. Duration sensitivity holds hypothetical fees fixed; it is not a price
forecast. Native MILP is the handoff recommendation because it avoids unnecessary
capacity quantization and certifies this modest binary model.

Limits and next engineering steps
---------------------------------

This assumes one constant-power block, no charging during delivery, constant
efficiency, independent assets and no ramp, network, response-time, degradation,
qualification or intertemporal constraints. Fees are neither energy revenue nor
lifetime costs. Before an operational study, acquire validated SOC and usable
energy, grid headroom, actual fees and service rules, and add constraints relevant
to that service. The agent creates a research handoff, not dispatch authority.
The next research case should test different asset instances and scaling budgets;
these results establish neither field validity nor quantum advantage.
