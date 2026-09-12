.PHONY: all build publish site serve smoke validate test format lint check audit clean version

PYTHON ?= python3
PORT ?= 8000
export PYTHONPATH := src

all: build check

# Print the installed OmniSource version.
version:
	$(PYTHON) -m omnisource --version

# Refresh generated source feeds from their configured upstreams.
build:
	$(PYTHON) scripts/omnisource.py

# Publish /apps.json + the api/ mirror into the repository root.
publish:
	$(PYTHON) scripts/publish_root.py

# Assemble the exact static bundle deployed to GitHub Pages.
site:
	$(PYTHON) scripts/build_site.py

# Preview the assembled website locally at http://localhost:$(PORT).
serve: site
	$(PYTHON) -m http.server $(PORT) --bind 0.0.0.0 --directory _site

# Build the site, serve it locally and verify every page/feed/API URL works.
# `--root` additionally verifies the repository tree surface (/apps.json,
# feeds/, api/) that GitHub Pages serves without a build step.
smoke:
	$(PYTHON) scripts/smoke_test.py
	$(PYTHON) scripts/smoke_test.py --root --no-build

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
	$(PYTHON) scripts/smoke_test.py --root --no-build
	$(PYTHON) -m ruff format --check src scripts tests

# Structural audits (dead code, duplication, i18n, performance, workflows,
# accessibility, links/SEO) into reports/*.md — read-only over the tree.
audit:
	$(PYTHON) scripts/audit.py

clean:
	rm -rf _site
