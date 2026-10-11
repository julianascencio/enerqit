# Contributing

Use a branch and keep physical forward models separate from inverse estimators
and solver encodings. Follow NumPy-style docstrings, SI units, seeded randomness,
and explicit uncertainty/identifiability statements. Use pvlib for established
PV physics instead of duplicating its model implementations.

Before proposing a new quantum-inspired method, include a native classical
baseline and a same-objective baseline. Report the original engineering residual,
constraint feasibility, optimization objective, data split and all runtime costs.
Do not infer physical validity from a lower penalized QUBO energy alone.

Run `python -m ruff check .`, `python -m pytest`, all examples, and a Sphinx build.
Scientific changes need recovery tests and a relevant failure case. Keep remote
execution opt-in and separate from local imports and examples. Do not include
client data, credentials, proprietary OEM tables, or operational database exports.

When reporting problems include Python/package versions, seed, a synthetic
reproducer, expected physical behavior and the observed result. Contributions
are provided under the project's MIT license. Only submit material you have
the right to contribute.

Always label execution honestly: a quantum-inspired method is a classical
algorithm; a simulator uses classical hardware; a QPU experiment must identify
the actual hardware and execution evidence. SDK imports and model exports do
not constitute quantum computation or prove quantum advantage.

Each new energy use case must define an engineering KPI, a strong classical
baseline, evidence/validity limits, an explanation of the result, scaling/cost
measurements, intended user value, and reproducibility artifacts (seeds,
structured logs, data provenance and exact run instructions).
