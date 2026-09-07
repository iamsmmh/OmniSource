.PHONY: all build validate test format lint check

PYTHON ?= python3
export PYTHONPATH := src

all: build validate test

build:
	$(PYTHON) scripts/omnisource.py

validate:
	$(PYTHON) scripts/validate.py
	bash scripts/validate_jq.sh

test:
	$(PYTHON) -m unittest discover -s tests

format:
	$(PYTHON) -m ruff format src scripts tests

lint:
	$(PYTHON) -m ruff check src scripts tests

check: lint validate test

