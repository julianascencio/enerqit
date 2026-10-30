Benchmark protocol
==================

Published reference results
---------------------------

The recorded synthetic reference contains three 12-bit instances and three
seeds per heuristic. All four methods ran on a classical CPU. These are the
recorded results, not a fresh benchmark executed in your browser.

.. list-table:: Fixed-budget reference; median solver time
   :header-rows: 1
   :widths: 38 15 15 16 16

   * - Method
     - Runs
     - Seconds
     - Feasible
     - Optimum hits
   * - Exact QUBO enumeration
     - 3
     - 0.001637
     - 3 / 3
     - 3 / 3
   * - Native grouped enumeration
     - 3
     - 0.008120
     - 3 / 3
     - 3 / 3
   * - Simulated annealing
     - 9
     - 0.028897
     - 9 / 9
     - 4 / 9
   * - Ballistic simulated bifurcation
     - 9
     - 0.026058
     - 9 / 9
     - 9 / 9

**Exact enumeration is fastest on these small instances.** The budgets are
not matched by runtime or evaluations. These results do not establish a
quantum-inspired speedup, scaling advantage or superiority over modern native
mixed-integer methods.

Download the :download:`raw reference records <../../../benchmarks/results/reference.jsonl>`
and :download:`recorded environment <../../../validation/environment.json>`.
The :doc:`coupled benchmark example <gallery/plot_coupled_benchmark>`
shows the comparison in code and plots.

Reproduce and interpret
-----------------------

Run ``enerqit benchmark --output results/benchmark.jsonl``. The included
reference run uses three independently seeded 12-bit synthetic instances and
three heuristic seeds per instance: 24 records including the two exact
baselines. Fixed budgets are SA 32 reads / 120 sweeps and bSB 64 agents / 800
steps. Both receive common one-bit polishing. These are transparent initial
settings, not an equal-runtime or equal-evaluation comparison.

Each record contains the seed, QUBO hash, environment versions, construction
time, solver time, energy, absolute certified energy gap, feasibility, original
signal RMSE, true bit recovery and optimum-hit status. The native group solver
certifies only the explicitly feasible domain; unconstrained QUBO enumeration
certifies the penalized binary objective. These certificates can disagree if
penalties are insufficient. Original physical residual and feasibility take
priority over penalized energy when selecting engineering outcomes.

Truth recovery and optimizer success are different. Multiple configurations
can fit noisy observations similarly; the planted truth need not minimize the
noisy objective. A low energy gap is therefore not an uncertainty statement.

For a commercial evaluation, expand to increasing groups/choices, multiple
constraint densities, sensor bias, weather shifts, missing channels, parameter
confounding and real held-out sites. Tune on a training set, freeze parameters,
and compare time-to-target, feasible success rate, interval coverage and total
cost with paired instances and adequate repeated seeds. Include strong native
MILP/MIQP/CP-SAT or decomposition methods at scale. They are not yet bundled.

Set a business acceptance gate before optimization: correct configuration or
bounded uncertainty, useful equipment curve over a declared domain, reduced
expert effort, and paid study conversion. Quantum-inspired adoption requires an
observable improvement at matched accuracy, constraints and end-to-end budget.
No such advantage has been established by this small synthetic benchmark.

Dense construction requires O(m*n²) work for m observations and n candidates;
the QUBO occupies O(n²) memory. Dense bSB costs approximately O(steps*agents*n²),
while exhaustive solving costs exponentially in bits and grouped enumeration
exponentially in groups. Decomposition, sparse structure and accelerator kernels
are research extensions, not current scalability claims.
