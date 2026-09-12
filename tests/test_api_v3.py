"""Tests for the API v3 helpers and static documents."""

from __future__ import annotations

from unittest import TestCase

from omnisource.api_v3 import (
    apply_filters,
    build_static_documents,
    envelope,
    etag_for,
    feed_version_for,
    paginate,
    slim_app,
    sort_items,
)


class PaginateTests(TestCase):
    def test_pages(self) -> None:
        page = paginate(list(range(5)), page=2, per_page=2)
        self.assertEqual(page["items"], [2, 3])
        self.assertEqual(page["pages"], 3)
        self.assertTrue(page["has_next"])
        self.assertTrue(page["has_prev"])

    def test_clamps(self) -> None:
        page = paginate([1], page=99, per_page=50)
        self.assertEqual(page["page"], 1)
        self.assertFalse(page["has_next"])


class FilterSortTests(TestCase):
    def test_apply_filters(self) -> None:
        items = [{"category": "Games", "name": "A"}, {"category": "Utilities", "name": "B"}]
        self.assertEqual(len(apply_filters(items, {"category": "games"})), 1)
        self.assertEqual(len(apply_filters(items, {"name": "b"})), 1)
        self.assertEqual(len(apply_filters(items, {})), 2)

    def test_sort_items(self) -> None:
        items = [{"name": "B", "score": 1}, {"name": "A", "score": 9}]
        self.assertEqual([item["name"] for item in sort_items(items, "name")], ["A", "B"])
        self.assertEqual([item["name"] for item in sort_items(items, "-score")], ["A", "B"])


class EnvelopeTests(TestCase):
    def test_envelope_with_pagination(self) -> None:
        page = paginate([1, 2, 3], page=1, per_page=2)
        body = envelope(page["items"], feed_version="abc", pagination=page)
        self.assertEqual(body["apiVersion"], "3.0.0")
        self.assertEqual(body["pagination"]["total"], 3)
        self.assertEqual(body["data"], [1, 2])

    def test_etag_stable(self) -> None:
        self.assertEqual(etag_for("x"), etag_for("x"))
        self.assertNotEqual(etag_for("x"), etag_for("y"))

    def test_feed_version_length(self) -> None:
        self.assertEqual(len(feed_version_for({"a": "1"})), 12)


class StaticDocumentsTests(TestCase):
    def test_build_documents(self) -> None:
        bundle = {
            "apps": [
                {
                    "slug": "demo",
                    "name": "Demo",
                    "bundleIdentifier": "com.demo",
                    "developerName": "D",
                    "category": "Utilities",
                    "version": "1.0",
                    "versionDate": "2026-01-01",
                    "iconURL": "",
                    "downloadURL": "https://example.com/d.ipa",
                    "size": 1,
                }
            ],
            "sources": [{"id": "s1", "source": "S"}],
            "trending": {},
            "search_index": {},
            "status": {},
            "security": {},
            "analytics": {},
            "releases": [],
            "generated_at": "2026-01-01",
        }
        docs = build_static_documents(bundle)
        self.assertIn("index.json", docs)
        self.assertIn("apps/demo.json", docs)
        self.assertIn("sources/s1.json", docs)
        self.assertEqual(docs["index.json"]["schemaVersion"], 3)
        self.assertEqual(docs["apps.json"]["pagination"]["total"], 1)

    def test_slim_app(self) -> None:
        slim = slim_app({"slug": "d", "name": "D", "bundleIdentifier": "b", "extra": "gone"})
        self.assertNotIn("extra", slim)
        self.assertEqual(slim["id"], "d")


if __name__ == "__main__":
    import unittest

    unittest.main()
