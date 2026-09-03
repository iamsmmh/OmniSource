.PHONY: test validate format lint build api

PYTHON ?= python3
export PYTHONPATH := src

build:
	$(PYTHON) scripts/omnisource.py

validate:
	$(PYTHON) scripts/validate.py
	bash scripts/validate_jq.sh

format:
	$(PYTHON) -m ruff format src scripts tests

lint:
	$(PYTHON) -m ruff check src scripts tests

# No network is required for the test suite.
test:
	$(PYTHON) -m unittest discover -s tests -v

api:
	$(PYTHON) scripts/api_server.py --root . --host 0.0.0.0 --port 8000
