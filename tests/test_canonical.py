"""Tests for the canonical app database (deduplication)."""

from __future__ import annotations

from unittest import TestCase

from omnisource.canonical import build_canonical, find_duplicates, group_duplicates, match_keys, merge_group


def _app(name: str, bundle: str, **overrides) -> dict:
    app = {
        "name": name,
        "bundleIdentifier": bundle,
        "developerName": "Dev",
        "version": "1.0",
        "versionDate": "2026-01-01",
        "downloadURL": f"https://example.com/{bundle}.ipa",
        "size": 10,
        "source": "https://example.com/apps.json",
    }
    app.update(overrides)
    return app


class MatchKeysTests(TestCase):
    def test_bundle_key_first(self) -> None:
        keys = match_keys(_app("A", "com.a"))
        self.assertTrue(keys[0].startswith("bundle:"))

    def test_repo_key_extracted(self) -> None:
        app = _app("A", "com.a", website="https://github.com/octo/repo/releases")
        self.assertIn("github:octo/repo", match_keys(app))


class GroupingTests(TestCase):
    def test_same_bundle_merges(self) -> None:
        groups = group_duplicates([_app("A", "com.a"), _app("A 2", "com.a"), _app("B", "com.b")])
        self.assertEqual(len(groups), 2)
        self.assertEqual(sorted(len(group) for group in groups), [1, 2])

    def test_merge_keeps_union(self) -> None:
        merged = merge_group(
            [
                _app("A", "com.a", versionDate="2026-01-01", source="https://one.test/f.json"),
                _app("A", "com.a", versionDate="2026-02-01", source="https://two.test/f.json"),
            ]
        )
        self.assertEqual(merged["duplicates"], 2)
        self.assertEqual(len(merged["sources"]), 2)
        self.assertEqual(merged["versionDate"], "2026-02-01")

    def test_build_canonical_counts(self) -> None:
        doc = build_canonical([_app("A", "com.a"), _app("A", "com.a"), _app("B", "com.b")])
        self.assertEqual(doc["count"], 2)
        self.assertEqual(doc["inputRecords"], 3)
        self.assertEqual(doc["mergedDuplicates"], 1)

    def test_find_duplicates(self) -> None:
        dupes = find_duplicates([_app("A", "com.a"), _app("A", "com.a")])
        self.assertEqual(len(dupes), 1)
        self.assertEqual(dupes[0]["count"], 2)


if __name__ == "__main__":
    import unittest

    unittest.main()
