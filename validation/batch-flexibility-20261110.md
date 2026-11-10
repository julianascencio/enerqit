# Batch flexibility engineering — second run, 10 November 2026

## Scope and provenance

AI-generated methods, tests, documentation and example, with automated scientific
accounting checks. No human domain approval or field validation is claimed.
The trigger is the IEA's 5 November Spain policy review. Four primary-source
candidates and deferred cases are preserved in `research/news-ledger.json`.
The 29 October Ember data-centre report is explicitly older background; it is
not relabelled as this week's news. No source articles are redistributed.

All profiles, jobs, prices, site ceilings and scenarios are synthetic. Source
response hashes, dates, input digest and actual installed agent revision are
recorded. Energy Data Insights was inspected at
`b5ae10d43619155519a56ab3a30cb6660db8ca55`; its REE statistics and BESS/HVAC
analyses cannot supply job-level site inputs. No new network connector is needed.

## Implemented and exercised

- Fixed noninterruptible AC profiles, release/deadline windows, whole-horizon
  energy accounting and one advance schedule across deterministic grid scenarios.
- Native SciPy/HiGHS MILP, independent enumeration of actual start tuples, and
  conservative QUBO with sufficient integer-residual penalty after per-job cost
  shifting. Negative prices are supported without incentivizing missing jobs.
- Existing exact, classical SA and quantum-inspired bSB solvers; no new solver
  copies, QPU jobs or claimed quantum advantage.
- The actual `career_quantum_ml_engineer` invokes four registered EnerQit tools.
  Current merged energy-agents source is pinned to
  `832f4117f95ac3137c63eace389e56cdc2c075fe`; no adapter change was required.
  The default planner is explicitly scripted/offline, not live LLM inference.
- Full record: `benchmarks/results/flexibility-engineer-20261110.json`.

## Checks

- Ruff and `git diff --check`: passed.
- Full suite with coverage: **60 passed**, including **23 new tests**; aggregate
  coverage 90% in this local environment.
- Exhaustive state-by-state objective/feasibility identity for a small negative-
  price QUBO, plus eight seeded native MILP/enumeration/QUBO cross-oracle cases.
- Physical energy and grid accounting, exact deadline boundary, subhour interval
  scaling, invalid/duplicate/missing inputs, conservative rounding exclusion,
  infeasible deadlines, violated baseline, invalid one-hot selections and bounded
  enumeration resources.
- All **nine** gallery examples executed. Four new plots visually inspected.
- Warnings-as-errors Sphinx build and source/wheel builds passed.
- The installed wheel ran the full agent workflow from `/tmp`, outside the
  repository checkout. Source archive includes pinned optional requirements,
  research ledger and JSON benchmark records.
- CI includes both storage and batch agent integrations and the full new CLI.

A preinstalled AnyIO plugin emits a pytest-internal deprecation warning locally;
it does not affect the numerical checks.

## Observed result

For identical 9 MWh of completed work, price-only scheduling costs synthetic
EUR 105 but violates a grid ceiling by up to 5 MW. Nominal-only planning costs
EUR 390 and violates the higher-load scenario by 1 MW. Shared-scenario MILP,
independent native enumeration, exact QUBO and each of the three seed-0/1/2
SA/bSB runs return a feasible EUR 525 optimum. Starts are 1/3/4/1.

The EUR 135 difference from nominal planning is a modeled feasibility premium,
not a realized saving. The 16-job scaling case has SA gap EUR 300 and bSB gap
EUR 200, retained with every candidate and timing. MILP remains the recommendation.

Deterministic sensitivities expose an EUR 800 solution at +0.25 MW baseline load,
infeasibility at +1.25 MW, deadline-driven infeasibility and an EUR 800 optimum
from a coarser 2 MW QUBO step. No calibrated scenario probabilities, actual tariffs,
process/thermal/staffing dynamics, network power flow or production dispatch are
claimed. Future operational use needs measured profiles and validated constraints.
