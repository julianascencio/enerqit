Energy application validation lab
=================================

This lab implements five connected improvements: matched-budget scaling studies,
chronological energy-data holdouts, versioned experiment records, boundary-aware
decomposition, and measured scripted/registered-agent workflow comparisons.
It extends the existing models and examples; none of these additions establishes
quantum advantage or operational readiness.

Run the complete offline lab
----------------------------

.. code-block:: bash

   python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
   python -m enerqit.validation_study --agent --output results/validation-lab

The command writes ``firming.json``, ``firming-record.jsonl``, ``scaling.jsonl``,
``workflows.jsonl`` and ``workflow-summary.json``. Imports and gallery builds do
not download observations, submit QPU jobs or call an LLM. The default profiles
and all default costs are authored illustrative assumptions.

Matched-budget scaling
-----------------------

``enerqit.scaling.run_scaling_benchmark`` grows the existing coupled-inventory
fixture to 12, 24 and 48 bits, with paired instance and algorithm seeds. The
classical baseline uses HiGHS MILP, explicit native equalities and exact binary
product linearization: for each pair, y <= x_i, y <= x_j and
y >= x_i + x_j - 1. This is a MILP reformulation of the binary quadratic objective,
not a continuous relaxation or a claim of state-of-the-art performance.

All methods get a common feasible start obtained from constraints alone; the
synthetic planted truth is not given to the solvers. SA and simulated bifurcation
use fixed small batches with the existing common one-bit polish. The allotted
search wall time includes method preparation and polishing. A batch finishing
late cannot update the incumbent. Construction, common warm-start preparation,
search, verification and measured overrun are reported separately. Soft solver
deadlines cannot guarantee OS-level preemption. Python allocation tracing is
enabled consistently and excludes native solver memory.

A separate native reference attempts certification. When it times out, certified
gap, target-hit and time-to-target remain null. A feasible incumbent is not a
proof of optimality. If the common start already hits the certified target,
time-to-target is zero for every method. Record this rather than attributing the
warm-start result to a search algorithm. Report feasible rate, original signal
RMSE and all failed runs, not just penalized QUBO energy.

The defaults demonstrate a protocol, not statistical power. Larger studies need
held-out tuning instances, more seeds, multiple domains, and optimized native
solvers. Time budgets vary with host, warm-up and instrumentation. Compare the
same input hashes, constraints, targets and hardware before interpreting speed.

See :doc:`gallery/plot_validation_scaling` and the original :doc:`benchmarking`.

Decomposition with boundary terms
---------------------------------

``conditioned_block`` keeps the interaction of selected bits with frozen outside
bits in the block's linear coefficients, plus the outside objective constant.
It also updates equality right-hand sides. Therefore each local assignment has
the same objective and feasibility as its reconstructed full assignment.

``block_coordinate`` enumerates up to 16 bits per block, accepts only feasible,
improving full candidates before the deadline, and retains an objective trace.
Block order is seeded and changes between passes. Globally coupled constraints
may prevent improvement in small blocks. This is a local classical heuristic;
there is no distributed QPU execution or global certificate.

Historical observations and chronological holdouts
--------------------------------------------------

For an explicitly requested download of the frozen OPSD hourly source:

.. code-block:: bash

   python benchmarks/download_opsd.py --output results/opsd-source
   python -m enerqit.validation_study --agent --opsd \
     --csv results/opsd-source/time_series_60min_singleindex.csv \
     --start 2018-01-01T00:00:00Z --split-at 2019-01-01T00:00:00Z \
     --end 2020-01-01T00:00:00Z --output results/historical-validation

The download is approximately 130 MB. It writes the provider metadata and source
hashes and refuses to overwrite existing files. Raw observations are not bundled
or relicensed with EnerQit. Open Power System Data attributes the observations
to ENTSO-E Transparency; consult provider terms separately from this code's MIT
license. Citation: Open Power System Data (2020), Data Package Time series,
version 2020-10-06, https://doi.org/10.25832/time_series/2020-10-06.

The reader selects actual German solar generation, wind generation and load in
MW. It requires explicit timezone offsets, converts to UTC and rejects missing,
duplicate, unordered, irregular, negative and nonfinite input. It performs no
interpolation or silent cleaning. Source and selected-slice hashes are retained.
You can supply your own canonical CSV (timestamp, solar_mw, wind_mw, demand_mw)
without ``--opsd`` or use an explicit mapping through ``read_profiles``.

The supplied historical run uses 2018 for design and 2019 as a chronological
holdout. Both have 8,760 complete hourly rows in the downloaded source. Scaling
uses training means only: average training load is normalized to 1 MW and the
chosen wind/solar energy mix to 1.7 times average training load. The 50/50 energy
share, 3 MW battery power and 10,000 MWh search bound are scenario assumptions.
These are national aggregate shapes used in a hypothetical system, not a
co-located asset, raw weather, plant-level validation or an investment forecast.

Sparse physical storage sizing
-------------------------------

The previous dense 168-interval restriction is replaced by CSC constraint storage
with linear nonzero growth, and an explicit cap of 87,840 intervals. The original
MILP and LP relaxation remain available. The chronological study uses a physical
LP with charge mode fixed on net renewable surplus and discharge mode on deficit.

This reduction applies only because demand must be served, curtailment is free,
and there is no grid charging, export price, throughput reward or minimum-run
constraint. Simultaneous operation dissipates energy; removing it cannot require
more storage when surplus may be curtailed. Discharging into a surplus and charging
during a deficit cannot improve minimum capacity under these assumptions. The
full MILP comparison, analytic examples and independent energy audit test this
reduction. Do not reuse it for arbitrary arbitrage or reserve optimization.

Training assumes an optimized cyclic initial/final state and perfect knowledge
of the training profile. The later replay uses fixed capacity, causal greedy
dispatch and a declared 50% initial state of charge, with no reset between days.
It reports initial/final inventory, shortfall hours, unserved MWh, spill and
physical residuals. Capacity is never refitted to the holdout. Optional reserves
are explicit. Cyclic sizing is not a cold-start or future reliability guarantee.

The base ``minimum_storage`` call continues to raise on unproved solver results;
``allow_incomplete=True`` records timeout/failure status and does not accept an
unproved design. The lab uses that path and omits holdout replay when design
does not complete. Infeasibility and timeouts remain different statuses.

Degradation and configured project economics
--------------------------------------------

The holdout is replayed at beginning of life and at an assumed calendar-retention
factor (1 - annual fade)**aging years. The default 2%/year over 10 years is an
authored sensitivity, not a chemistry-calibrated degradation law. It does not
model cycling, temperature, resistance or power fade; those need separate data.

``LifecycleCosts`` requires explicit battery energy/power unit costs, renewable
capital, other initial costs and annual operating cost. It itemizes and discounts
replacement energy costs at declared years. The runnable example uses assumed
EUR 200,000/MWh, EUR 150,000/MW, EUR 4 million renewable capital, EUR 250,000
other capital, EUR 100,000 annual opex, 20 years, 6% discount and a 70% energy-cost
replacement in year 10. These are not market prices. Tax, inflation, salvage,
revenue and unconfigured costs are excluded. Replacement cash flows do not imply
a simulated 20-year dispatch or a bankable lifecycle design.

See :doc:`gallery/plot_chronological_validation`.

Unified evidence records
-------------------------

``ExperimentRecord`` uses strict JSONL schema version 1.0 with input hash, method,
seed, environment, status, independent feasibility, objective, timings, resources,
cost basis, metrics and provenance. Unknown values stay null. Timings use seconds,
memory uses bytes with an explicit scope, and costs require a declared currency
and basis. The module never invents paid compute costs from elapsed time.

Execution categories are classical, quantum_inspired, circuit_simulation and
quantum_hardware. Hardware records require device and job identifiers. The schema
can carry embedding, transpilation, queue, execution and readout times in
``timings_s``; they remain absent/unknown until measured. Metadata alone does not
authenticate a hardware claim. This contribution runs entirely on CPUs.

Workflow evaluation
--------------------

``compare_firming_workflows`` runs the same four callbacks directly and through
the installed ``career_quantum_ml_engineer`` registered study. Tool calls are
counted at callback invocation. Three fixed-seed repetitions measure wall time,
feasible completion, failures and semantic-output repeatability. Exceptions are
retained as failed records. Human effort stays null unless explicitly reported.

The existing agent planner is scripted and offline; this tests its orchestration,
not a live LLM, autonomous scientific judgment or reduced engineering time. See
:doc:`gallery/plot_workflow_evaluation`. ``evaluate_workflows`` also accepts custom
callables, enabling failure injection and future separately labeled live studies.

Sources and scientific status
-----------------------------

* `JRC Outlook Report on Quantum, JRC148269 (30 October 2026)
  <https://publications.jrc.ec.europa.eu/repository/handle/JRC148269>`_ motivates
  application evaluation. It is not evidence for these implementation results.
* Alex G. Lee, *Quantum Computing Beyond the Hype: From Scientific Promise to
  Real-World Applications* (user-provided 2026 outlook) motivated this review.
  It explicitly separates proposed agentic integrations from demonstrated JRC
  outcomes. Its copyrighted text is not redistributed.
* `SciPy milp documentation
  <https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html>`_
  documents HiGHS, sparse constraints, time limits and solver statuses.
* `OPSD 2020-10-06 metadata
  <https://data.open-power-system-data.org/time_series/2020-10-06/>`_ identifies
  the historical observation fields, provenance and processing.

Code, tests and documentation were AI-authored. Automated analytic and numerical
checks are implementation evidence; independent human scientific review and
plant-level field validation remain outstanding. No quantum performance or
commercial benefit is established by this lab.

Recorded implementation evidence
---------------------------------

The `dated validation note
<https://github.com/julianascencio/enerqit/blob/main/validation/readiness-20261113.md>`_
links the verification scope. The historical scenario's 75.99 MWh design leaves
9.28 MWh unserved across 16 held-out hours; the declared calendar-fade sensitivity
increases this to 21.79 MWh across 28 hours. These are hypothetical scaled-system
results, not reliability measurements for a real plant.

Download the recorded :download:`historical study <../../../validation/historical-firming-20261113.json>`,
:download:`72 benchmark records <../../../benchmarks/results/readiness-scaling-20261113.jsonl>`
and :download:`workflow records <../../../benchmarks/results/workflow-evaluation-20261113.jsonl>`.
The larger reference MILPs timed out, so their optimality gaps remain unknown.
Solver certification uses floating-point tolerances, not exact arithmetic.
