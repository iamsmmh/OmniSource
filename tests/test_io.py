"""Tests for I/O operations and atomic file publishing."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import json
import tempfile
import unittest
from pathlib import Path

from omnisource.io import atomic_write_many, dumps, dumps_pretty, read_json, write_json


class TestIO(unittest.TestCase):
    def test_dumps(self) -> None:
        data = {"name": "test", "val": 1}
        rendered = dumps(data)
        self.assertTrue(rendered.endswith("\n"))
        self.assertEqual(json.loads(rendered), data)

    def test_dumps_pretty_indents(self) -> None:
        data = {"name": "test", "apps": [1, 2]}
        rendered = dumps_pretty(data)
        self.assertTrue(rendered.endswith("\n"))
        self.assertIn("\n  ", rendered)  # multi-line / indented, not compact
        self.assertEqual(json.loads(rendered), data)

    def test_atomic_write_many_pretty_selective(self) -> None:
        # Only documents the ``pretty`` predicate accepts are indented; the
        # rest stay compact so feed clients keep their single-line payloads.
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pretty_doc = root / "sources.json"
            compact_doc = root / "apps.json"
            docs = {
                pretty_doc: {"sources": [{"id": "a/b", "apps": []}]},
                compact_doc: {"apps": [{"name": "A"}]},
            }
            changed = atomic_write_many(docs, pretty=lambda path: path.name == "sources.json")
            self.assertEqual(len(changed), 2)
            self.assertIn("\n  ", pretty_doc.read_text(encoding="utf-8"))
            self.assertNotIn("\n  ", compact_doc.read_text(encoding="utf-8"))

    def test_write_and_read_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.json"
            data = {"key": "value", "list": [1, 2, 3]}

            # First write should return True (changed)
            self.assertTrue(write_json(file_path, data))
            self.assertTrue(file_path.exists())

            # Read back
            read_back = read_json(file_path)
            self.assertEqual(read_back, data)

            # Second write with same data should return False (no change)
            self.assertFalse(write_json(file_path, data))

    def test_atomic_write_many(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            doc1 = root / "dir1" / "doc1.json"
            doc2 = root / "dir2" / "doc2.json"

            docs = {
                doc1: {"id": 1},
                doc2: {"id": 2},
            }
            changed = atomic_write_many(docs)
            self.assertEqual(len(changed), 2)
            self.assertEqual(read_json(doc1), {"id": 1})
            self.assertEqual(read_json(doc2), {"id": 2})

            # Re-running with unchanged data
            changed_again = atomic_write_many(docs)
            self.assertEqual(len(changed_again), 0)


if __name__ == "__main__":
    unittest.main()
