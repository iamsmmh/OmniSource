"""Provider tests against a fake HTTP client."""

from __future__ import annotations

import unittest
from typing import Any

from omnisource.domain import RepositoryRef, SourceType
from omnisource.http import HttpClient
from omnisource.providers.feed import GenericFeedProvider
from omnisource.providers.github import GitHubReleasesProvider
from omnisource.providers.gitlab import GitLabReleasesProvider
from omnisource.providers.registry import build_default_registry


class FakeHttp(HttpClient):
    def __init__(self, responses: dict[str, Any]) -> None:
        super().__init__(auth_rules=())
        self.responses = responses
        self.calls: list[str] = []

    def get_json(self, url: str, *, extra_headers: dict[str, str] | None = None, retries: int | None = None) -> Any:
        self.calls.append(url)
        self.requests += 1
        matches = [(prefix, payload) for prefix, payload in self.responses.items() if prefix in url]
        if not matches:
            raise AssertionError(f"unexpected URL {url}")
        _prefix, payload = max(matches, key=lambda item: len(item[0]))
        return payload


GITHUB_RELEASE = {
    "tag_name": "v1.2.3",
    "name": "1.2.3",
    "body": "SHA256: " + ("ab" * 32),
    "published_at": "2026-01-02T00:00:00Z",
    "draft": False,
    "prerelease": False,
    "assets": [
        {
            "name": "Demo-1.2.3.ipa",
            "browser_download_url": "https://github.com/o/r/releases/download/v1.2.3/Demo-1.2.3.ipa",
            "size": 42,
            "digest": "sha256:" + ("ab" * 32),
        }
    ],
}


class GitHubProviderTests(unittest.TestCase):
    def test_fetch_releases_normalises_assets(self) -> None:
        http = FakeHttp({"/repos/o/r/releases": [GITHUB_RELEASE]})
        provider = GitHubReleasesProvider(http)
        ref = RepositoryRef(provider=SourceType.GITHUB_RELEASES, repo="o/r")
        releases = provider.fetch_releases(ref)
        self.assertEqual(len(releases), 1)
        self.assertEqual(releases[0].tag, "v1.2.3")
        self.assertEqual(releases[0].assets[0].size, 42)
        self.assertEqual(releases[0].assets[0].sha256, "ab" * 32)

    def test_incremental_short_circuit(self) -> None:
        http = FakeHttp({"/repos/o/r/releases": [GITHUB_RELEASE]})
        provider = GitHubReleasesProvider(http)
        ref = RepositoryRef(provider=SourceType.GITHUB_RELEASES, repo="o/r", max_pages=3)
        url = GITHUB_RELEASE["assets"][0]["browser_download_url"]
        result = provider.fetch_releases(ref, previous_latest_url=url, incremental=True)
        self.assertEqual(result, [])
        self.assertEqual(len(http.calls), 1)

    def test_validate_repository(self) -> None:
        http = FakeHttp({"/repos/o/r": {"html_url": "https://github.com/o/r", "archived": False}})
        provider = GitHubReleasesProvider(http)
        result = provider.validate_repository(RepositoryRef(provider=SourceType.GITHUB_RELEASES, repo="o/r"))
        self.assertTrue(result.ok)
        aliased = provider.validateRepository(RepositoryRef(provider=SourceType.GITHUB_RELEASES, repo="o/r"))
        self.assertTrue(aliased.ok)

    def test_contract_aliases(self) -> None:
        http = FakeHttp(
            {
                "/repos/o/r": {
                    "name": "r",
                    "html_url": "https://github.com/o/r",
                    "owner": {"login": "o"},
                    "description": "d",
                    "topics": [],
                    "license": {},
                },
                "/repos/o/r/releases": [GITHUB_RELEASE],
            }
        )
        provider = GitHubReleasesProvider(http)
        ref = RepositoryRef(provider=SourceType.GITHUB_RELEASES, repo="o/r")
        apps = provider.discoverApps(ref)
        self.assertEqual(apps[0].name, "r")
        meta = provider.fetchMetadata(ref)
        self.assertEqual(meta.developer, "o")


class GitLabProviderTests(unittest.TestCase):
    def test_fetch_releases(self) -> None:
        payload = [
            {
                "tag_name": "v2.0.0",
                "name": "2.0.0",
                "description": "notes",
                "released_at": "2026-02-01T00:00:00Z",
                "assets": {
                    "links": [
                        {"name": "App.ipa", "direct_asset_url": "https://gitlab.com/o/r/-/releases/v2.0.0/App.ipa"}
                    ]
                },
            }
        ]
        http = FakeHttp({"/releases": payload})
        provider = GitLabReleasesProvider(http)
        releases = provider.fetch_releases(RepositoryRef(provider=SourceType.GITLAB_RELEASES, repo="o/r"))
        self.assertEqual(releases[0].assets[0].name, "App.ipa")


class FeedProviderTests(unittest.TestCase):
    def test_altstore_shape(self) -> None:
        payload = {
            "name": "Source",
            "apps": [
                {
                    "name": "Demo",
                    "bundleIdentifier": "com.example.demo",
                    "developerName": "dev",
                    "version": "1.0",
                    "versionDate": "2026-01-01",
                    "downloadURL": "https://example.com/demo.ipa",
                    "size": 9,
                    "versions": [
                        {
                            "version": "1.0",
                            "date": "2026-01-01",
                            "downloadURL": "https://example.com/demo.ipa",
                            "size": 9,
                            "localizedDescription": "first",
                        }
                    ],
                }
            ],
        }
        http = FakeHttp({"https://example.com/source.json": payload})
        provider = GenericFeedProvider(http)
        ref = RepositoryRef(
            provider=SourceType.JSON_FEED,
            feed_url="https://example.com/source.json",
        )
        self.assertTrue(provider.validate_repository(ref).ok)
        apps = provider.discover_apps(ref)
        self.assertEqual(apps[0].name, "Demo")
        releases = provider.fetch_releases(ref)
        self.assertEqual(releases[0].tag, "1.0")


class RegistryTests(unittest.TestCase):
    def test_default_registry_covers_every_source_type(self) -> None:
        registry = build_default_registry(FakeHttp({}))
        for source_type in SourceType:
            if source_type is SourceType.MANUAL:
                continue
            self.assertTrue(source_type in registry, source_type)


if __name__ == "__main__":
    unittest.main()
