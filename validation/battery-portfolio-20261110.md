# Battery portfolio engineering — 10 November 2026

AI-generated implementation and documentation, checked against explicit physical
accounting and independent optimization oracles. No human domain review or field
validation is claimed. Synthetic inputs are separate from sourced news facts.

## Delivered

- `enerqit.storage`: DC/AC energy and duration limits, independently evaluated
  portfolios, native binary-cover MILP, native enumeration and conservative QUBO.
- `enerqit.storage_study`: evidence inspection, repeatable solver benchmarking,
  duration/SOC/encoding sensitivity and handoff through the Quantum ML Engineer.
- Runnable gallery with three figures; offline fixture and full JSON benchmark.
- Optional agent pinned to `f5c40e7766646f29875da5e2df1df8aa3a5d3027`
  from energy-agents PR #19. Core EnerQit numerical methods do not import it.

## Checks performed

- Ruff: passed.
- Full EnerQit test suite: **37 passed**, including 17 storage/integration tests.
- Physical checks: usable DC/AC energy, discharge efficiency, SOH, reserve energy,
  ending SOC, export limits, unavailability, zero target, positive-duration and
  finite-input validation, SOC-buffer/duration monotonicity, explicit infeasibility.
- Independent oracles: twelve seeded random native MILP/enumeration/QUBO problems;
  exhaustive energy and constraint comparison for every bitstring in a small QUBO.
- All **8** executable gallery examples passed.
- Sphinx build with warnings treated as errors: passed; three new plots inspected.
- Source distribution and wheel: built successfully.
- Pinned Git agent installed into a separate target directory; built EnerQit wheel
  executed the full study from `/tmp`, outside the repository source directory.
- Supporting energy-agents change: 400 tests passed, Ruff, docs and package builds
  passed; GitHub quality and documentation workflows green at the pinned revision.

One local pytest warning comes from the preinstalled AnyIO pytest plugin using a
deprecated pytest internal alias; it is unrelated to the scientific methods.

## Result and limits

Native MILP and independent native enumeration select B/E/H at synthetic £25,000,
providing 180.1667 MW of three-hour capacity. The £7,000 power-only A/G selection
provides 22.1271 MW and misses 157.8729 MW of the constructed target. Exact QUBO
agrees with the native optimum. bSB seeds 0/1/2 attain it; SA seeds 0/1/2 have gaps
£0/£2,000/£3,000. Every outcome is retained, with budgets and timings in
`benchmarks/results/battery-engineer-20261110.json`.

This small eight-asset, 14-bit example establishes no scaling, hardware, field,
realized-savings or quantum-advantage claim. The default agent is a scripted tool
workflow, not an autonomous LLM. The news review is the dated, separately performed
research preserved in the fixture. No operational dispatch or publication occurs
when running the example.
