# Methods note

EnerQit separates four concerns: physical forward prediction, statistical
identifiability of an inverse problem, constrained binary encoding, and solver
performance. Success at one layer does not establish success at the others.

Configuration recovery conditions on measured weather, known capacity and a
simplified loss model. Equipment curves are estimated only over observable
regimes. A single-diode model can reconstruct an IV curve from operating MPP
evidence under sufficiently informative conditions and parameter assumptions;
power alone generally cannot identify its full parameterization.

The binary layer encodes weighted template residuals with one-hot and inventory
equalities. It preserves constants and documents QUBO/Ising sign conventions.
Classical exact, native feasible enumeration and Metropolis annealing provide
baselines for a transparent ballistic simulated-bifurcation reference solver.
Optional dimod/Qiskit exports preserve the problem, not the classical solver
dynamics. Quantum hardware advantage is a separate empirical question.

Primary references:

- Holmgren et al. (2018), *pvlib python: a python package for modeling solar
  energy systems*, JOSS, https://doi.org/10.21105/joss.00884.
- De Soto et al. (2006), *Improvement and validation of a model for photovoltaic
  array performance*, https://doi.org/10.1016/j.solener.2005.06.010.
- Goto et al. (2021), *High-performance combinatorial optimization based on
  classical mechanics*, https://doi.org/10.1126/sciadv.abe7953.
- DuraMAT PVPRO, operational PV parameter extraction source and references:
  https://github.com/DuraMAT/pvpro.
- Official pvlib inverter model documentation:
  https://pvlib-python.readthedocs.io/en/stable/reference/inverter.html.
- IBM QAOA tutorial:
  https://quantum.cloud.ibm.com/docs/en/tutorials/quantum-approximate-optimization-algorithm.
- D-Wave model conventions:
  https://docs.dwavequantum.com/en/latest/concepts/models.html.

The delivered synthetic experiments verify implementation behavior; they do
not establish a field performance result, novelty, patentability, OEM agreement,
or quantum-inspired advantage.

## Battery availability portfolio study (10 November 2026)

The [duration-aware portfolio study](../docs/sphinx/source/battery_portfolio.rst)
adds a fixed-fee binary cover model constrained by AC power, DC usable energy,
SOC, SOH, efficiency and export headroom. It compares SciPy/HiGHS MILP, native
subset enumeration, conservative QUBO exact enumeration and the existing SA/bSB
solvers. [SciPy MILP documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html)
defines the classical solver interface; Goto et al. (2021), cited above, motivates
the existing classical bSB method. The algebraic penalty bound and rounding
limits are derived in the study and exhaustively tested on small instances.

Official Elexon SYSWARN metadata and NESO's GC0166 update motivate the problem;
all battery offers and fees are synthetic. The numerical result does not
validate Grid Code compliance, reconstruct dispatch, or establish quantum
advantage. The complete agent trace, solver budgets and environment are in
[the recorded benchmark](../benchmarks/results/battery-engineer-20261110.json).
This contribution was AI-generated and checked with physical accounting tests,
independent exact oracles and runnable examples; human and field review remain
separate from these implementation checks.

## Industrial batch flexibility (second 10 November 2026 run)

[The batch scheduling study](../docs/sphinx/source/batch_flexibility.rst) is
motivated by the IEA's 5 November Spain energy-policy review. Its scheduling
formulation is an independent engineering interpretation, not an IEA algorithm
or empirical reproduction. All site inputs are synthetic. The native binary
start-time model uses SciPy/HiGHS MILP, compared against actual-start enumeration
and the existing exact/SA/bSB backends. Conservative upper rounding of demand and
lower rounding of headroom preserves the direction of physical feasibility.
Per-job cost shifting yields a nonnegative objective and a bounded sufficient
penalty even with negative energy prices; exhaustive state tests check this.

Every job's energy and completion deadline are preserved. One common schedule
meets all declared scenarios, without suggesting a calibrated risk probability.
The study retains failed/inferior solver outcomes, deterministic sensitivities
and 4/8/16-job resource measurements. The complete result is in
`benchmarks/results/flexibility-engineer-20261110.json`. Native MILP remains the
recommendation; no hardware, field-validation or quantum-advantage claim is made.
This AI-generated implementation has automated accounting/oracle checks and
requires separate human and field review before operational use.

## Network curtailment screening (10 November 2026)

The [study](../docs/sphinx/source/network_curtailment.rst) uses standard lossless
DC nodal/angle constraints, as documented in [PyPSA's power-flow reference](https://docs.pypsa.org/latest/user-guide/optimization/power-flow/).
Ember's [5 November grid guide](https://ember-energy.org/latest-insights/building-a-grid-for-the-age-of-power/)
is context, not calibration. The independently authored synthetic triangle has an
analytic 120 MW renewable transfer limit, allowing an objective and physical
feasibility reference independent of LP assembly. Classical LP solves this convex
problem; quantum-inspired methods are not needed. The AI-generated implementation
is checked automatically; field validation and human scientific review remain open.
