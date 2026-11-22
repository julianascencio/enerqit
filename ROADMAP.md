# EnerQit roadmap

EnerQit develops reproducible algorithms for the energy sector. Quantum-inspired
methods are classical algorithms running on classical computers. Future quantum
hardware experiments will be a separate, explicitly labeled execution path.

## Implemented in 0.1.0

- Generic weighted template QUBOs, inventory equalities and Ising exports.
- Classical exact/native enumeration, simulated annealing and quantum-inspired
  ballistic simulated bifurcation.
- Solar configuration inference and effective equipment characterization.
- Reproducible benchmarks, synthetic evidence, tests and executable examples.
- Local classical QAOA simulation and optional dimod/Qiskit model exports.

- Duration-aware battery portfolio selection and registered external agent studies.
- Industrial batch scheduling with deadlines, scenario-specific grid ceilings,
  native MILP, conservative QUBO and independently evaluated rebound overload.

- Single-interval DC network dispatch, independently audited relaxations and line-rating screening.
  Preventive connected line-outage DC screening is implemented; real topology calibration, AC power flow and operational N-1 validation remain outstanding.

- Cyclic chronological renewable firming with losses, MILP mode exclusivity and LP lower bounds. Multi-year field calibration remains open.

- Exact small-fleet probabilistic window adequacy and finite firm-capacity offers; joint-outage calibration and chronological reliability remain open.

## Next research milestones — not implemented yet

| Domain | Candidate problem | Required classical baseline |
|---|---|---|
| Solar | Coupled configuration inference on real held-out assets | Physical fitting, native MILP/MIQP or decomposition |
| Storage | Battery schedule selection with physical constraints | LP/MILP and dynamic programming |
| Wind | Coupled layout or operating-hypothesis selection | Established continuous/mixed-integer methods |
| Grids | Network reconfiguration and discrete resource placement | Power-flow-aware MILP/MINLP and heuristics |
| Markets | Constrained bidding/scenario selection | Stochastic programming and robust optimization |
| Experimental design | Select measurements under a budget | Greedy information gain and MILP |
| Quantum hardware | Small, verified QUBO/Ising experiments | The same native and encoded classical objectives |

Every milestone needs engineering KPIs, a clear intended user benefit,
identifiability/validity evidence, explanations, scaling and cost measurements,
deterministic seeds, structured logs, data provenance and run instructions.
Use real held-out evidence before field claims. Compare total costs and matching
solution quality before any algorithmic advantage claim.

The earlier QuantumPV prototype is the basis of the first solar application.
New domain modules should reuse the generic interfaces where scientifically
appropriate; energy-specific constraints and physics remain explicit.

## Application validation lab delivered

- Matched search budgets on growing coupled-inventory instances; native sparse MILP,
  SA, bSB and block-coordinate experiments, with timeouts and late batches retained.
- Sparse cyclic storage constraints up to 87,840 intervals; physical net-balance LP
  for the restricted no-grid/free-curtailment firming model.
- Strict UTC CSV ingestion, training-only normalization, frozen chronological
  holdout replay and explicit calendar-capacity/cost scenarios.
- Shared JSONL experiment records and actual registered-agent/direct-script
  repeatability comparison.

Still open: co-located multi-year site evidence; cycle/thermal aging calibration;
optimized large native MIQP/CP-SAT baselines; statistically powered matched-target
comparisons; live-agent human-effort studies; independent human scientific review;
physical QPU execution. See the validation-lab guide for reproducible commands.

Implemented finite-support probability-robust reserve screening; statistical radius calibration and missing-state validation remain open.

Implemented sequential no-recharge battery reserve screening. Initial SOC and outage-path calibration remain open.

Implemented shared export allocation for initial AC energy budgets. Site-specific charging, hydro head, fees and terminal values remain open.

Implemented export-ceiling curtailment recovery ledger; site charging permissions, degradation and settlement validation remain open.

Implemented discrete ramp deliverability screening; continuous ramp energy, forecast uncertainty and operator calibration remain open.

Implemented temporal renewable capacity procurement. Forecast uncertainty, network deliverability and attribute ownership remain open.

Implemented bidirectional activation initial-energy envelopes and preparation screening; correlated activation calibration, thermal/ramp limits and opportunity-cost validation remain open.

Implemented single-reservoir constant-head allocation with minimum releases and terminal inventory. Plant calibration, variable head and water-value uncertainty remain open.
