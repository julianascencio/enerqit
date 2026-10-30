PYTHON ?= python
SPHINX_SOURCE = docs/sphinx/source
SPHINX_BUILD = docs/_build/html

.PHONY: docs lint test examples check build

docs:
	$(PYTHON) -m sphinx -W --keep-going -b html $(SPHINX_SOURCE) $(SPHINX_BUILD)

lint:
	$(PYTHON) -m ruff check .

test:
	$(PYTHON) -m pytest --cov=enerqit --cov-report=term-missing

examples:
	$(PYTHON) ci/run_examples.py --output results/examples

check: lint test docs

build:
	$(PYTHON) -m build
