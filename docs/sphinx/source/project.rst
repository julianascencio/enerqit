Repository guide and roadmap
============================

`Open the source repository <https://github.com/julianascencio/enerqit>`_ to
inspect the code, follow development, or report an issue. This site follows
the ``main`` branch; the package version is currently 0.1.0.

.. _ai-native-development:

AI-native, human-controlled development
---------------------------------------

Most of EnerQit's code, tests, examples and documentation are AI-generated.
Human maintainers set the direction, define scientific requirements, and retain
control over review, acceptance and releases. AI is a core part of how the
repository is developed.

Human control does not mean every line has received expert review. Automated
checks, human review and validation on real assets are different forms of
evidence and should be reported separately. Contributions should describe AI
involvement and the review and checks actually performed. The current release
remains a research implementation validated on synthetic evidence.

Where the content lives
-----------------------

.. list-table:: Repository map
   :header-rows: 1
   :widths: 30 70

   * - Directory
     - What you will find
   * - ``enerqit/solar/``
     - Public solar inference entry points; start with :doc:`api`.
   * - ``enerqit/``
     - Physical fits, data validation, QUBO/Ising encoding and result records.
   * - ``enerqit/solvers/``
     - Classical baselines, simulated bifurcation and optional quantum exports.
   * - ``docs/examples/``
     - The scripts executed to produce the :doc:`example gallery <auto_examples/index>`.
   * - ``docs/notebooks/``
     - An introductory inverse-study notebook.
   * - ``benchmarks/``
     - Comparison runner and downloadable :doc:`reference results <benchmarking>`.
   * - ``tests/`` and ``validation/``
     - Recovery/failure tests and the delivered environment and validation report.
   * - ``docs/sphinx/source/``
     - The source of these pages. Use the source button on a page to inspect it.

Follow changes
--------------

* `Changelog <https://github.com/julianascencio/enerqit/blob/main/CHANGELOG.md>`_
  — changes included in each version.
* `Roadmap <https://github.com/julianascencio/enerqit/blob/main/ROADMAP.md>`_
  — planned research and the classical baseline required for each domain.
* `Commit history <https://github.com/julianascencio/enerqit/commits/main/>`_
  — the most recent source and documentation changes.
* `Issues <https://github.com/julianascencio/enerqit/issues>`_
  — bug reports and proposed work.
* `Automated checks <https://github.com/julianascencio/enerqit/actions>`_
  — Python tests, documentation builds and site deployments.

What is available and what comes next
-------------------------------------

**Available:** PV orientation and tracker inference, conditional equipment
characterization, synthetic configuration benchmarks, local evidence storage,
classical and quantum-inspired CPU solvers, and quantum model export examples.

**Planned:** validation on real held-out assets, stronger native optimization
baselines at scale, and separate storage, wind, grid and market applications.
Future quantum hardware experiments require an explicitly labeled backend and
comparison against the same classical engineering objectives.

Contribute with evidence
------------------------

Read `CONTRIBUTING.md
<https://github.com/julianascencio/enerqit/blob/main/CONTRIBUTING.md>`_ before
submitting changes. Each new method or use case needs an engineering KPI,
validity limits, a meaningful classical baseline, explanation of results,
scaling/cost evidence, intended user benefit and reproducibility artifacts.

EnerQit is released under the `MIT license
<https://github.com/julianascencio/enerqit/blob/main/LICENSE>`_. It uses pvlib
for PV forward physics and is independent of, and not endorsed by, pvlib.

How this site updates
---------------------

``.github/workflows/pages.yml`` builds the Sphinx documentation and executes the
example gallery on pushes to ``main``. GitHub Pages publishes the successful
build. Failed builds do not replace the last successfully deployed site.

To preview the same content locally, follow the :doc:`installation` instructions.
No separate copy of the documentation needs to be edited.
