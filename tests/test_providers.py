"""Tests for source providers and provider registry."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import unittest
from unittest.mock import MagicMock

from omnisource.domain import RepositoryRef, SourceType
from omnisource.http import HttpClient
from omnisource.providers.feed import AltStoreFeedProvider
from omnisource.providers.github import GitHubReleasesProvider
from omnisource.providers.registry import build_default_registry


class TestProviders(unittest.TestCase):
    def setUp(self) -> None:
        self.http_mock = MagicMock(spec=HttpClient)
        self.registry = build_default_registry(self.http_mock)

    def test_registry_resolution(self) -> None:
        github_ref = RepositoryRef(provider=SourceType.GITHUB_RELEASES, repo="owner/repo")
        provider = self.registry.resolve(github_ref)
        self.assertIsInstance(provider, GitHubReleasesProvider)

        feed_ref = RepositoryRef(provider=SourceType.ALTSTORE, feed_url="https://example.com/repo.json")
        provider = self.registry.resolve(feed_ref)
        self.assertIsInstance(provider, AltStoreFeedProvider)

    def test_github_releases_provider(self) -> None:
        self.http_mock.get_json.return_value = [
            {
                "tag_name": "v1.0.0",
                "name": "Release 1.0.0",
                "body": "Test changelog",
                "published_at": "2026-09-07T10:00:00Z",
                "draft": False,
                "prerelease": False,
                "assets": [
                    {
                        "name": "App.ipa",
                        "browser_download_url": "https://example.com/App.ipa",
                        "size": 50000,
                        "content_type": "application/octet-stream",
                    }
                ],
            }
        ]
        provider = GitHubReleasesProvider(self.http_mock)
        ref = RepositoryRef(provider=SourceType.GITHUB_RELEASES, repo="owner/repo")
        releases = provider.fetch_releases(ref)
        self.assertEqual(len(releases), 1)
        self.assertEqual(releases[0].tag, "v1.0.0")
        self.assertEqual(len(releases[0].assets), 1)
        self.assertEqual(releases[0].assets[0].download_url, "https://example.com/App.ipa")

    def test_generic_feed_provider(self) -> None:
        self.http_mock.get_json.return_value = {
            "name": "Test Source",
            "identifier": "com.test.source",
            "apps": [
                {
                    "name": "Feed App",
                    "bundleIdentifier": "com.feed.app",
                    "version": "2.0.0",
                    "versionDate": "2026-09-07",
                    "downloadURL": "https://example.com/feedapp.ipa",
                    "size": 123456,
                    "localizedDescription": "Feed app description",
                    "versions": [
                        {
                            "version": "2.0.0",
                            "date": "2026-09-07",
                            "downloadURL": "https://example.com/feedapp.ipa",
                            "size": 123456,
                            "localizedDescription": "Feed app description",
                        }
                    ],
                }
            ],
        }
        provider = AltStoreFeedProvider(self.http_mock)
        ref = RepositoryRef(provider=SourceType.ALTSTORE, feed_url="https://example.com/repo.json")
        releases = provider.fetch_releases(ref)
        self.assertEqual(len(releases), 1)
        self.assertEqual(releases[0].tag, "2.0.0")


if __name__ == "__main__":
    unittest.main()
