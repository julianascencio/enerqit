#!/usr/bin/env sh
set -eu
python -m ruff check .
python -m pytest --cov=enerqit --cov-report=term-missing
python ci/run_examples.py --output results/examples
python -m sphinx -W --keep-going -b html docs/sphinx/source docs/_build/html
python -m build
