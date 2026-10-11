EnerQit
========

.. raw:: html

   <section class="eq-hero" aria-label="About EnerQit">
     <p class="eq-eyebrow">OPEN ENERGY RESEARCH · VERSION 0.1.0</p>
     <h2>Quantum-inspired algorithms.<br>Engineering evidence.</h2>
     <p class="eq-intro">Infer PV configurations, reconstruct field response
     curves, and compare optimization methods on the same problem.</p>
     <div class="eq-actions">
       <a class="eq-button" href="start.html">Start exploring <span aria-hidden="true">→</span></a>
       <a class="eq-button eq-secondary" href="auto_examples/index.html">Browse examples</a>
     </div>
     <p class="eq-meta">Python · MIT licensed · Classical computers · Synthetic validation</p>
   </section>

.. important::

   **Quantum-inspired is not quantum computing.** EnerQit's algorithms run on
   classical computers. The QAOA example is a classical simulation. No quantum
   hardware execution or quantum advantage is demonstrated.

Find your starting point
------------------------

.. raw:: html

   <div class="eq-grid">
     <a class="eq-card" href="use_cases.html">
       <span class="eq-card-number">01 / APPLICATIONS</span>
       <strong>What can we infer?</strong>
       <span>Tilt, trackers, string topology, IV curves, efficiency and thermal limits.
       See the evidence each task needs.</span>
       <span class="eq-card-link">Explore use cases →</span>
     </a>
     <a class="eq-card" href="auto_examples/index.html">
       <span class="eq-card-number">02 / WORKED EXAMPLES</span>
       <strong>See the code and results</strong>
       <span>Seven runnable examples with generated plots, downloadable Python
       scripts and notebooks.</span>
       <span class="eq-card-link">Open the gallery →</span>
     </a>
     <a class="eq-card" href="benchmarking.html">
       <span class="eq-card-number">03 / EVIDENCE</span>
       <strong>Compare the solvers</strong>
       <span>Exact methods, simulated annealing and simulated bifurcation.
       Inspect results, budgets and limitations.</span>
       <span class="eq-card-link">Read the benchmarks →</span>
     </a>
     <a class="eq-card" href="quantum.html">
       <span class="eq-card-number">04 / QUANTUM ROADMAP</span>
       <strong>Understand the distinction</strong>
       <span>What is quantum-inspired today, what can transfer, and what a
       future hardware experiment would need.</span>
       <span class="eq-card-link">Explore the quantum path →</span>
     </a>
   </div>

Start with a physical question
------------------------------

The first application domain is **solar PV**. EnerQit uses pvlib forward physics
to connect observed signals to candidate configurations. Generic QUBO/Ising
interfaces provide a common problem for classical and quantum-inspired solvers.
Wind, storage, grids and energy markets are :doc:`planned domains <project>`.

**AC power alone cannot uniquely recover everything.** Exact equipment counts
and complete IV curves require additional evidence and assumptions. The
:doc:`data contract <data_contract>` and :doc:`methods <methods>` explain what
each result actually means.

Keep up with the project
------------------------

Follow the :doc:`repository guide and roadmap <project>` for where to find code,
changes, contribution rules and current research milestones. The documentation
is built from the same repository and deployed automatically from ``main``.

.. toctree::
   :hidden:
   :caption: Get started

   start
   installation
   use_cases

.. toctree::
   :hidden:
   :caption: Learn by doing

   auto_examples/index
   benchmarking
   workflow

.. toctree::
   :hidden:
   :caption: Scientific reference

   data_contract
   methods
   quantum
   api

.. toctree::
   :hidden:
   :caption: Follow the project

   project
