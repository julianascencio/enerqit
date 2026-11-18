# Shared export validation — 17 November 2026

Base: 2c7f9c1fcf9432f11c6321e3d726b4febb10c58e.
Actual agent installation: c8a61091683856c890a5059d0ff6e3d4bd94a445.

Local checks: 231 tests passed, 87% coverage; all 18 gallery examples passed;
Ruff, wheel/sdist, diff check and Sphinx warnings-as-errors passed. One external
pytest-plugin deprecation warning remains. No type-check command is configured.
The figure was inspected. Inputs, source hashes or retrieval failures, package
versions, four executed tools and results are in the benchmark JSON.

Independent references: exhaustive binary allocation for integral three-period
flow instances, a hand-computed EUR 12,500 feasible upper bound, variable-duration
energy accounting, zero budget, negative prices and invalid data tests. The
physical audit recomputes power, energy and shared connection inequalities.

Synthetic results: independent requested value EUR 14,500 with 50 MW overload;
clipped feasible value EUR 9,500; coordinated value EUR 12,500. Difference EUR
3,000 is gross scenario value before costs, not realized profit. Sensitivities
cover connection 25/50/75/100 MW, energy multipliers .5/1/1.5 and horizon scaling
6/24/168 intervals. No random seed, quantum method or hardware execution.

EnBW English/German primary pages conflict on 41/46 MW. Neither rating is used,
and the actual site's connection is unknown. Primary publication date was not
verified; secondary coverage is dated 17 November. All numerical inputs are
synthetic MIT fixtures. No external connector or third-party observations reused.

Perfect-price discharge-only model excludes charging, head-dependent hydraulics,
fees, degradation, terminal values and reserve obligations. AI-authored with
human scientific review and site calibration pending. This is a local validation
record, not remote CI completion, merge or deployment evidence; see PR checks.
