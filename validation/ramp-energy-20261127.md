# Continuous ramp audit — 27 November 2026

AI-authored methods, tests and documentation. Human review and field validation
remain outstanding. Base b8dbbf54bcba6f0f5ab4ae22cbf100853ae6f885. Actual installed
agent 9a8a56b3be12e734183a0350600bf874bdee8ff0; inspected EDI
0f3c90cbb13b8ecc72f5d6c6b44beb319a7d4aaf. No EDI connector reused.

Synthetic authored MIT fixture SHA256: da590c19dfc456f4711d840c868bf7c30e920b90db70ac0cb7a8f2bd6e791821.
No source dataset copied. NESO 26 November publication is context only; no raw
response archived, so source-response hash is null rather than fabricated.
UTC interval starts 27 November 00:00Z. Deterministic study; test seeds 0–5.
Actual five-entry trace and package versions are in the benchmark JSON. Python
3.12.14, NumPy 2.3.5, SciPy 1.17.0. No quantum method executed or needed.

Ruff and full pytest coverage run: 364 passed, 87% coverage. One external AnyIO
plugin deprecation warning; no test failure. Six random quadrature references,
hand-derived triangles, subdivision, reversal, balance, invalid input and
capacity/ramp infeasibility tests. Initial adaptive quadrature missed a small
crossing; subdividing its integration domain fixed the independent reference
without relaxing the assertion tolerance. Figure visually inspected.

Commands: `python -m ruff check .`, `python -m pytest --cov=enerqit`,
`python -m enerqit.ramp_energy_study`,
`MPLBACKEND=Agg python ci/run_examples.py --output results/examples`,
`MPLBACKEND=Agg python -m sphinx -W --keep-going -b html docs/sphinx/source docs/_build/html`,
`python -m build`. Final example/docs/build completion recorded in the PR.
No separate type checker configured. Exact-head GitHub CI is separate evidence.

Continuous 0-to-40 MW ramp: 20 MWh generation and 20 MWh shortage, EUR21000
scenario objective. Held endpoint baseline: 40 MWh generation, zero shortage,
EUR2000 objective. EUR19000 difference is not realized loss: it exposes differing
trajectory semantics. No continuous optimum or optimality gap is claimed.

Half-hour delivery is infeasible at 40 MW/h; one and two hours feasible, with
20 and 40 MWh shortage respectively. Subdivision through 8760 segments preserves
energy. Single-run audit runtimes are environment-dependent, not speedup claims.
Linear interpolation, constant penalties and no network/startup model limit use.
Next: validate instantaneous telemetry and physical trajectory assumptions before
optimizing or accepting an operator schedule. No dispatch or deployment occurred.

Final local completion: all 26 offline examples passed; strict Sphinx build
succeeded; wheel and sdist built successfully.

First GitHub head passed scientific jobs but failed strict docs on two generated
heading underlines. Lengthened gallery headings and reran a clean `sphinx -E -a
-W` build; this corrects markup without weakening warnings-as-errors.
