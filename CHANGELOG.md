# Changelog

## Unreleased

- Disclose the AI-native, human-controlled development process in the README,
  documentation and contribution guide, distinguishing review from validation.
- Add a searchable GitHub Pages documentation site with a getting-started guide,
  executed example gallery, reference benchmark downloads and repository roadmap.
- Automatically build and publish documentation from `main` with GitHub Actions.

## 0.1.0 — 2026-10-11

First public EnerQit release, adapted from the earlier QuantumPV prototype.
MIT license; explicit classical/quantum-inspired/simulator/hardware distinctions.

Initial research implementation: pvlib-based orientation/tracker inference;
single-diode sweep and MPP fits; uniform string topology; effective inverter and
thermal curves; QUBO/Ising conventions and exact/SA/bSB solvers; optional quantum
exports and educational QAOA simulation; daily evidence store; benchmark CLI;
tests, seven gallery examples, notebook, documentation and CI.

Known limits: synthetic validation only, simplified irradiance/thermal models,
no globally calibrated uncertainty, no production scalability guarantees, and
no demonstrated quantum-inspired or quantum hardware advantage.
