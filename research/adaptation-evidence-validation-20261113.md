# Genesis-inspired adaptation evidence: validation record

## Source and scope

Considered the user-supplied Genesis AiX, LLC white paper *Hybrid
Quantum-Classical Intelligence Architecture*, version 0.3, November 2026.
Source SHA-256: `2f3b9a0f8fef410301cd3764ffa5ef45f534706c9d72a98ec031c05435e01c5a`.
Sections 3.5, 5, 6.2–6.4, 7.1, 9.3 and 10.1 motivate evidence separation,
currentness, exact scope, effect witnessing and negative controls. The PDF is
not redistributed. Its claims remain those of a conceptual research proposal.

EnerQit implements an independent offline semantic model and a reproducible PV
optimization example. This is not Genesis middleware, QEC, a control adapter,
an authenticated policy engine or a demonstration of quantum reliability.

## Protocol and observed results

The existing `coupled_inventory(seed=42)` generator creates one 12-variable
synthetic PV problem. Exhaustive enumeration supplies the reference optimum.
Eight seeds compare classical simulated annealing with 1 versus 16 reads, each
using 80 sweeps and local polishing. The materiality threshold is fixed at
`1e-6` synthetic objective units before evaluation. Changed compute is explicit.

The recorded run contains **3 improved, 1 regressed, and 4 inconclusive**
comparisons. The inconclusive comparisons lack feasibility for both candidates;
the raw candidates, feasibility, objective gap and signal RMSE are preserved.
Regression is retained. These are descriptive labels on one synthetic instance,
not statistical significance, causality, speedup or history-learning value.

All 12 adverse controls return `HOLD_REVALIDATE`; the positive control returns
`ELIGIBLE_FOR_SIMULATION`. The eight applied local settings receive a declared
W2 grade from solver metadata. Acknowledgment alone receives W1 and remains
unverified. No independently corroborated W3 application is claimed.

The [JSON result](../benchmarks/results/adaptation-evidence-20261113.json) stores
source metadata, input fingerprint, environment, budgets, exact reference,
observations, interpretations, proposals, declarations of authority, decisions,
request identities, witnesses, later measurements, outcomes and timing/size
measurements. Wall times are machine-dependent; increasing reads also changes
random-number consumption, even when seed labels match.

## Verification

- Full Python suite: 175 tests passed (57 new lineage cases).
- Ruff checks passed.
- Strict Sphinx build executes the 13-example gallery.
- Source distribution and wheel build successfully.
- SQLite restart, idempotency, parent integrity, immutable IDs, nonfinite JSON
  rejection and accidental content-corruption detection are tested.
- Negative tests cover every required context identity, missing/revoked/expired
  authority, modified settings, replay, incomplete/contradictory evidence,
  uncertain clocks, partial application and unbound or wrongly ordered witnesses.

Reproduce with `python -m pytest`, `python -m ruff check .`, `make docs`,
`python -m build`, and `python -m enerqit.lineage_study`.

## Remaining research boundary

No provider interface, concurrent replay prevention, atomic effect enforcement,
independent telemetry, real-time isolation or architecture-level improvement is
established. W3 grades rely on adapter-declared channel identities. Before any
stronger claim, require matched-resource no-history comparisons, held-out
instances, predeclared benefit/overhead thresholds and provider-specific
instrumentation. Do not reinterpret failed or inconclusive trials as success.
