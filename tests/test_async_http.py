"""Tests for async batch fetching (offline, via file:// URLs)."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest import TestCase

from omnisource import async_http


class AsyncHttpTests(TestCase):
    def test_fetch_many_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "a.json"
            second = Path(tmp) / "b.json"
            first.write_text('{"a": 1}', encoding="utf-8")
            second.write_text('{"b": 2}', encoding="utf-8")
            results = async_http.fetch_many([first.as_uri(), second.as_uri()])
        self.assertEqual(len(results), 2)
        self.assertTrue(all(item["ok"] for item in results))
        self.assertTrue(all(item["bytes"] > 0 for item in results))

    def test_fetch_many_missing_file(self) -> None:
        results = async_http.fetch_many(["file:///definitely/not/here-12345.json"])
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]["ok"])
        self.assertTrue(results[0]["error"])

    def test_probe_many_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "a.json"
            target.write_text("{}", encoding="utf-8")
            summary = async_http.probe_many([target.as_uri(), "file:///definitely/not/here-12345.json"])
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["ok"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertIn(summary["backend"], ("aiohttp", "stdlib"))

    def test_async_variant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "a.json"
            target.write_text("{}", encoding="utf-8")
            results = asyncio.run(async_http.fetch_many_async([target.as_uri()]))
        self.assertTrue(results[0]["ok"])


if __name__ == "__main__":
    import unittest

    unittest.main()
