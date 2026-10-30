# EnerQit

<p align="center">
  <a href="https://asvaconsulting.com">
    <img
      src="docs/sphinx/source/_static/asva-consulting.jpg"
      alt="ASVA Consulting"
      width="280"
    />
  </a>
</p>

<p align="center">
  <strong>Created by ASVA Consulting</strong><br>
  <a href="https://asvaconsulting.com">asvaconsulting.com</a><br>
  <a href="mailto:contacto@asvaconsulting.com">contacto@asvaconsulting.com</a>
</p>

**An open-source Python toolkit for quantum-inspired algorithms in energy systems.**

EnerQit connects physical energy models, inverse inference and reproducible solver
comparisons. Its first application is **solar PV**: infer array configurations,
estimate equipment response curves and compare classical and quantum-inspired
optimization on the same explicitly defined problem.

**[Documentation](https://julianascencio.github.io/enerqit/)** ·
[User Guide](https://julianascencio.github.io/enerqit/user_guide/index.html) ·
[Example Gallery](https://julianascencio.github.io/enerqit/gallery/index.html) ·
[API Reference](https://julianascencio.github.io/enerqit/api.html) ·
[Research Library](https://julianascencio.github.io/enerqit/research/index.html) ·
[Contributing](https://julianascencio.github.io/enerqit/contributing/index.html)

The documentation follows the scientific Python format used by
[OrbitalPV](https://github.com/julianascencio/orbital-pv): a user guide, executable
examples with figures, API reference and research sources. EnerQit's package
remains focused on energy inference and optimization.

## AI-assisted development and literature basis

EnerQit is **AI-native and human-controlled**. Most code, tests, examples and
documentation are AI-generated or AI-drafted. Human maintainers choose the
scientific direction and source literature, define requirements, and retain
control over review, acceptance and releases.

Assumptions and methods should be traceable to the selected papers, public
technical documentation or explicitly stated engineering assumptions. The
[research library](https://julianascencio.github.io/enerqit/research/index.html)
connects the implemented methods to their sources.

Validation is still developing. AI-generated implementations, explanations and
source interpretations may contain mistakes; human control does not mean every
line has received expert review. Automated checks, human review and validation on
real assets provide different evidence. Version 0.1.0 is a research implementation
validated on synthetic examples; verify assumptions and results for your use case.

## Install from source

Use Python 3.11 or newer in a clean environment. The CI matrix covers Python
3.11–3.13. From a checkout:

```bash
git clone https://github.com/julianascencio/enerqit.git
cd enerqit
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[examples]"
```

Optional extras support development, documentation and local model export:

```bash
python -m pip install -e ".[dev,docs]"
python -m pip install -e ".[quantum]"
```

## Quickstart

Recover the orientation of a synthetic fixed PV array with the public solar API:

```python
from enerqit.datasets import fixed_array
from enerqit.solar import fit_orientation

observations, truth = fixed_array(seed=42)
result = fit_orientation(
    observations,
    latitude=truth["latitude"],
    longitude=truth["longitude"],
)
print(result.parameters)
print(result.status, result.warnings)
result.to_json("results/orientation.json")
```

The observations above are **synthetic**. A fit is conditional on its inputs,
known capacities and forward-model assumptions; `status="estimated"` does not
establish a globally unique or unbiased answer. See the
[data contract](https://julianascencio.github.io/enerqit/data_contract.html) and
[physical inference guide](https://julianascencio.github.io/enerqit/methods.html).

Run the command-line demonstrations or a complete plotted example:

```bash
enerqit demo --output results/demo
enerqit benchmark --output results/benchmark.jsonl
python docs/examples/plot_orientation.py
```

The demo writes observations and a JSON result with provenance. The
[example gallery](https://julianascencio.github.io/enerqit/gallery/index.html)
contains seven executed studies with downloadable scripts and notebooks.

## Main capabilities

| Capability | Evidence and current implementation |
|---|---|
| Fixed-array tilt and azimuth | AC power, irradiance, weather, location and known capacities; bounded physical least squares |
| Tracker geometry | Known axis and backtracking mode, with low-sun coverage; differential evolution for GCR and rotation limit |
| IV reference parameters | Measured IV sweeps at known effective irradiance and cell temperature; De Soto single-diode fitting through pvlib |
| Operational IV reconstruction | Confirmed MPP voltage/current over informative conditions; selected parameters fitted while others remain fixed |
| Uniform string topology | Array DC voltage/current and known module physics at MPPT; integer candidate enumeration |
| Effective inverter and thermal curves | Synchronized converter input/output or independently available AC and thermal evidence; explicit coverage checks |
| Coupled configuration selection | Forward templates, one-hot choices and inventory equalities; common QUBO/Ising encodings |
| Solver benchmarking | Exact QUBO and native feasible enumeration, simulated annealing, and ballistic simulated bifurcation |
| Local evidence studies | Idempotent SQLite ingestion, late corrections, immutable snapshots and structured result records |

**AC power alone cannot uniquely reveal full IV curves, exact equipment counts or
unrestricted tracker settings.** Model-derived equipment curves are conditional
field estimates, not manufacturer-certified specifications. The
[use-case register](https://julianascencio.github.io/enerqit/use_cases.html)
sets out the evidence and limits for each application.

### What “quantum-inspired” means here

| Approach | Execution in EnerQit | Current status |
|---|---|---|
| Classical optimization | CPU | Physical fitting, exact enumeration and simulated annealing |
| Quantum-inspired optimization | CPU | NumPy ballistic simulated-bifurcation reference solver |
| Quantum-circuit simulation | CPU | Small educational QAOA statevector example |
| Quantum hardware execution | Not implemented | Local dimod and Qiskit model export adapters are available |

Quantum-inspired algorithms run on ordinary computers. Exporting a model to a
quantum SDK does not execute it on physical qubits. **No quantum advantage or
superiority over classical methods is claimed**; exact enumeration is fastest on
the supplied small [reference benchmark](https://julianascencio.github.io/enerqit/benchmarking.html).
Read the [quantum guide](https://julianascencio.github.io/enerqit/quantum.html)
for the encoding conventions, limitations and future hardware research path.

## Repository map

| Path | Purpose |
|---|---|
| `enerqit/` | Physical models, inverse estimators, QUBO encodings and evidence utilities |
| `enerqit/solar/` | Public entry point for the initial solar application |
| `enerqit/solvers/` | Classical baselines, simulated bifurcation and optional quantum exports |
| `docs/examples/` | Seven executable gallery examples |
| `docs/notebooks/` | Introductory inverse-study notebook |
| `docs/sphinx/source/` | User guide, gallery configuration, API, research and contributor documentation |
| `tests/` | Recovery, invalid-data, identifiability, encoding and audit checks |
| `benchmarks/` | Reproducible runner and recorded reference results |
| `paper/` | Methods note and primary references |
| `validation/` | Recorded validation evidence and environment details |
| `ci/` and `.github/workflows/` | Quality checks, example runner and documentation deployment |

## Documentation

Read the published site at **https://julianascencio.github.io/enerqit/**.
The Sphinx documentation uses the PyData theme and executes the examples during
the build, following OrbitalPV's documentation format.

```bash
python -m pip install -e ".[docs]"
make docs
```

Without `make`, run the equivalent command from the repository root:

```bash
python -m sphinx -W --keep-going -b html docs/sphinx/source docs/_build/html
```

Open `docs/_build/html/index.html` to review the site. To save all example figures
without building documentation:

```bash
python ci/run_examples.py --output results/examples
```

## Development and reproducibility

```bash
python -m pip install -e ".[dev,docs,examples,quantum]"
python -m ruff check .
python -m pytest --cov=enerqit --cov-report=term-missing
make docs
python -m build
```

`uv.lock` records a dependency solution. To use it, run
`uv sync --extra dev --extra docs --extra examples --extra quantum`.
Synthetic seeds are explicit; elapsed times depend on the host. The recorded
results do not establish real-plant performance or a large-scale speedup.
Follow [CONTRIBUTING.md](CONTRIBUTING.md) for scientific and documentation changes.

## Research and roadmap

The [methods note](paper/README.md) and
[research library](https://julianascencio.github.io/enerqit/research/index.html)
describe the current evidence base: pvlib forward physics, De Soto parameter
translation, simulated bifurcation, and QUBO/Ising model conventions.

[ROADMAP.md](ROADMAP.md) tracks held-out field validation, stronger classical
baselines and future wind, storage, grid and market applications. Those additional
energy domains are planned, not implemented. The initial solar application grew
from the earlier QuantumPV work.

## Creator and license

Created by **[ASVA Consulting](https://asvaconsulting.com)**.
Contact: **[contacto@asvaconsulting.com](mailto:contacto@asvaconsulting.com)**.

EnerQit is released under the [MIT license](LICENSE). See [NOTICE](NOTICE) for
attribution; dependencies retain their own licenses. EnerQit uses pvlib for
forward PV physics and is independent of, and not endorsed by, pvlib.
