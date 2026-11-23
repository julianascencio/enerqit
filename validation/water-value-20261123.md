# Terminal water value validation — 23 November 2026

AI-authored implementation, tests, documentation and source synthesis. Independent
human review and validation on real assets are outstanding. Automated checks are
not scientific approval or operational authorization.

## Recorded inputs and execution

- EnerQit base: b8dbbf54bcba6f0f5ab4ae22cbf100853ae6f885.
- Actual installed energy-agents: 9a8a56b3be12e734183a0350600bf874bdee8ff0.
- Inspected EDI: e72d9d822b442f6392c80ce12dfc62f738f51ddd; no connector reused.
- Fixture: `enerqit/data/water_value_20261123.json`, authored synthetic MIT inputs.
- Fixture SHA256: 9f5a032dbbd05d4a8472097ae55f69d2bf7ce01054cca1971222b2949f5dd7a3.
- NVE publication 18 November covers 9–15 November; context only. No raw source
  response archived: source-response hash is explicitly null. No provider data,
  full article, or paper redistributed. Candidate/source ledger is in
  `research/water-value-selection-20261123.md`.
- Deterministic LP; no stochastic study seed. Independent reference seeds 0–5.
- Environment and actual five-entry agent trace (four callbacks then finish) are
  in `benchmarks/results/water-value-20261123.json`. Python 3.12.14, NumPy 2.3.5,
  SciPy 1.17.0. UTC data intervals; user-facing date Atlantic/Canary.

## Verification

Executed on this contribution:

```bash
python -m ruff check .
python -m pytest --cov=enerqit
python -m enerqit.water_value_study
MPLBACKEND=Agg OPENBLAS_NUM_THREADS=1 python ci/run_examples.py --output results/examples
MPLBACKEND=Agg OPENBLAS_NUM_THREADS=1 python -m sphinx -W --keep-going -b html docs/sphinx/source docs/_build/html
python -m build
```

366 tests pass, 87% aggregate coverage; all 26 offline examples pass. Strict
Sphinx build succeeds, and both wheel and sdist build. No separate type-check
command is configured. The new figure was visually inspected. GitHub exact-head
CI is recorded in the PR, separately from these local results.

Six seeded independent exhaustive enumerations agree with LP objectives within
1e-8 EUR on tiny integer water schedules. Tests cover the zero/default valuation,
terminal knot optimum, equal slopes, nonconcave/negative/nonfinite/invalid knots,
insufficient domain and invalid adapter type. Physical water residuals are zero
in the published three-hour policy comparison. Existing hydro infeasibility and
negative-price tests remain in the full suite.

## Results and limits

| Policy | Gross energy EUR | Final m3 | Common cash + terminal EUR |
|---|---:|---:|---:|
| Cash-only | 1373.400 | 0 | 1373.400 |
| Fixed 60000 m3 floor | 613.125 | 60000 | 1913.125 |
| Concave valuation | 1103.625 | 40000 | 2303.625 |

All policies are rescored using the same assumed curve. The 930.225 EUR increase
is a scenario decision score; immediate gross energy value falls by 269.775 EUR.
It is not realized revenue, profit, savings or bankable fair value. No quantum,
quantum-inspired or circuit execution is warranted for this continuous concave LP.

Valuation scales 0/0.5/1/2 and inflows 0/5/10 m3/s expose scenario sensitivity;
they are not empirical confidence intervals. Zero valuation restores depletion.
Single-run construction-plus-solver timings span 3, 24, 168 and 8760 intervals;
timings are machine-dependent, not a comparative speed claim. The annual-scale
run took 0.423 s locally.
The formulation adds one variable and one inequality per curve segment.

Constant head, perfect within-window foresight and unlimited bypass remain.
Next: estimate continuation values from approved pre-decision data, freeze the
estimation, then validate on untouched later prices/inflows and review physical
release/spillway constraints. No field dispatch or deployment occurred.
