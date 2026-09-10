.PHONY: all build publish site serve smoke validate test format lint check clean

PYTHON ?= python3
PORT ?= 8000
export PYTHONPATH := src

all: build check

# Refresh generated source feeds from their configured upstreams.
build:
	$(PYTHON) scripts/omnisource.py

# Publish the generated flat/API URLs into the repository root (branch deploy).
publish:
	$(PYTHON) scripts/publish_root.py

# Assemble the exact static bundle deployed to GitHub Pages.
site:
	$(PYTHON) scripts/build_site.py

# Preview the assembled website locally at http://localhost:$(PORT).
serve: site
	$(PYTHON) -m http.server $(PORT) --bind 0.0.0.0 --directory _site

# Build the site, serve it locally and verify every page/feed/API URL works.
smoke:
	$(PYTHON) scripts/smoke_test.py

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
	$(PYTHON) scripts/publish_root.py --check
	$(PYTHON) scripts/merge_feeds.py --check
	$(PYTHON) scripts/check_reproducible.py --diff
	$(PYTHON) scripts/smoke_test.py
	$(PYTHON) -m ruff format --check src scripts tests

clean:
	rm -rf _site
