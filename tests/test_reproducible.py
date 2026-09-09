"""Tests for the generated-artifact reproducibility checker."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

_SCRIPTS = str(Path(__file__).resolve().parents[1] / "scripts")
SPEC = importlib.util.spec_from_file_location("check_reproducible", Path(_SCRIPTS) / "check_reproducible.py")
assert SPEC and SPEC.loader, "cannot load scripts/check_reproducible.py"
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules["check_reproducible"] = MODULE
SPEC.loader.exec_module(MODULE)


class TestReproducible(unittest.TestCase):
    def test_normalizes_dates(self) -> None:
        payload = (
            b'{"generatedAt": "2026-09-09", "lastSync": "2026-09-09", "history": [{"date": "2026-09-09", "apps": 3}]}'
        )
        normalized = MODULE._norm(payload)
        self.assertNotIn(b"2026-09-09", normalized)
        self.assertIn(b'"generatedAt": "<DATE>"', normalized)

    def test_matches_patterns(self) -> None:
        self.assertTrue(MODULE._matches("feeds/discovery.json", "feeds/*.json"))
        self.assertTrue(MODULE._matches("apps/alpha/index.html", "apps/*/index.html"))
        self.assertFalse(MODULE._matches("apps/alpha/assets/x.css", "apps/*/index.html"))
        self.assertTrue(MODULE._matches("README.md", "README.md"))
        self.assertFalse(MODULE._matches("docs/API.md", "README.md"))


if __name__ == "__main__":
    unittest.main()
