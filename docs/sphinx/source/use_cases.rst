Use-case register and algorithm selection
=========================================

Quantum-inspired optimization is useful to investigate when choices are
discrete and coupled. It does not create information absent from observations.
Use native continuous/convex methods before quantizing every parameter. The
register distinguishes delivered estimators from research proposals; it is not
a feature-completeness claim for every possible PV inverse problem.

.. list-table:: Delivered capabilities
   :header-rows: 1
   :widths: 23 25 28 24

   * - Use case
     - Classical comparator
     - Quantum-inspired formulation
     - Delivered scope
   * - Tilt/azimuth
     - Bounded physical fit and candidate scan
     - One-hot candidate QUBO via bSB
     - Continuous fit and discrete example
   * - Tracker GCR/angle limit
     - Differential evolution and scan
     - One-hot geometry hypotheses via bSB
     - Fixed axis/backtracking assumed
   * - Uniform string topology
     - Integer enumeration
     - Coupled inventory/template QUBO
     - Electrical count estimator; coupling is synthetic surrogate
   * - Coupled block configurations
     - Exact QUBO and feasible-domain enumeration; SA
     - bSB with identical penalties and common polishing
     - Synthetic benchmark, no plant validation
   * - IV sweep parameters
     - Physical nonlinear least squares
     - Discrete model/fault hypothesis selection as an extension
     - Classical estimator delivered; QI extension proposed
   * - MPPT-derived IV curves
     - Selected-parameter physical fit; external PVPRO comparison
     - Coupled module-family/parameter hypotheses
     - Classical estimator delivered; QI extension proposed
   * - Inverter efficiency
     - Nonnegative least squares; external Sandia fit
     - Joint discrete converter-family selection
     - 1-D classical curve; QI not needed for its convex fit
   * - Thermal derating
     - Piecewise constrained fit
     - Discrete cooling-state/threshold hypotheses
     - Single-state classical fit; QI extension proposed
   * - Repeated evidence batches
     - Versioned batch calibration and temporal validation
     - Re-solve selected coupled hypotheses as evidence improves
     - Local store and example; no automated monitoring

.. list-table:: Future research, not implemented
   :header-rows: 1
   :widths: 24 25 29 22

   * - Use case
     - Classical baseline
     - Quantum-inspired candidate
     - Required additional evidence
   * - Unknown inverter inventory
     - Mixed-integer model or constrained template search
     - bSB QUBO selecting converter families/counts
     - Per-device telemetry or informative bounds
   * - MPPT input-to-string mapping
     - Graph matching/MILP
     - Assignment QUBO via bSB or annealing
     - Channel-level electrical traces
   * - Tracker backtracking mode and axis tilt
     - Profile search plus continuous fit
     - Mode/geometry group selection
     - Angle telemetry and low-sun conditions
   * - Bifaciality/albedo/design separation
     - Bayesian physical inference
     - Discrete coupled hypothesis selection
     - Rear irradiance or independent albedo
   * - Static obstruction/shading geometry audit
     - Ray tracing plus sparse regression/MILP
     - Sparse obstruction-library selection
     - Geometry or validated shade templates
   * - Irradiance sensor scale versus installed capacity
     - Constrained errors-in-variables fit
     - Calibration hypothesis selection
     - Independent scale reference
   * - Heterogeneous module-family mixture
     - Mixture models/MILP
     - Constrained component-library selection
     - Resolved IV/channel observations
   * - Next best commissioning measurement
     - Greedy information gain and MILP
     - Budgeted experimental-design QUBO
     - Cost model and parameter uncertainty
   * - Replacement/retrofit scenario selection
     - MILP and dynamic programming
     - Coupled feasible component selection
     - Engineering constraints and cost inputs

Tensor-network probability models or quantum-inspired sampling may become
useful for structured posterior approximations, but are not implemented and
should be compared with sparse graphical models, variational inference and MCMC.
A dense QUBO is not automatically the right representation for every row above.
