# Probability ambiguity validation — 15 November 2026

Base: 2c7f9c1fcf9432f11c6321e3d726b4febb10c58e.
Agent: c8a61091683856c890a5059d0ff6e3d4bd94a445 (actual Git install recorded).

Executed: 233 pytest tests passed, 87% total coverage; Ruff passed; all 18 gallery
examples passed; Sphinx warnings-as-errors passed after correcting heading lengths;
wheel/sdist build and git diff checks passed. No type-check command is configured.
One environment anyio pytest deprecation warning remains. Figure visually checked.

Independent tests: two-state analytic worst-case expectation at five radii;
three-state exhaustive simplex lattice; zero-probability support; invalid radius
and probability mass; nominal/robust procurement; infeasible offers; actual four
registered agent stages. All methods are classical CPU execution. LP feasibility
is audited separately from solver status. No statistical confidence is inferred.

Synthetic four-hour case: nominal chooses 60 MW / EUR 6,000, EENS 17.44 MWh.
At TV radius .05 this offer has worst EENS 25.44 MWh and fails the 20 MWh target;
80 MW / EUR 8,000 passes with 12.72 MWh. Exact offer optimum is conditional on the
finite supplied set, within solver tolerance. No realized savings claimed.
Results, source/input hashes and versions: benchmarks/results/robust-adequacy-20261115.json.

AI-generated methods and documentation. Human scientific review, support/radius
calibration and real asset validation remain pending. Current news motivates the
one-day-old backlog gap; no numerical input is a measured GB/European value.
This records local validation only; see the PR for exact-head remote CI. Not a
merge or deployment record.
