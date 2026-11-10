Batch flexibility with deadlines and grid headroom
==================================================

The engineering question is precise: **when should each fixed-work industrial
batch start so that the energy bill is minimized, every deadline is met, and the
site stays below its grid import ceiling in every declared load scenario?**
Shifting all jobs into cheap hours can create a rebound peak. A cheaper but
infeasible schedule is not an operational saving.

The :doc:`runnable gallery <gallery/plot_batch_flexibility>` uses the existing
Quantum ML Engineer and EnerQit-owned methods. Its default planner follows an
explicit scripted sequence, not LLM reasoning. News research was performed
separately and frozen; rerunning the gallery makes no network request.

Dated evidence and why this case
--------------------------------

The primary trigger is the IEA's `Spain review announcement of 5 November 2026
<https://www.iea.org/news/accelerating-electrification-can-unlock-the-full-benefits-of-spains-renewables-leadership>`_.
It identifies electrification, grid modernisation and flexibility as priorities
for extending the benefits of renewable generation. The scheduling problem here
is our engineering interpretation of that challenge, not a model published by
the IEA. No reported national figure is used as a site parameter.

The 10 November run first searched the previous 72 hours, then extended to seven
days to find a new implementable case. Four primary-source candidates were compared:

.. list-table:: Research selection
   :header-rows: 1
   :widths: 28 20 52

   * - Candidate
     - Publication date
     - Decision
   * - IEA Spain electrification review
     - 5 November
     - Selected: industrial energy cost and grid headroom give a bounded,
       falsifiable scheduling decision; operational inputs remain missing.
   * - `IEA Renewables 2026 announcement
       <https://www.iea.org/news/energy-security-concerns-spur-faster-renewables-growth-across-a-widening-constellation-of-countries>`_
     - 6 November
     - Broad investment/integration importance; needs a regional dataset before
       a useful system-level study. Backlog.
   * - `Ember grid modernisation guide
       <https://ember-energy.org/latest-insights/building-a-grid-for-the-age-of-power/>`_
     - 5 November
     - Network solutions are relevant, but require actual topology and ratings.
       Backlog for power-flow-aware optimization.
   * - `Banque de France data-centre price-signal analysis
       <https://www.banque-france.fr/en/publications-and-statistics/publications/data-centres-and-energy-environmental-cost-faulty-price-signal>`_
     - 4 November
     - Geographic workload placement is interesting; migration, latency and
       tariff evidence are insufficient. Backlog.

The `Ember data-centre flexibility report
<https://ember-energy.org/latest-insights/data-centres-for-grids-the-potential-impact-of-flexibility/>`_
is dated **29 October**, twelve days before this run. Search freshness labels
were misleading; it is background, not a new November event. The GB margin/battery
portfolio case was excluded because EnerQit PR 2 was already merged.

``research/news-ledger.json`` preserves selection rationale, backlog and
previous work. ``enerqit/data/batch_flexibility_20261110.json`` packages the case,
source dates/URLs and available response hashes. No source page or article is
redistributed. News supports motivation; **all prices, jobs, profiles, limits,
load scenarios and the example horizon are synthetic assumptions**.

Repository awareness and agent execution
-----------------------------------------

Energy Data Insights revision ``b5ae10d43619155519a56ab3a30cb6660db8ca55`` was
inspected before choosing inputs. Its REE connector provides daily/monthly/yearly
regional generation, not hourly site tariffs or job windows. Its REE BESS screen
and HVAC counterfactual analysis answer different questions. None can fill the
missing industrial profiles and deadlines. No fabricated observed dataset or
unnecessary network connector is introduced.

The existing ``career_quantum_ml_engineer`` role runs four registered tools:
``inspect_evidence``, ``benchmark_methods``, ``assess_sensitivity`` and
``prepare_handoff``, then ``finish``. The adapter already exists in merged
energy-agents main, so no second integration PR is needed. The optional dependency
is pinned to ``832f4117f95ac3137c63eace389e56cdc2c075fe``; the benchmark records
installed package version and source revision when available. All new numerical
methods, scenario experiments and the gallery live in EnerQit.

Reproduce offline
------------------

.. code-block:: bash

   python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
   python -m enerqit.flexibility_study --output results/flexibility-engineer.json
   MPLBACKEND=Agg python docs/examples/plot_batch_flexibility.py
   python -m pytest tests/test_flexibility.py

The JSON output includes the actual agent trace, source/input hashes, environment,
all solver outcomes and timings, sensitivity, scaling and a handoff. Core methods
in ``enerqit.flexibility`` work without the optional agent package. Construct
``BatchJob``, ``GridScenario`` and ``BatchProblem`` for other inputs. The packaged
``flexibility_sensitivity`` experiment is specifically for this six-slot case
and its Batch-C deadline; generic numerical methods do not assume those names.

Input contract and physical accounting
--------------------------------------

Profiles are incremental **AC MW at the site import meter**. Prices are EUR/MWh
and may be negative. The UTC start has an explicit zero offset; slots have fixed
positive duration in hours. Release is inclusive and completion deadline is
exclusive: a job starting at :math:`k` with :math:`L_j` slots must satisfy
:math:`r_j\le k` and :math:`k+L_j\le d_j`. A job runs exactly once, contiguously,
with its full profile. All work finishes inside the modeled horizon.

Every scenario supplies inflexible baseline demand and an AC import ceiling for
every slot. One advance schedule must satisfy all scenarios. There is no ability
to adapt its starts after learning which scenario occurs. For incremental
profile :math:`p_{j,\ell}`, slot duration :math:`\Delta t`, prices :math:`\pi_t`
and binary allowed-start choice :math:`x_{j,k}`:

.. math::

   D_t(x)=\sum_{j,k}p_{j,t-k}x_{j,k},\qquad
   \min_x\;\Delta t\sum_t\pi_t D_t(x),

.. math::

   \sum_{k\in K_j}x_{j,k}=1,\qquad
   B_{s,t}+D_t(x)\le G_{s,t}\quad\forall s,t.

Out-of-profile indices contribute zero. Inflexible energy charges are constant
with respect to this decision and excluded from the reported incremental bill.
Taxes, demand charges, product value and emissions are not modeled. Cheap hours
do not by themselves establish renewable absorption or avoided curtailment.

The scenario envelope :math:`H_t=\min_s(G_{s,t}-B_{s,t})` is exact for these
constraints on one common schedule. It is not a probabilistic risk bound. A
negative envelope makes the native problem infeasible even with no batch running.

Native and encoded methods
---------------------------

``solve_batch_milp`` uses `SciPy/HiGHS MILP
<https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html>`_
with native MW inequalities and zero requested relative gap. Timeouts or failed
solver statuses are not presented as optimal. ``enumerate_batch_schedules``
independently enumerates actual start tuples and reconstructs demand directly
from each profile. Both use ``evaluate_schedule`` to check every scenario,
completed work and energy cost outside the penalized objective.

For a MW encoding step :math:`\delta`, the QUBO rounds each profile contribution
**up** and available headroom **down**. Each binding capacity row becomes
:math:`A_tx+w_t^Tz_t=R_t` with nonnegative binary-encoded unused capacity. Rows
that cannot bind under any one-start-per-job selection are omitted. This keeps
the fixture at 14 start bits plus two slack bits. Integer equality constraints
retain the actual one-hot and encoded capacity requirements.

Each job's start costs are shifted by its minimum :math:`m_j`. Let
:math:`c'_{j,k}=c_{j,k}-m_j\ge0` and
:math:`\lambda=1+\sum_j\max_k c'_{j,k}`. For all equality rows :math:`Cx=h`:

.. math::

   E(x,z)=\sum_jm_j+c'^Tx+\lambda\lVert C[x,z]-h\rVert_2^2.

Every feasible state has shifted cost at most the sum of per-job ranges.
An infeasible integer residual costs at least :math:`\lambda`. Thus an exact
encoded optimum is feasible whenever that encoded model admits a feasible
state, including with negative prices. This does not guarantee convergence of
heuristics. Conservative rounding can exclude a physically feasible schedule;
encoded optimality is not generally native physical optimality.

The existing full symmetric QUBO convention, exact solver, ordinary classical
simulated annealing and quantum-inspired ballistic simulated bifurcation are
reused. No QPU is invoked. Invalid one-hot candidates are reported without
inventing starts, removing work or assigning a meaningful cost gap. Physical
and encoded feasibility remain separate even when a valid schedule has a bad
slack assignment.

Measured synthetic result
--------------------------

.. list-table:: Same 9 MWh of completed work
   :header-rows: 1
   :widths: 34 22 22 22

   * - Schedule
     - Incremental cost (EUR)
     - Largest import violation (MW)
     - Feasible in both scenarios
   * - Price-only optimization
     - 105
     - 5
     - No
   * - Nominal-only MILP
     - 390
     - 1
     - No
   * - Two-scenario MILP and native enumeration
     - 525
     - 0
     - Yes
   * - Exact QUBO at 1 MW resolution
     - 525
     - 0
     - Yes

The robust schedule starts A/B/C/D in slots **1/3/4/1** (10:00/12:00/13:00/10:00
UTC), with all completion deadlines met. The **EUR 135** premium over nominal
planning is the modeled cost of meeting the extra scenario, not realized savings
or the value of an actual reliability service.

Exact native enumeration examines 144 schedules; exact QUBO checks 65,536 states.
For this fixture, all three seeds (0/1/2) of SA and bSB find the same optimum.
SA uses 32 reads × 150 sweeps, bSB 64 trajectories × 800 steps, with the same
one-bit polishing option. These are fixed iteration budgets, not equal-runtime
budgets. Before-polish metadata and every returned candidate are retained.

With replicated cohorts, the 8-job/32-bit example has seed-0 SA gap EUR 80 and bSB
gap zero; the 16-job/62-bit example has gaps EUR 300 and EUR 200 respectively.
These modest synthetic scaling experiments show imperfect heuristic outcomes,
not general performance guarantees. Construction time, solver time, native
combination counts and dense matrix bytes are recorded. Native MILP is the
recommended handoff method because it avoids artificial quantization and
certifies the stated native problem.

Sensitivity and limits
-----------------------

* Adding 0.25 MW baseline demand in all slots raises the optimum from EUR 525 to
  EUR 800; at 1.25 MW additional baseline demand the problem is infeasible.
* Tightening Batch C's completion boundary from slot 6 to slot 4 makes the robust
  problem infeasible. Jobs are never silently deleted or postponed past the horizon.
* Changing the QUBO step from 1 MW to 2 MW raises its feasible optimum to EUR 800.
  It remains physically feasible but excludes a cheaper native schedule.

The native compiler limits inputs to 32 jobs, 168 slots, 32 scenarios and 512
start choices. Dense QUBO construction caps at 256 variables. Native exact
search caps at one million start combinations; generic exact QUBO defaults to
22 bits. The scaling study does not enumerate its 32- or 62-bit models.

This is a deterministic scheduling prototype. It omits process precedence,
ramp/thermal constraints, staffing, uncertain job duration, distribution power
flow, taxes and actual grid-service qualification. A declared scenario set has
no calibrated probability. Before a pilot, obtain metered job profiles, validated
deadlines, contracted import ceilings, actual tariffs and baseline forecasts;
then test unseen operating days and integrate the missing plant constraints.
No dispatch authority or quantum advantage is claimed.
