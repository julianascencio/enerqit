Installation and first run
==========================

Use Python 3.11 or newer in a clean environment. CI checks Python 3.11–3.13;
the delivered local build was tested on 3.12. Clone the repository first::

   git clone https://github.com/julianascencio/enerqit.git
   cd enerqit
   python -m venv .venv
   source .venv/bin/activate
   python -m pip install -e '.[dev,docs,examples]'
   enerqit demo --output results/demo
   enerqit benchmark --output results/benchmark.jsonl
   python -m pytest -q

On Windows PowerShell, activate with ``.venv\Scripts\Activate.ps1``.
Install ``.[quantum]`` for dimod and Qiskit export adapters. No account or QPU
is needed for the local QAOA statevector example.

Build this documentation, including executed example figures::

   python -m sphinx -W --keep-going -b html docs/sphinx/source docs/_build/html

Then open ``docs/_build/html/index.html`` locally. The notebook in
``docs/notebooks/`` assumes the package is installed in the notebook kernel.
For saved example figures without Sphinx::

   python ci/run_examples.py --output results/examples

The dependency lock is for reproducible installation, not proof that every
supported Python/platform combination was exercised locally. Check
`GitHub Actions <https://github.com/julianascencio/enerqit/actions>`_ for the
status of each commit. The documentation site deploys successful builds from
``main`` automatically.
