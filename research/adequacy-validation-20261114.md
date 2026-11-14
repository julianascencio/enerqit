# Winter adequacy screen: validation record

Run date: 2026-11-14 (Atlantic/Canary, UTC+00:00). Data timestamps use UTC.
Base: `26d2bdd67ab8682e705f1eb25e47b17f8ddfc09b`.
Actual energy-agents source: `f465e6afb43a52f41b151c199144b53c3bbf441f`.
The result JSON records its installed Git revision, package versions, input SHA256,
source-response hashes, four executed role tools, results and timings.

## Executed local checks

- `python -m pytest --cov=enerqit`: 191 passed, 90% total coverage.
  One external anyio pytest-plugin deprecation warning; no failed tests.
- `python -m ruff check .`: passed.
- `python ci/run_examples.py --output results/examples`: all 14 examples passed.
- `python -m sphinx -W --keep-going -b html docs/sphinx/source docs/_build/html`: passed after correcting a heading underline.
- `python -m build`: wheel and source distribution passed.
- `git diff --check`: passed. No repository type-check command is configured.
- Two study figures inspected for labels and consistency with numeric results.

Checks used an isolated virtual environment with pinned agent installation to avoid
shared editable-install interference. The reproducible installation command is in
the gallery example; no new numerical dependency or lock update is required.

## Independent scientific evidence

Hand-calculated three-capacity probability distribution and binomial formulas for
1/3/8/12-unit fleets verify enumeration. Tests cover q=0 and q=1, invalid inputs,
probability mass, zero demand, duration scaling, infeasible offer sets and the
four-tool registered-agent trace. Exhaustive offer search certifies the minimum
within the supplied discrete offer list; it is not a continuous-market optimum.

The common-outage model gives 69.52 MWh EENS versus 63.688 under independence at
identical marginal unit outage probabilities. Independence selects 40 MW / EUR
4,000, which yields 26.16 MWh under the common-outage model and misses the assumed
20 MWh target. Common-outage screening selects 60 MW / EUR 6,000 with 17.44 MWh.
The EUR 2,000 difference is an assumed window procurement fee, not realized savings.

Inputs are authored synthetic MIT fixtures. Primary report facts motivate this
inference/optimization question but do not calibrate probabilities. Sensitivity
is a scenario sweep, not statistical confidence bounds. Timings are machine-specific.
No quantum computation, ML training, annual adequacy claim, live equipment action,
or claim of independent human review is made. Real joint-outage/weather/load,
network, storage-energy and contract evidence remain prerequisites for procurement.

## Publication status

This record documents local evidence, not GitHub CI completion, merge or deployment.
Consult the PR's exact-head checks for publication verification. The new methods
are proposed changes until merged. Independent human scientific review is pending.
