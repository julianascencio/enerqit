# EnerQit

**An open-source Python toolkit for quantum-inspired algorithms in energy systems.**

**AI-native, human-controlled.** Most of EnerQit's code, tests, examples and
documentation are AI-generated. Human maintainers set the direction and scientific
requirements, and retain control over review, acceptance and releases.
This describes the development process; it does not imply that every line has
received expert review or that passing automated checks proves scientific validity.

**[Explore the documentation website](https://julianascencio.github.io/enerqit/)**
— start here, worked examples, benchmark results, API reference and roadmap.

> **Quantum-inspired is not quantum computing.** EnerQit's quantum-inspired
> solvers are classical algorithms running on ordinary computers. They use ideas
> motivated by quantum research, but do not use physical qubits or execute on a
> quantum processor. The optional QAOA example is also a classical simulation.
> Exporting a model to Qiskit or dimod does not mean it has run on quantum hardware.

The first release provides PV configuration inference, equipment characterization,
and reproducible comparisons between classical and quantum-inspired solvers.
The long-term scope includes solar, wind, storage, grids and energy markets;
only the implemented capabilities listed below are currently available.
Version 0.1.0 is a research implementation validated on synthetic evidence.

| Approach | Where it runs in this project | Current status |
|---|---|---|
| Classical optimization | CPU | Exact enumeration, constrained physical fitting, simulated annealing |
| Quantum-inspired optimization | CPU | Ballistic simulated bifurcation, implemented with NumPy |
| Quantum-circuit simulation | CPU | Small educational QAOA statevector example |
| Quantum hardware execution | Would require a QPU or quantum annealer | Not implemented; model export adapters are available |

**No quantum advantage or superiority over classical methods is claimed.**
The exact classical solver is faster on the supplied small benchmark.

The layout follows [pvlib-python](https://github.com/pvlib/pvlib-python): a flat
scientific package, independent tests, Sphinx documentation with an executable
example gallery, benchmarks, CI, and a methods note. EnerQit depends on pvlib
for forward physics; it is independent of, and not endorsed by, pvlib.

## Quick start

CI checks Python 3.11–3.13; the delivered local validation used Python 3.12. A clean
virtual environment is recommended. Start from the repository directory:

```bash
git clone https://github.com/julianascencio/enerqit.git
cd enerqit
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e '.[dev,docs,examples]'
enerqit demo --output results/demo
enerqit benchmark --output results/benchmark.jsonl
python -m pytest -q
python docs/examples/plot_orientation.py
```

The CLI writes a CSV and a provenance-bearing JSON report. Examples produce
Matplotlib figures and print estimates; in a noninteractive environment use the
gallery build or `python ci/run_examples.py --output results/examples` to save figures.

```python
from enerqit.datasets import fixed_array
from enerqit.solar import fit_orientation

frame, truth = fixed_array(seed=42)  # synthetic, not an OEM dataset
result = fit_orientation(frame, latitude=35, longitude=-5)
print(result.parameters)
result.to_json("results/orientation.json")
```

## Implemented scientific scope

| Inference | Required evidence | Implemented estimator / comparison |
|---|---|---|
| Fixed tilt and azimuth | AC, GHI/DNI/DHI, weather, location, known capacities | Bounded physical least squares; candidate scan versus bSB |
| Tracker GCR and rotation limit | Above plus known axis and backtracking mode, low-sun coverage | Differential evolution; candidate scan versus bSB |
| IV reference parameters | Measured IV sweeps at known effective irradiance and cell temperature | Five-parameter De Soto fit via pvlib |
| Conditional operational IV reconstruction | Confirmed MPP voltage/current across G/T conditions | Selected parameter fit, with other parameters fixed |
| Uniform modules/string and parallel strings | Array DC V/I, known module physics, confirmed MPPT | Integer enumeration; ranked alternatives |
| Effective inverter efficiency | Synchronized actual DC input and AC output | Nonnegative loss model; coverage/rank checks |
| Effective thermal limiting envelope | Defined thermal sensor, independently available AC, command limits | Piecewise fit; refuse an unexcited knee |
| Coupled configuration hypotheses | Forward templates and explicit inventory equalities | Exact QUBO, native feasible enumeration, SA and bSB |
| Daily evidence for an offline study | Timestamped numeric batches for a named asset | Idempotent SQLite ingestion, late corrections and immutable snapshots |

**AC power alone does not uniquely reveal full IV curves, exact module/inverter
counts, or unrestricted tracker settings.** Every fit is conditional on its
stated data and modeling assumptions. Model-derived field curves are not
manufacturer-certified curves. `status="estimated"` means a fit passed local
checks; it is not proof of a globally unique or unbiased answer.

## The quantum component

`enerqit.solvers.simulated_bifurcation` is a transparent NumPy implementation
of ballistic simulated bifurcation, a classical oscillator algorithm inspired by
quantum optimization research. It runs on a normal CPU, not a quantum device.
The same QUBO can be exported to a dimod BQM or a Qiskit Pauli operator:

```bash
python -m pip install -e '.[quantum]'
python docs/examples/plot_quantum_bridge.py
```

The built-in small QAOA statevector example is also classical simulation. No
credentials, network execution, paid job or hardware advantage is implied.

The transferable investment is the physical model, binary encoding, constraint
tests, datasets, and benchmark harness. bSB trajectories do not automatically
transfer to a QPU. See `docs/sphinx/source/quantum.rst` for the migration steps.

For low-dimensional continuous fits, ordinary constrained optimization is the
appropriate baseline and often the best tool. For single-candidate selection,
direct enumeration is simpler. The quantum-inspired research target is **coupled
discrete inverse problems with physical and inventory constraints**, where many
configurations interact. There is no established superiority claim here.

## Repository map

| Path | Purpose |
|---|---|
| `enerqit/` | Public APIs, generic optimization, and initial solar inference modules |
| `enerqit/solar/` | Public entry point for the first energy-domain application |
| `tests/` | Physical recovery, invalid data, identifiability, QUBO conventions and audit tests |
| `docs/examples/` | Seven executable worked examples |
| `docs/notebooks/` | Self-contained introductory notebook |
| `docs/sphinx/source/` | Installation, methods, API, use cases, data contract, product workflow |
| `benchmarks/` | Reproducible comparison runner and measured reference results |
| `ci/` | Example runner and quality-check commands |
| `.github/workflows/` | Python test matrix, docs build and automatic GitHub Pages deployment |
| `paper/` | Methods note and primary references |
| `validation/` | Delivered test/build report and environment details |

## Daily study workflow

```bash
enerqit ingest results/demo/synthetic_observations.csv \
  --store results/study.sqlite --asset demo-plant
```

Ingest each new batch, review its coverage, select physically valid operating
regimes, and fit a separately versioned current-evidence model. Keep the initial
reference immutable. Do not interpret every daily refit as a physical change.
Seasonal coverage matters more than a daily delivery schedule. The worked daily
example demonstrates this locally; no recurring task is installed.

The initial applications support reproducible inverse-engineering studies,
equipment characterization and solver evaluations using authorized data exports.
Future energy-domain contributions should follow the same evidence requirements;
see `ROADMAP.md` and `CONTRIBUTING.md`.

## Development and reproducibility

```bash
python -m ruff check .
python -m pytest --cov=enerqit --cov-report=term-missing
python -m sphinx -W --keep-going -b html docs/sphinx/source docs/_build/html
python -m build
```

`uv.lock` records a dependency solution. To use it: `uv sync --extra dev --extra
docs --extra examples --extra quantum`. The validation report records the actual
environment used for this delivery. Synthetic seeds are explicit; elapsed times
depend on the host and are not deterministic. No real plant validation or
large-scale speedup test has been performed.

EnerQit is released under the **MIT license**. See `LICENSE`, `NOTICE`,
`CONTRIBUTING.md`, and `CHANGELOG.md`. Third-party dependencies retain their
own licenses. The earlier QuantumPV work supplies the initial solar application;
EnerQit is the broader energy-algorithms project.
