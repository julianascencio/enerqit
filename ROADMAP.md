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
