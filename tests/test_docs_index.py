"""Tests for the docs hub: reference cards vs the historical archive."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from omnisource.docs_index import build_docs_index


class DocsIndexTests(unittest.TestCase):
    def _docs(self, tmpdir: str) -> Path:
        docs = Path(tmpdir) / "docs"
        (docs / "archive").mkdir(parents=True)
        (docs / "API.md").write_text("# API reference\n\nEvery endpoint.\n", encoding="utf-8")
        (docs / "archive" / "FINAL-SUMMARY.txt").write_text("OLD BUILD NOTES\n", encoding="utf-8")
        (docs / "archive" / "REPOSITORY.md").write_text("# Repository guide\n\nOlder layout notes.\n", encoding="utf-8")
        return docs

    def test_reference_documents_are_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = self._docs(tmpdir)
            index = build_docs_index(docs, base_url="https://example.com")
            page = Path(index).read_text(encoding="utf-8")
        self.assertIn('href="API.md"', page)

    def test_archive_files_are_linked_not_lost(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = self._docs(tmpdir)
            index = build_docs_index(docs, base_url="https://example.com")
            page = Path(index).read_text(encoding="utf-8")
        self.assertIn('href="archive/REPOSITORY.md"', page)
        self.assertIn('href="archive/FINAL-SUMMARY.txt"', page)
        self.assertIn("Archive", page)
        # The one-off write-up must not be promoted into the reference grid.
        self.assertNotIn('class="docs-card panel" href="archive/', page)
