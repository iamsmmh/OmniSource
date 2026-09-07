.PHONY: build validate format lint

PYTHON ?= python3
export PYTHONPATH := src

build:
	$(PYTHON) scripts/omnisource.py

validate:
	$(PYTHON) scripts/validate.py
	bash scripts/validate_jq.sh

format:
	$(PYTHON) -m ruff format src scripts

lint:
	$(PYTHON) -m ruff check src scripts
