Package overview
================

EnerQit is an open-source Python toolkit for quantum-inspired algorithms in
energy systems. Its first application is **solar PV inference**: using physical
forward models and observations to estimate system configuration and equipment
response. The generic binary optimization tools allow classical and
quantum-inspired solvers to work on the same encoded problem.

The project is created by `ASVA Consulting <https://asvaconsulting.com>`_.
Its modelling and documentation follow the scientific Python package pattern:
small public functions, explicit assumptions, executable examples and
reproducible comparisons.

What is implemented
-------------------

.. list-table:: Current capabilities
   :header-rows: 1
   :widths: 28 47 25

   * - Area
     - Implemented capability
     - Learn more
   * - PV geometry
     - Fit fixed-array tilt and azimuth, or tracker GCR and rotation limit,
       conditional on known system properties and weather.
     - :doc:`/methods`
   * - Electrical characterization
     - Fit IV model parameters, uniform string counts, effective inverter
       efficiency and thermal limiting envelopes from suitable evidence.
     - :doc:`/use_cases`
   * - Optimization
     - Encode template residuals and equality constraints as QUBOs; compare
       exact enumeration, native grouped enumeration, simulated annealing
       and ballistic simulated bifurcation.
     - :doc:`/quantum`
   * - Study evidence
     - Ingest timestamped numeric batches into a local SQLite study, preserve
       batch provenance and record analysis snapshots.
     - :doc:`/workflow`
   * - Quantum model preparation
     - Export to dimod or Qiskit and explore a small NumPy QAOA statevector
       simulation.
     - :doc:`/gallery/plot_quantum_bridge`

Wind, storage, grids and energy markets are future application domains, as
described in the :doc:`/project`. They are not implemented applications in
version 0.1.0.

How a study fits together
-------------------------

1. **Define the physical question.** Choose the unknowns and fix the quantities
   supported by inventory or independent measurements.
2. **Prepare the evidence.** Check units, timezone, sensor boundaries and
   operating regimes against the :doc:`/data_contract`.
3. **Establish a physical baseline.** Use a continuous fit or direct candidate
   enumeration when it suits the problem.
4. **Compare solvers where useful.** Encode coupled discrete choices once,
   then compare the same engineering objective and constraints.
5. **Inspect and retain the result.** Review residuals, feasibility, ambiguity,
   assumptions and provenance alongside any parameter estimate.

Public entry points
-------------------

Use ``enerqit.solar`` for the initial solar application, ``enerqit.solvers``
for interchangeable binary solvers and ``enerqit.qubo`` for problem construction.
``enerqit.datasets`` provides deterministic synthetic inputs;
``enerqit.timeseries`` provides the local study store. The :doc:`/api` describes
these functions and their underlying modules.

The :doc:`/start` begins with a fixed-array fit that runs on an ordinary
computer. The :doc:`/gallery/index` expands that workflow to trackers,
electrical curves, coupled benchmarks and daily evidence.

Evidence and scope
------------------

The supplied examples and benchmark data are synthetic. They exercise
implementation behaviour and failure checks; they do not establish field
accuracy or performance on an unseen plant. Full IV curves and equipment
counts cannot generally be recovered from aggregate AC power alone.

Quantum-inspired solvers execute on a classical CPU. The QAOA demonstration is
also classical simulation. There is no bundled quantum hardware execution or
demonstrated quantum advantage. On the supplied small benchmark, exact
enumeration is the fastest method; see the :doc:`/benchmarking` for the recorded
budgets, results and limitations.

Most code and documentation are AI-generated under maintainer direction.
Review and validation are evolving, so source interpretations and results may
contain errors. See the :ref:`development process <ai-native-development>` and
:doc:`/research/index` for the evidence behind the project.
