# EnerQit 0.1.0 validation

Validated locally on Python 3.12 / Linux with deterministic synthetic evidence.

- 20 tests passed, including dimod and Qiskit energy-preservation checks.
- Test statement coverage: 90% (the new solar facade was also smoke-tested separately).
- Seven gallery examples executed successfully.
- Introductory notebook code cells executed sequentially.
- Sphinx HTML built with warnings treated as errors.
- Source distribution and wheel built successfully.
- The solar entry point recovered the synthetic orientation.
- Reference benchmark: 24 records, including every solver outcome.

See `environment.json` for package versions and `benchmarks/results/` for raw
benchmark evidence. Reproduce with the commands in the root README. The
GitHub Actions matrix is configured separately; this report does not assert
remote CI success or validation on all supported Python versions.

All supplied solvers execute on classical computers. The QAOA example is a
classical simulation; export adapters do not execute a quantum computation.
No quantum hardware or quantum advantage is demonstrated.
