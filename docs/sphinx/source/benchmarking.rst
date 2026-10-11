Benchmark protocol
==================

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
