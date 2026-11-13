# Application validation lab - 2026-11-13

AI-authored implementation inspired by JRC148269 and the user-provided Alex G. Lee
outlook. Independent human scientific review remains outstanding.

## Recorded checks

- Ruff: passed.
- Full suite: 147 passed, overall measured coverage 86%; optional quantum SDK and
  pinned energy-agents integration were available.
- Final focused validation suite after record/timeout refinements: 29 passed.
- All 15 gallery examples executed; three new plots visually inspected or checked
  through the generated gallery.
- Warning-as-error Sphinx build passed; wheel and source distribution built.
- An environment pytest plugin emits a deprecation warning; no test failed.

## Historical holdout

Run with the explicit CSV command in docs/sphinx/source/validation_lab.rst.
Raw observations are not redistributed. Source hash and training-only scaling are
in historical-firming-20261113.json. The source is OPSD time_series 2020-10-06,
DOI 10.25832/time_series/2020-10-06, underlying provider ENTSO-E Transparency.

- 2018 training: 8,760 hours. 2019 holdout: 8,760 hours. No missing selected values.
- Hypothetical national-shape scenario, 1 MW average training demand, 1.7x renewable
  energy, 50/50 wind/solar energy shares and 3 MW AC battery power.
- Sized usable DC capacity: 75.987228 MWh.
- Fixed-design 2019 replay: 9.281757 MWh unserved, across 16 hours.
- Assumed 2% annual calendar fade for 10 years: 62.087098 MWh retained capacity;
  21.791875 MWh unserved across 28 hours on the same holdout.
- Sparse annual constraint arrays: 1,401,660 bytes, 105,124 nonzeros; this is not
  process peak memory.
- Initial annual full MILP attempt reached its 30-second limit without proving
  optimality. The restricted physical net-balance LP completed and passed the
  independent energy audit. No result from that timed-out attempt was accepted.

The aging case is a sensitivity, not measured battery degradation. The configured
cash flows are authored assumptions, not prices, realized savings or revenue.

## Matched-budget benchmark

Command: run_scaling_benchmark(groups=(4,8,16), instance_seeds=(42,43),
seeds=(0,1,2), seconds=0.2, reference_seconds=5.0).

72 contender records are retained in benchmarks/results/readiness-scaling-20261113.jsonl.
All have independently feasible incumbents, including shared warm starts. Statuses:
54 feasible, 6 optimal, 12 timeout. Timeouts remain visible even when the fallback
incumbent is feasible. The two 12-bit references achieved solver certification;
the 24/48-bit references timed out. Their target/gap metrics remain null.
Soft-deadline overruns are recorded; later candidates are discarded.
The 72 rows are paired runs, not 72 independent problem instances.
This small study cannot establish solver or quantum advantage.

## Workflow measurement

The installed registered agent (e077b5f240852c7fe28c4de2ed530a52f65e8347)
and the direct script each completed three repeats with identical semantic
outcomes and four actual callbacks. Timings and input/output hashes are stored
in benchmarks/results/workflow-evaluation-20261113.jsonl.
The planner is scripted/offline. Human effort is unmeasured. No claim of
engineering-time savings, autonomous science or quantum acceleration is made.
