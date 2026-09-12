"""Tests for the domain model and dataclass serialization."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import unittest

from omnisource.domain import (
    App,
    Catalog,
    RemoteAsset,
    RemoteRelease,
    RepositoryRef,
    SourceType,
    SyncReport,
    UpdateEvent,
    today,
)
from omnisource.errors import ConfigurationError


class TestDomainModel(unittest.TestCase):
    def test_source_type_parse(self) -> None:
        self.assertEqual(SourceType.parse("github"), SourceType.GITHUB_RELEASES)
        self.assertEqual(SourceType.parse("altstore"), SourceType.ALTSTORE)
        self.assertEqual(SourceType.parse(None), SourceType.GITHUB_RELEASES)
        with self.assertRaises(ConfigurationError):
            SourceType.parse("invalid-type")

    def test_repository_ref_parse(self) -> None:
        raw_github = {"repo": "owner/repo", "keepVersions": 2}
        ref = RepositoryRef.parse(raw_github)
        self.assertEqual(ref.provider, SourceType.GITHUB_RELEASES)
        self.assertEqual(ref.repo, "owner/repo")
        self.assertEqual(ref.keep_versions, 2)
        self.assertFalse(ref.is_feed)

        raw_feed = {"provider": "altstore", "feedURL": "https://example.com/repo.json"}
        feed_ref = RepositoryRef.parse(raw_feed)
        self.assertEqual(feed_ref.provider, SourceType.ALTSTORE)
        self.assertEqual(feed_ref.feed_url, "https://example.com/repo.json")
        self.assertTrue(feed_ref.is_feed)

    def test_remote_asset_to_dict(self) -> None:
        asset = RemoteAsset(
            name="app.ipa",
            download_url="https://example.com/app.ipa",
            size=1024,
            sha256="a" * 64,
        )
        data = asset.to_dict()
        self.assertEqual(data["filename"], "app.ipa")
        self.assertEqual(data["downloadUrl"], "https://example.com/app.ipa")
        self.assertEqual(data["size"], 1024)
        self.assertEqual(data["platform"], "ios")
        self.assertEqual(data["fileType"], "IPA")
        self.assertTrue(data["installable"])

    def test_remote_release(self) -> None:
        release = RemoteRelease(
            tag="v1.0.0",
            name="Release 1.0.0",
            body="Initial release",
            published_at="2026-09-07T12:00:00Z",
            draft=False,
            prerelease=False,
        )
        self.assertTrue(release.is_published)

    def test_catalog_and_app(self) -> None:
        raw = {
            "source": {
                "name": "OmniSource",
                "identifier": "com.omnisource",
                "baseURL": "https://example.com/source",
            },
            "apps": [
                {
                    "slug": "test-app",
                    "name": "Test App",
                    "subtitle": "A test app",
                    "bundleIdentifier": "com.test.app",
                    "developerName": "Tester",
                    "icon": "Test.png",
                    "status": "stable",
                    "category": "utilities",
                    "compatibility": {"minOSVersion": "16.0", "clients": ["altstore"]},
                }
            ],
        }
        catalog = Catalog.from_dict(raw)
        self.assertEqual(len(catalog.apps), 1)
        app = catalog.apps[0]
        self.assertEqual(app.slug, "test-app")
        self.assertEqual(app.name, "Test App")
        self.assertEqual(app.bundle_id, "com.test.app")
        self.assertEqual(app.lifecycle_status, "active")

    def _app(self, **overrides: object) -> App:
        raw: dict[str, object] = {
            "slug": "demo",
            "name": "Demo",
            "bundleIdentifier": "com.example.demo",
            "developerName": "Example",
            "icon": "Demo.png",
            "status": "stable",
            "compatibility": {"minOSVersion": "16.0", "clients": ["altstore"]},
        }
        raw.update(overrides)
        return App(slug=str(raw["slug"]), raw=raw)

    def test_source_url_tracks_sideload_builder(self) -> None:
        """Apps whose sideload IPA is built by a fork link to that source."""
        app = self._app(
            upstreamURL="https://github.com/Developer/Official",
            upstream={"provider": "github", "repo": "Builder/SideloadReleases"},
        )
        self.assertEqual(app.repository_url, "https://github.com/Developer/Official")
        self.assertEqual(app.source_url, "https://github.com/Builder/SideloadReleases")

    def test_source_url_defaults_to_official_repo(self) -> None:
        """Apps published by their own repo keep the official page as source."""
        app = self._app(
            upstreamURL="https://github.com/Owner/App",
            upstream={"provider": "github", "repo": "Owner/App"},
        )
        self.assertEqual(app.source_url, "https://github.com/Owner/App")
        self.assertEqual(app.source_url, app.repository_url)

    def test_source_url_for_feed_providers(self) -> None:
        """AltStore/JSON feeds link to the feed's own site/origin."""
        app = self._app(
            upstreamURL="https://github.com/Dev/Project",
            upstream={"provider": "altstore", "feedURL": "https://repo.example.test/repo.json"},
        )
        self.assertEqual(app.source_url, "https://repo.example.test")
        # The official project page stays available as the repository URL.
        self.assertEqual(app.repository_url, "https://github.com/Dev/Project")

    def test_source_url_falls_back_to_upstream(self) -> None:
        app = self._app(upstreamURL="https://example.com/project")
        self.assertEqual(app.source_url, "https://example.com/project")

    def test_source_url_explicit_override_wins(self) -> None:
        app = self._app(
            upstreamURL="https://github.com/Developer/Official",
            sourceURL="https://archive.org/details/mirror-item",
            upstream={"provider": "github", "repo": "Builder/SideloadReleases"},
        )
        self.assertEqual(app.source_url, "https://archive.org/details/mirror-item")

    def test_update_event_to_json(self) -> None:
        event = UpdateEvent(
            app_id="spotiflac",
            name="SpotiFLAC Mobile",
            version="4.9.6",
            previous_version="4.9.0",
            release_date="2026-09-07",
            download_url="https://example.com/app.ipa",
            changelog="New features",
            kind="updated",
        )
        json_data = event.to_json()
        self.assertEqual(json_data["appId"], "spotiflac")
        self.assertEqual(json_data["version"], "4.9.6")
        self.assertEqual(json_data["kind"], "updated")

    def test_sync_report_to_json(self) -> None:
        report = SyncReport(apps_total=22, apps_synced=22, apps_updated=1)
        json_data = report.to_json()
        self.assertEqual(json_data["appsTotal"], 22)
        self.assertEqual(json_data["appsSynced"], 22)
        self.assertEqual(json_data["appsUpdated"], 1)

    def test_today_helper(self) -> None:
        t = today()
        self.assertRegex(t, r"^\d{4}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()


class TestReleaseHistory(unittest.TestCase):
    """Cadence must survive ``keepVersions: 1`` (ISSUES-REPORT.md #4)."""

    def test_release_dates_merge_versions_and_history(self) -> None:
        from omnisource.utils.dates import release_dates

        state = {
            "demo": {"versions": [{"version": "2.0", "date": "2026-09-01"}]},
            "updateHistory": [
                {"appId": "demo", "version": "1.0", "releaseDate": "2026-07-01"},
                {"appId": "other", "version": "9.0", "releaseDate": "2026-08-01"},
            ],
        }
        self.assertEqual([d.isoformat() for d in release_dates(state, "demo")], ["2026-07-01", "2026-09-01"])

    def test_average_gap_uses_the_recorded_history(self) -> None:
        from omnisource.utils.dates import average_update_gap_days

        state = {
            "demo": {"versions": [{"version": "2.0", "date": "2026-09-01"}]},
            "updateHistory": [
                {"appId": "demo", "version": "1.0", "releaseDate": "2026-08-01"},
                {"appId": "demo", "version": "2.0", "releaseDate": "2026-09-01"},
            ],
        }
        self.assertAlmostEqual(average_update_gap_days(state, "demo"), 31.0, places=3)

    def test_average_gap_without_history_is_zero(self) -> None:
        from omnisource.utils.dates import average_update_gap_days

        state = {"demo": {"versions": [{"version": "1.0", "date": "2026-09-01"}]}}
        self.assertEqual(average_update_gap_days(state, "demo"), 0.0)
