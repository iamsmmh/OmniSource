"""Catalog / domain model tests."""

from __future__ import annotations

import unittest

from omnisource.domain import Catalog, SourceType
from omnisource.errors import ConfigurationError, SyncError
from omnisource.repository_registry import build_repository_registry


class SourceTypeTests(unittest.TestCase):
    def test_default_github(self) -> None:
        self.assertEqual(SourceType.parse(None), SourceType.GITHUB_RELEASES)
        self.assertEqual(SourceType.parse("gitlab"), SourceType.GITLAB_RELEASES)

    def test_unknown_provider(self) -> None:
        with self.assertRaises(ConfigurationError):
            SourceType.parse("bitbucket")


class CatalogTests(unittest.TestCase):
    def test_from_dict(self) -> None:
        catalog = Catalog.from_dict(
            {
                "source": {"baseURL": "https://example.com/OmniSource"},
                "apps": [
                    {
                        "slug": "demo",
                        "name": "Demo",
                        "bundleIdentifier": "com.example.demo",
                        "developerName": "dev",
                        "category": "utilities",
                        "icon": "Demo.png",
                        "localizedDescription": "A demo.",
                        "upstream": {"repo": "owner/demo", "provider": "github"},
                    }
                ],
            }
        )
        self.assertEqual(catalog.base_url, "https://example.com/OmniSource")
        app = catalog.apps[0]
        self.assertEqual(app.source_type, SourceType.GITHUB_RELEASES)
        self.assertEqual(app.repository_url, "https://github.com/owner/demo")
        self.assertIsNotNone(app.upstream)
        assert app.upstream is not None
        self.assertEqual(app.upstream.repo, "owner/demo")

    def test_empty_catalog_rejected(self) -> None:
        with self.assertRaises(SyncError):
            Catalog.from_dict({"source": {}, "apps": []})

    def test_feed_provider_requires_url(self) -> None:
        with self.assertRaises(ConfigurationError):
            Catalog.from_dict(
                {
                    "source": {},
                    "apps": [
                        {
                            "slug": "demo",
                            "name": "Demo",
                            "bundleIdentifier": "com.example.demo",
                            "developerName": "dev",
                            "upstream": {"provider": "altstore"},
                        }
                    ],
                }
            )


class FeedBackedCatalogTests(unittest.TestCase):
    """Apps published together in one source share a monitored repository."""

    def _catalog(self) -> Catalog:
        def app(slug: str, bundle: str, app_id: str) -> dict[str, object]:
            return {
                "slug": slug,
                "name": slug,
                "bundleIdentifier": bundle,
                "developerName": "dev",
                "upstream": {
                    "provider": "altstore",
                    "feedURL": "https://repo.example.com/repo.json",
                    "appId": app_id,
                },
            }

        return Catalog.from_dict(
            {
                "source": {},
                "apps": [
                    app("one", "com.example.one", "com.example.one"),
                    app("two", "com.example.two", "com.example.two"),
                    {
                        "slug": "three",
                        "name": "three",
                        "bundleIdentifier": "com.example.three",
                        "developerName": "dev",
                        "upstream": {"provider": "github", "repo": "owner/three"},
                    },
                ],
            }
        )

    def test_app_id_is_parsed_and_identifies_the_feed(self) -> None:
        catalog = self._catalog()
        first = catalog.apps[0].upstream
        assert first is not None
        self.assertTrue(first.is_feed)
        self.assertEqual(first.app_id, "com.example.one")
        self.assertEqual(first.identity, "https://repo.example.com/repo.json")
        forge = catalog.apps[2].upstream
        assert forge is not None
        self.assertFalse(forge.is_feed)
        self.assertEqual(forge.identity, "owner/three")

    def test_registry_groups_feed_apps_and_names_them_by_host(self) -> None:
        registry = build_repository_registry(self._catalog(), generated_at="2026-09-08")
        self.assertEqual(registry["count"], 2)
        feed_repo = next(item for item in registry["repositories"] if item["provider"] == "altstore")
        self.assertEqual(feed_repo["name"], "repo.example.com")
        self.assertEqual(sorted(feed_repo["applicationIds"]), ["one", "two"])
        forge_repo = next(item for item in registry["repositories"] if item["provider"] == "github")
        self.assertEqual(forge_repo["name"], "owner/three")


if __name__ == "__main__":
    unittest.main()
