# Contributing

EnerQit welcomes reproducible improvements to energy models, inverse estimators,
optimization methods, evidence utilities, examples and documentation.

## Development setup

Use a branch in a local checkout and install the development tools:

```bash
git clone https://github.com/julianascencio/enerqit.git
cd enerqit
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,docs,examples,quantum]"
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. The optional
`quantum` extra provides local export SDKs; it does not enable remote execution.

## AI-assisted contributions and provenance

EnerQit is **AI-native and human-controlled**: most code, tests, examples and
documentation are AI-generated or AI-drafted. Human maintainers choose the
scientific direction and source literature, define requirements, and retain
control over review, acceptance and releases.

For each contribution:

- Cite the specific papers, public datasets or technical documentation behind a
  method, parameter choice or comparison. Distinguish sourced values from
  illustrative defaults and engineering assumptions.
- Describe what AI generated or modified and summarize the review and checks
  actually performed. Do not claim review or validation that has not happened.
- Keep automated checks, human review and validation on real assets distinct.
  AI-generated code and interpretations may contain mistakes; passing tests alone
  does not establish scientific validity.
- Update the relevant method page, [methods note](paper/README.md) and research
  library when sources materially affect implementation or assumptions.

Contributors remain responsible for accuracy, provenance and the right to share
their material. The current implementation has synthetic validation; broader
field validation should grow alongside the project.

## Scientific and software conventions

Keep physical forward models separate from inverse estimators and solver
encodings. Follow NumPy-style docstrings, SI units, seeded randomness and explicit
uncertainty or identifiability statements. Use pvlib for established PV physics
instead of duplicating its implementations.

A new method or energy use case should define:

- An engineering KPI and the intended user benefit.
- Input evidence, provenance, units, operating regimes and validity limits.
- A meaningful classical baseline and the same engineering objective for each
  solver comparison.
- An explanation of the result, including ambiguity and infeasible outcomes.
- Scaling or cost measurements appropriate to the claim, including preprocessing
  and solver time.
- Reproduction instructions, seeds, structured logs and relevant data splits.

Report original physical residuals and constraint feasibility alongside penalized
QUBO energy. Scientific changes need recovery tests and a relevant failure case;
lower QUBO energy alone does not establish physical validity.

Label execution accurately: quantum-inspired methods are classical algorithms;
statevector simulation runs on classical hardware; a QPU experiment must identify
the actual hardware and execution evidence. SDK imports and model exports do not
constitute quantum computation or prove quantum advantage.

## Documentation and examples

The site follows OrbitalPV's scientific Python documentation format: User Guide,
Example Gallery, API Reference, Research Library and Contributing. Maintain RST
sources under `docs/sphinx/source/`; generated HTML and gallery output are build
artifacts.

Document user-facing behavior both conceptually and in API docstrings. Add an
executable example in `docs/examples/` when a figure or complete workflow makes
the feature easier to understand. Examples should state their data provenance,
use explicit seeds and run locally without credentials. Remote execution must be
opt-in and separate from imports or the default documentation build.

## Before opening a pull request

Run the checks relevant to your changes; scientific or packaging changes should
also pass the complete test suite:

```bash
python -m ruff check .
python -m pytest --cov=enerqit --cov-report=term-missing
python ci/run_examples.py --output results/examples
make docs
python -m build
```

Without `make`, build the documentation with:

```bash
python -m sphinx -W --keep-going -b html docs/sphinx/source docs/_build/html
```

Describe the problem, the resulting behavior, verification performed and remaining
limitations in the pull request. A documentation build executes the gallery, so a
successful build also checks that the documented examples run.

## Reporting issues and repository hygiene

Include Python/package versions, the seed, a synthetic reproducer, expected
physical behavior and the observed result in bug reports.

Use public technical sources and authorized data. Do not include client data,
credentials, proprietary OEM tables or operational database exports.
Contributions are provided under the project's MIT license. Only submit material
you have the right to contribute.
