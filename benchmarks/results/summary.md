# Synthetic benchmark results

Three 12-bit instances, three seeds per heuristic; fixed budgets, not equal runtimes.

| Method | Runs | Median solver seconds | Feasible | Exact optimum hits |
|---|---:|---:|---:|---:|
| ballistic_simulated_bifurcation | 9 | 0.026058 | 9/9 | 9/9 |
| exact | 3 | 0.001637 | 3/3 | 3/3 |
| group_exact | 3 | 0.008120 | 3/3 | 3/3 |
| simulated_annealing | 9 | 0.028897 | 9/9 | 4/9 |

Exact enumeration is faster on these small instances. This benchmark does not establish quantum advantage, scaling advantage, or superiority over modern native mixed-integer methods. All solvers ran on classical hardware.
