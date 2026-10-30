Research Library
================

EnerQit connects implemented methods to a selected scientific evidence base.
The `methods note on GitHub
<https://github.com/julianascencio/enerqit/blob/main/paper/README.md>`_ records
the initial references and separates physical prediction, inverse-problem
identifiability, binary encoding and solver performance. Evidence at one layer
does not establish validity at the others.

Use the :doc:`/methods` and :doc:`/quantum` guides for the implemented assumptions
and conventions, and the :doc:`/api` for callable behavior.

Sources and their role
----------------------

.. list-table:: Current evidence base
   :header-rows: 1
   :widths: 30 40 30

   * - Source
     - Role in EnerQit
     - Scope of the connection
   * - `Holmgren et al. (2018), pvlib python
       <https://doi.org/10.21105/joss.00884>`_
     - PV forward physics used by ``enerqit.pvsystem`` and the inverse estimators.
     - EnerQit builds on pvlib; it does not establish new validation of every
       underlying physical model.
   * - `De Soto et al. (2006), Improvement and validation of a model for
       photovoltaic array performance
       <https://doi.org/10.1016/j.solener.2005.06.010>`_
     - Reference-parameter translation through pvlib for the single-diode
       calculations in ``enerqit.ivtools.sdm``.
     - Fitted curves remain conditional on effective irradiance, cell temperature
       and the parameters held fixed.
   * - `Goto et al. (2021), High-performance combinatorial optimization based
       on classical mechanics <https://doi.org/10.1126/sciadv.abe7953>`_
     - Ballistic simulated-bifurcation concept behind the transparent NumPy
       reference solver in ``enerqit.solvers.bifurcation``.
     - This is a classical CPU implementation. It does not reproduce the paper's
       hardware, throughput or benchmark claims.
   * - `DuraMAT PVPRO <https://github.com/DuraMAT/pvpro>`_
     - A published alternative for operational PV parameter extraction and a
       potential external benchmark.
     - EnerQit's operational MPP fit is its own implementation, not PVPRO.
   * - `Official pvlib inverter model documentation
       <https://pvlib-python.readthedocs.io/en/stable/reference/inverter.html>`_
     - Context for inverter forward models and stronger multi-voltage
       alternatives to the current efficiency fit.
     - The existing efficiency estimator fits a simpler nonnegative loss model;
       it does not implement Sandia parameter fitting.
   * - `IBM QAOA tutorial
       <https://quantum.cloud.ibm.com/docs/en/tutorials/quantum-approximate-optimization-algorithm>`_
     - Background for the QAOA cost/mixer concept and a future gate-model
       workflow.
     - EnerQit's small statevector demonstrator runs locally in NumPy. Qiskit
       export does not execute it on a quantum processor.
   * - `D-Wave model conventions
       <https://docs.dwavequantum.com/en/latest/concepts/models.html>`_
     - QUBO/Ising and binary quadratic model context for local export.
     - EnerQit tests its own signs, constants and bitstring energies; hardware
       embedding and annealer execution are not implemented.

Evidence available today
------------------------

The :doc:`/gallery/index` contains deterministic synthetic demonstrations of
PV configuration inference, equipment characterization, constrained optimization
and daily evidence handling. They show how to reproduce the code and inspect
outputs; they are not real-plant validation studies.

The :doc:`/benchmarking` page presents recorded small synthetic comparisons,
downloadable results and the evaluation protocol. Exact enumeration is fastest
on those instances. Heuristic budgets are explicitly reported, and are not
matched by runtime or evaluation count. No quantum-inspired or quantum-hardware
advantage has been established.

The `validation directory
<https://github.com/julianascencio/enerqit/tree/main/validation>`_ records the
delivered checks and environment. Current commit checks are available in
`GitHub Actions <https://github.com/julianascencio/enerqit/actions>`_. Keep those
implementation checks separate from field validation or globally calibrated
uncertainty claims.

How the evidence base develops
------------------------------

Developers select the papers, datasets and technical sources that define the
scientific direction. AI helps with implementation and documentation, while
maintainers retain control over review and acceptance. Validation is evolving;
generated code or interpretations may contain mistakes and need comparison with
the cited source and appropriate numerical evidence.

A useful research addition states the engineering question, the evidence needed,
the implemented assumptions and a reproducible comparison against a meaningful
classical baseline. See :doc:`/contributing/index` for the contribution process.

Planned research
----------------

The `roadmap <https://github.com/julianascencio/enerqit/blob/main/ROADMAP.md>`_
tracks validation on held-out field data, stronger optimization baselines,
scaling studies and future wind, storage, grid and market applications. These
future domains and hardware experiments remain research directions; consult the
:doc:`/use_cases` register for what the package currently implements.
