EnerQit
========

.. raw:: html

   <div class="asva-brand">
     <a href="https://asvaconsulting.com">
       <img
         src="_static/asva-consulting.jpg"
         alt="ASVA Consulting"
         width="280"
       >
     </a>
     <p>
       <strong>Created by ASVA Consulting</strong><br>
       <a href="https://asvaconsulting.com">asvaconsulting.com</a><br>
       <a href="mailto:contacto@asvaconsulting.com">contacto@asvaconsulting.com</a>
     </p>
   </div>

**EnerQit** is an open-source Python toolkit for quantum-inspired algorithms
in energy systems, created by **ASVA Consulting**.

It combines physical PV models, configuration inference, equipment
characterization, QUBO/Ising formulations, classical and quantum-inspired
solvers, and reproducible benchmark studies. Solar PV is the first implemented
application domain; wind, storage, grids and energy markets are part of the
:doc:`research roadmap <project>`.

Start here
----------

* Read the :doc:`package overview <user_guide/overview>` to understand the scope.
* Follow :doc:`installation` and run the :doc:`quickstart <start>`.
* Explore the seven executable examples in the :doc:`gallery/index`.
* Use the :doc:`api` for public entry points and module details.
* Check the :doc:`research/index` for the methods, evidence and open questions.

Core modelling idea
-------------------

EnerQit starts with a physical question and the evidence needed to answer it.
Measured signals and known system properties constrain a forward model;
inverse fitting then estimates the unknown parameters. Discrete candidate
configurations can also be encoded as a shared optimization problem so that
different solvers are compared on the same engineering objective.

.. list-table:: From observations to a reproducible result
   :header-rows: 1
   :widths: 27 73

   * - Stage
     - What to examine
   * - Observations
     - Sensor channels, units, timing, location and operating regimes.
   * - Physical model
     - Known capacities, weather inputs, model assumptions and candidate configurations.
   * - Inference or optimization
     - Fit parameters, enforce constraints and compare suitable classical baselines.
   * - Evidence
     - Physical residuals, feasibility, ambiguity, solver budget and runtime.
   * - Reproduction
     - Explicit seeds, provenance-bearing results and immutable evidence snapshots.

The :doc:`data contract <data_contract>`, :doc:`methods <methods>` and
:doc:`benchmark protocol <benchmarking>` explain these stages in detail.

Research status
---------------

Version |release| is a research implementation with synthetic validation.
Quantum-inspired solvers run on classical computers; the small QAOA example
is a classical statevector simulation. Hardware execution is not implemented,
and no quantum advantage is claimed. See :doc:`quantum` for the precise
distinctions and :doc:`use_cases` for the evidence each inference requires.

AI-assisted development
-----------------------

Most EnerQit code, tests, examples and documentation are AI-generated or
AI-drafted. Human maintainers select the scientific references, set the scope
and requirements, and retain control over review, acceptance and releases.

AI-generated content may contain errors or imperfect interpretations of the
selected sources. Review and validation are evolving and are not yet
comprehensive. Automated checks demonstrate implementation behavior; field
validation and scientific confidence require additional evidence. Trace
important assumptions to the :doc:`cited sources <research/index>` and
independently verify results for your application.

Documentation structure
-----------------------

The documentation follows the same scientific-package format as
`OrbitalPV <https://julianascencio.github.io/orbital-pv/>`_: a User Guide,
executable Example Gallery, generated API Reference, Research Library and
Contributing guide.

.. toctree::
   :maxdepth: 2
   :hidden:

   user_guide/index
   gallery/index
   API Reference <api>
   research/index
   contributing/index
