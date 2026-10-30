Installation
============

EnerQit requires Python 3.11 or newer. The repository's CI checks Python
3.11–3.13. Install from the source repository in a clean virtual environment:

.. code-block:: bash

   git clone https://github.com/julianascencio/enerqit.git
   cd enerqit
   python -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -e .

On Windows PowerShell, replace the activation command with
``.venv\Scripts\Activate.ps1``. The editable installation makes local source
changes available to the current environment.

Run a first study
-----------------

The command-line demo writes synthetic observations and a JSON inference
report with provenance:

.. code-block:: bash

   enerqit demo --output results/demo
   enerqit benchmark --output results/benchmark.jsonl

For the Python API version, follow the :doc:`start`. No account, credentials
or quantum processor is needed for these commands.

Optional dependencies
---------------------

.. list-table:: Installation extras
   :header-rows: 1
   :widths: 30 70

   * - Command
     - Purpose
   * - ``python -m pip install -e '.[examples]'``
     - Matplotlib and JupyterLab for local plots and notebooks.
   * - ``python -m pip install -e '.[docs]'``
     - Sphinx, the PyData theme and Sphinx-Gallery for the documentation site.
   * - ``python -m pip install -e '.[dev]'``
     - Ruff, pytest, coverage and package-build tooling.
   * - ``python -m pip install -e '.[quantum]'``
     - dimod and Qiskit model export adapters; this does not enable hardware
       execution.

Combine extras for a development checkout:

.. code-block:: bash

   python -m pip install -e '.[dev,docs,examples,quantum]'
   python -m pytest -q

The NumPy QAOA statevector example runs without the optional quantum SDKs.
Install the quantum extra when testing or using the dimod/Qiskit exporters.
The notebook in ``docs/notebooks/`` requires EnerQit in the notebook kernel's
Python environment.

Build the documentation
-----------------------

The documentation uses the same Sphinx and PyData layout as Orbital-PV.
From the repository root, after installing the docs extra:

.. code-block:: bash

   make docs

If Make is unavailable, run the equivalent command directly:

.. code-block:: bash

   python -m sphinx -W --keep-going -b html docs/sphinx/source docs/_build/html

The build executes the gallery and treats documentation warnings as errors.
Open ``docs/_build/html/index.html`` to view the result. To save figures
without building the site:

.. code-block:: bash

   python ci/run_examples.py --output results/examples

Reproduce the dependency environment
------------------------------------

``uv.lock`` records the dependency solution. If you use uv, synchronize the
same extras with:

.. code-block:: bash

   uv sync --extra dev --extra docs --extra examples --extra quantum

The lock file records dependencies; it does not establish that every supported
platform was tested. Check `GitHub Actions
<https://github.com/julianascencio/enerqit/actions>`_ for the status of a
specific commit. Pull requests build the documentation for validation;
successful builds from ``main`` are published to GitHub Pages.
