Frequently asked questions
==========================

Do I need a quantum computer?
-----------------------------

No. The current physical estimators, classical solvers and quantum-inspired
simulated bifurcation run on ordinary computers. The small QAOA example uses
classical simulation. Optional dimod and Qiskit adapters export a model;
they do not submit jobs. See :doc:`/quantum` for the distinction and the
additional work a hardware experiment would require.

Has EnerQit demonstrated a quantum-inspired advantage?
------------------------------------------------------

No. Exact enumeration is fastest on the supplied small synthetic benchmark.
The heuristic budgets are reported but are not matched by runtime or number
of evaluations. The :doc:`/benchmarking` describes the measured results and
the stronger comparisons needed before making an advantage claim.

Which energy domains can I use today?
-------------------------------------

The implemented application is solar PV inference and equipment
characterization. The QUBO and solver modules are generic tools, but complete
wind, storage, grid and energy-market applications remain planned. Use the
:doc:`/use_cases` to check the capabilities and evidence requirements of each
current estimator.

Can I infer everything from AC power alone?
-------------------------------------------

No. Geometry fitting also requires weather, location and known system
properties. Full IV curves, exact equipment counts and unrestricted tracker
settings are generally not uniquely determined by aggregate AC power. Each
estimator conditions on its documented measurements and fixed assumptions;
see :doc:`/methods` and :doc:`/data_contract`.

Are the gallery measurements real plant data?
---------------------------------------------

No. All seven bundled examples use deterministic synthetic evidence and
run locally. They demonstrate the workflow and known test conditions, not
validation on an operating asset. A real study needs independently checked
measurements, operating-regime selection and held-out validation.

What does an estimated result mean?
-----------------------------------

``InferenceResult.status == "estimated"`` means the fit passed the checks
implemented for that estimator. It does not prove global identifiability,
absence of bias or agreement with an OEM specification. Inspect its
``diagnostics``, ``warnings``, residuals and data coverage. A result marked
``not_identifiable`` needs more informative evidence or a narrower model.

Can I compare solvers by QUBO energy alone?
-------------------------------------------

Check the original physical residual and explicit feasibility as well.
Penalty strength changes the objective and can leave a low-energy solution
infeasible. Record construction time, solver time, repeated seeds and any
postprocessing. See :doc:`/gallery/plot_coupled_benchmark` for a worked
comparison on the same encoded problem.

Does daily ingestion run or update a production service?
--------------------------------------------------------

No. ``enerqit ingest`` explicitly imports one numeric CSV batch into a local
SQLite study. The :doc:`/workflow` covers late corrections and immutable
analysis snapshots. The repository does not install a recurring task, and
new daily data do not automatically establish a physical change in a plant.

Where should I report a problem or contribute a method?
-------------------------------------------------------

Use the `GitHub issue tracker
<https://github.com/julianascencio/enerqit/issues>`_ with a minimal reproducer,
environment details and expected behaviour. Read the
:doc:`/contributing/index` for source provenance, assumptions, reproducibility
and validation expectations. Project contact is
`contacto@asvaconsulting.com <mailto:contacto@asvaconsulting.com>`_.
