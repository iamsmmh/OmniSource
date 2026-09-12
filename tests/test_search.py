"""Tests for the advanced search engine (offline)."""

from __future__ import annotations

from unittest import TestCase

from omnisource.search import fuzzy_score, matches_filters, score_app, search, tokenize


def _app(name: str, **overrides) -> dict:
    app = {
        "name": name,
        "bundleIdentifier": f"com.test.{name.lower().replace(' ', '')}",
        "developerName": "Test Dev",
        "category": "Utilities",
        "version": "1.0",
        "versionDate": "2026-01-01",
    }
    app.update(overrides)
    return app


class TokenizeTests(TestCase):
    def test_tokenize(self) -> None:
        self.assertEqual(tokenize("YouTube Plus!"), ["youtube", "plus"])
        self.assertEqual(tokenize(None), [])


class FuzzyTests(TestCase):
    def test_exact_and_prefix(self) -> None:
        self.assertEqual(fuzzy_score("demo", "demo"), 1.0)
        self.assertGreater(fuzzy_score("dem", "demo app"), 0.9)

    def test_typo_still_matches(self) -> None:
        self.assertGreater(fuzzy_score("youtbe", "youtube"), 0.55)

    def test_unrelated_scores_low(self) -> None:
        self.assertLess(fuzzy_score("xyzabc", "youtube"), 0.55)


class SearchTests(TestCase):
    def test_name_search_ranks_exact_first(self) -> None:
        apps = [_app("Demo Plus"), _app("Other"), _app("Demo")]
        result = search(apps, "demo")
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["results"][0]["name"], "Demo")

    def test_bundle_id_search(self) -> None:
        apps = [_app("Demo"), _app("Other", bundleIdentifier="com.other.x")]
        result = search(apps, "com.test.demo")
        self.assertEqual(result["total"], 1)

    def test_filters(self) -> None:
        apps = [_app("A", category="Games"), _app("B", category="Utilities")]
        result = search(apps, "", filters={"category": "games"})
        self.assertEqual([hit["name"] for hit in result["results"]], ["A"])

    def test_matches_filters_developer(self) -> None:
        app = _app("A", developerName="Acme Inc")
        self.assertTrue(matches_filters(app, {"developer": "acme"}))
        self.assertFalse(matches_filters(app, {"developer": "nope"}))

    def test_pagination(self) -> None:
        apps = [_app(f"App {index}") for index in range(5)]
        result = search(apps, "app", limit=2, offset=2)
        self.assertEqual(result["total"], 5)
        self.assertEqual(len(result["results"]), 2)

    def test_sort_by_name(self) -> None:
        apps = [_app("Zulu"), _app("Alpha")]
        result = search(apps, "", sort="name")
        self.assertEqual([hit["name"] for hit in result["results"]], ["Alpha", "Zulu"])


class ScoreTests(TestCase):
    def test_empty_query_scores_zero(self) -> None:
        self.assertEqual(score_app(_app("Demo"), ""), 0.0)

    def test_developer_field_counts(self) -> None:
        app = _app("Demo", developerName="UniqueDeveloperName")
        self.assertGreater(score_app(app, "uniquedevelopername"), 0.0)


if __name__ == "__main__":
    import unittest

    unittest.main()
