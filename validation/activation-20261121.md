# Bidirectional battery readiness — 21 November 2026

AI-authored proposed contribution, not merged or deployed. Independent human
scientific review and field calibration remain pending.

## Reproduction and evidence

Base: `f8ab496eb9c53c048d541b95ef5b9c7685df97a2` (current main inspected).
Actual installed/executed agent: `f8150df9a4272bf2b97042a61b3b785a92450057`.
EDI capabilities inspected: `e72d9d822b442f6392c80ce12dfc62f738f51ddd`;
no connector/data/code reused. PRs 14 and 15 are separate, untouched work.

- Candidate selection: `research/activation-selection-20261121.json` (five cases).
- Fixture: `enerqit/data/activation_20261121.json`, entirely synthetic, MIT.
- Result: `benchmarks/results/activation-20261121.json`; SHA256 of exact input
  bytes, package versions, actual VCS agent installation and tool trace included.
- Method deterministic, no study RNG. Independent test seeds 0 through 7.
- Primary news checked by web retrieval, no provider article redistributed or
  raw HTTP hash invented. News dates and forecast event horizon are distinct.

```sh
python -m pip install -e '.[dev,docs,quantum]' -r requirements/agent-study.txt
python -m enerqit.activation_study
python docs/examples/plot_storage_headroom.py
python -m pytest --cov=enerqit --cov-report=term-missing
python -m ruff check .
python ci/run_examples.py --output results/examples
python -m sphinx -W --keep-going -b html docs/sphinx/source docs/_build/html
python -m build
```

## Scientific checks and interpretation

24 new tests: eight seeded independent state-variable LP comparisons, all corner
replays at both admissible boundaries, random interior paths, unequal durations,
charge/discharge losses, exact singleton interval, zero-capacity/zero-power,
infeasible power versus energy, inaccessible/short preparation, invalid inputs
and actual registered four-tool agent execution.

For 40 DC MWh / 30 AC MW with 0.9 efficiencies, initial admissible energy is
13.222222..22 MWh; LP endpoint discrepancy is zero in the recorded run.
Minimum usable capacity ignoring power is 31.222222 MWh. Full SOC fails the
20 MWh absorption probe; half-full and prepared track it. Empty SOC misses
3.8 MWh of discharge on this probe (11.9 on the smaller-charge test trajectory).
Preparing full to 22 DC MWh exports 16.2 AC MWh in at least 0.54 hours.
EUR81 is only an assumed throughput fee, not total cost, revenue or savings.
Power-only screening would accept all these states and miss their energy limits.

Capacity, efficiency, activation-radius and preparation-time sensitivities
include infeasible outcomes. Scaling spans 2 to 100000 intervals. Function timers
include array conversion but exclude dataclass construction; single-run timings
are not a controlled speed comparison. LP reference explicitly caps n at 8.
Monotonicity proves the box certificate; no claimed research/quantum novelty.
No quantum-inspired, circuit or QPU algorithm is appropriate or executed.

## Validation record

298 tests passed, 87% overall coverage; all 22 offline gallery scripts passed.
Ruff, source/wheel build and clean warnings-as-errors Sphinx build passed.
No separate repository type-check command is configured. One external AnyIO
pytest plugin deprecation warning remains; no new test warnings suppressed.
The generated figure was inspected. Early concurrent validation processes were
killed under resource contention; sequential reruns were used. Stale ignored
gallery files from a different local branch were removed before the clean build.
Final published-head GitHub checks are recorded separately in the PR description.

The agent preserves `human_review_required=true` and `execution_authorized=false`.
Box independence can be conservative; bounds have no calibrated probability.
No ramps, standby loss, thermal/network constraints, competing obligations or
terminal target. Preparation assumes permitted import/export and energy access.
Next obtain licensed asset evidence and independently review physics, uncertainty
and opportunity costs. No equipment control or market transactions performed.
