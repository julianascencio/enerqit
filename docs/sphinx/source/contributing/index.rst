Contributing
============

EnerQit welcomes reproducible improvements to energy models, inverse estimators,
optimization methods, evidence utilities, examples and documentation. The
`repository contribution guide
<https://github.com/julianascencio/enerqit/blob/main/CONTRIBUTING.md>`_ is the
complete contribution policy.

Development setup
-----------------

Use a branch in a local checkout and install the development tools:

.. code-block:: bash

   git clone https://github.com/julianascencio/enerqit.git
   cd enerqit
   python -m venv .venv
   source .venv/bin/activate
   python -m pip install -e ".[dev,docs,examples,quantum]"

On Windows PowerShell, activate with ``.venv\Scripts\Activate.ps1``.
The ``quantum`` extra provides local export SDKs; it does not enable remote jobs.
See :doc:`/installation` for the installation and documentation-build options.

Before opening a pull request
-----------------------------

Run the checks relevant to your changes. Scientific or packaging changes should
also pass the complete test suite:

.. code-block:: bash

   python -m ruff check .
   python -m pytest --cov=enerqit --cov-report=term-missing
   python ci/run_examples.py --output results/examples
   make docs
   python -m build

Without ``make``, build the site from the repository root with:

.. code-block:: bash

   python -m sphinx -W --keep-going -b html docs/sphinx/source docs/_build/html

Describe the problem, resulting behavior, verification performed and remaining
limitations in the pull request. The documentation build executes the gallery
and treats warnings as errors.

AI-assisted contributions
-------------------------

EnerQit is **AI-native and human-controlled**. Most code, tests, examples and
documentation are AI-generated or AI-drafted. Human maintainers choose the
scientific direction and source literature, define requirements, and retain
control over review, acceptance and releases.

Contributors should:

* Cite the specific literature, datasets or public technical sources that
  motivate a method or parameter choice. Separate sourced values from engineering
  assumptions and illustrative defaults.
* Describe what AI generated or modified and the review and checks actually
  performed. Do not claim review or validation that has not happened.
* Keep automated checks, human review and real-asset validation distinct.
  Generated implementations and interpretations can contain mistakes, and passing
  tests alone does not establish scientific validity.
* Update the relevant method page, methods note and :doc:`/research/index` when
  sources materially affect implementation or assumptions.

Contributors remain responsible for accuracy, provenance and the right to share
their material. The current implementation has synthetic validation; broader
field validation should grow alongside the project.

Scientific contributions
------------------------

Keep physical forward models separate from inverse estimators and solver
encodings. Use NumPy-style docstrings, SI units, deterministic seeds and explicit
uncertainty or identifiability statements. Use pvlib for established PV physics.

Each new method or use case needs an engineering KPI, input evidence and validity
limits, a meaningful classical baseline, an explanation of the result, relevant
scaling or cost measurements, intended user benefit, and reproduction artifacts.
Report physical residuals and constraint feasibility alongside QUBO energy.
Scientific changes need recovery tests and a relevant failure case.

Label execution accurately: a quantum-inspired algorithm and a statevector
simulator run on classical hardware. A QPU experiment must identify the actual
hardware and execution evidence. SDK imports or model exports do not constitute
quantum computation or prove an advantage.

Documentation and examples
--------------------------

Maintain RST source under ``docs/sphinx/source/``. Generated HTML and gallery
output are build artifacts. User-facing behavior should have conceptual
documentation and API docstrings, with an executable ``docs/examples/`` example
when a figure or end-to-end workflow best explains it.

Examples should state data provenance, use explicit seeds and run locally
without credentials. Remote execution must be opt-in and separate from imports
or the default documentation build.

Issues, attribution and contact
-------------------------------

Bug reports should include package versions, a seed, a synthetic reproducer,
expected physical behavior and the observed result. Use public technical sources
and authorized data; keep client data, credentials, proprietary OEM tables and
operational database exports out of the repository.

EnerQit is created by `ASVA Consulting <https://asvaconsulting.com>`_. Contact
`contacto@asvaconsulting.com <mailto:contacto@asvaconsulting.com>`_. Contributions
are provided under the project's `MIT license
<https://github.com/julianascencio/enerqit/blob/main/LICENSE>`_; submit only
material you have the right to contribute.
