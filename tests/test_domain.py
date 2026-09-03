"""Catalog / domain model tests."""

from __future__ import annotations

import unittest

from omnisource.domain import Catalog, SourceType
from omnisource.errors import ConfigurationError, SyncError


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


if __name__ == "__main__":
    unittest.main()
