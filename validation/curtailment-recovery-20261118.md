# Curtailment recovery — 18 November 2026

AI-authored implementation, tests and documentation; independent human scientific review and field validation remain pending. These are local checks, not remote CI or deployment evidence.

Base: `2c7f9c1fcf9432f11c6321e3d726b4febb10c58e`. Agent executed at `c8a61091683856c890a5059d0ff6e3d4bd94a445`, using the existing four registered scientific-study callbacks and scripted planner. This is tool orchestration, not an autonomous LLM decision or quantum execution. No integration changes required.

Local Python 3.12 checks:

- Ruff passed; no separate repository type checker is configured.
- 236 tests passed, total statement coverage 87%. One external AnyIO pytest-plugin deprecation warning; no failing test. Twelve original new tests plus four input-contract cases.
- Five independently formulated continuous inventory LP references (seeds 0..4, variable durations) agree with greedy recovered energy within pytest numerical tolerance. Physical export feasibility and disjoint charging/discharging verified.
- All 18 gallery scripts passed via `ci/run_examples.py`.
- Standalone new example and `python -m enerqit.curtailment_study` passed.
- Sphinx warnings-as-errors HTML build passed; gallery figure visually inspected.
- Wheel and source distribution built; `git diff --check` passed.

Numerical inputs are authored synthetic MIT fixtures; source news is context only. Raw source response hash, input hash, installed agent revision, package versions, capacity/efficiency/headroom sensitivity and runtime scaling are in `benchmarks/results/curtailment-recovery-20261118.json`. Deterministic replay needs no RNG seed; LP tests use 0..4. The source body is not redistributed. UTC provenance; elapsed-hour synthetic intervals.

For 20 MW / 40 MWh DC, 40 MWh captured becomes 32.4 MWh exported plus 7.6 MWh losses. No battery: zero recovery. At 20 MWh capacity: 18 MWh recovered; 80 MWh does not improve on 40 MWh. No later headroom: zero recovered export and 36 MWh DC terminal inventory. At an assumed flat EUR 50/MWh, gross additional export value is EUR 1620; this excludes costs and is not realized savings. No quantum comparison is warranted for this linear inventory problem.

EDI generation contracts were inspected at `fc63c5f97e6513e7f290340ddfdce0b80962644a` (`docs/generation-connectors.md` blob `223e8ea0184e7c5224b146b9d91e4fe16ae73f9f`). REE's aggregate calendar-period generation cannot supply plant-level available output/limits/permissions; no connector, separately licensed code or provider data was reused.

Limits: no calibrated site series, market optimization, degradation, thermal limits, network stability model or investment recommendation. Charging permission and licensed interval observations are next prerequisites. Sensitivity is not a probability distribution or confidence interval. Constant efficiencies and one device only.
