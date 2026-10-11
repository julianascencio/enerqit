# Benchmarks

Run `python benchmarks/run_benchmarks.py` after installing the package.
`results/reference.jsonl` contains a measured reference run from the delivery
environment; `results/summary.md` summarizes it. Times are host-specific.

Three 12-bit instances × (two exact baselines + three seeds for two heuristics)
produce 24 records. No result is filtered out for failure. Feasibility, exact
energy gap, original signal error, truth recovery, budgets, timings and versions
are recorded. These small synthetic instances do not test commercial-scale
performance and are not an equal-runtime comparison.

Native feasible enumeration is the stronger formulation-aware baseline here.
Before making any advantage claim, add larger constrained instances, tuned
native MILP/MIQP/CP-SAT/decomposition solvers, real held-out plants and matched
end-to-end cost or time-to-target experiments. ML models should only be compared
under clearly specified training-data availability and domain shift.
