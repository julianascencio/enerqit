# Network-curtailment validation — 10 November 2026 (UTC)

AI-generated code, tests, synthetic fixture and documentation; automated review
only. Human scientific review and real-network validation remain outstanding.
Base EnerQit commit: `2847f95124c6f45b98d403e444877ca18451ab32`.
Actual installed energy-agents Git commit:
`832f4117f95ac3137c63eace389e56cdc2c075fe` (also recorded from direct_url.json).
No role adapter change was necessary; all four registered callbacks executed.

Executed locally on Python 3.12:

- `python -m ruff check .`: passed.
- `python -m pytest --cov=enerqit --cov-report=term-missing`: 84 passed;
  90% overall coverage. One pre-existing environment warning from the installed
  anyio pytest plugin about a deprecated pytest alias; no failed tests.
- `python ci/run_examples.py --output results/examples`: all 10 examples passed.
- `python -m sphinx -W --keep-going -b html docs/sphinx/source docs/_build/html`:
  passed; all 10 gallery examples executed. First comparison figure visually inspected; all three generated successfully.
- `python -m build`: wheel and sdist built successfully.
- Built wheel installed with `--no-deps --target /tmp/enerqit-network-wheel`;
  `python -m enerqit.network_study` executed outside the checkout with that target
  on PYTHONPATH. Packaged synthetic data and existing agent import succeeded.
- No repository type-check command is configured. No new dependencies or lock
  changes are required; existing SciPy supplies HiGHS LP.

Numerical checks:

- Analytic equal-reactance triangle reference: 120 MW renewable transfer,
  30 MWh curtailment and EUR 3,000 cost. DC LP gap to independent optimum: zero.
- Copperplate and transport relaxations violate physical ratings by 10 MW and
  6.6666667 MW respectively; their cheaper costs are not feasible savings.
- A +10 MW rating change on line 0–1 avoids EUR 3,000 in the synthetic hour;
  upgrading either other line alone avoids zero.
- Kirchhoff cycle balance, reversed orientation, radial transport/DC agreement,
  duration scaling, physical scaling and infeasible supply cases tested.
- Additional radial size checks at 5/20/100 buses independently match their
  40 MW cut, requiring 110 MW firm supply (EUR 11,000); all DC-feasible.
- Actual agent role, bounded five-step trace and no-quantum declaration tested.

The JSON result preserves inputs/evidence hashes, versions, installed agent
revision, full trace, dispatches, sensitivities, construction/solver runtimes
and resource counts. Run timings are host-dependent and single observations,
not statistical speedup measurements. All numerical inputs are synthetic;
news response hashes identify source retrievals, not calibration measurements.

GitHub CI is verified separately for the published PR head. This record describes
local execution and does not imply merge, deployed documentation or plant approval.
