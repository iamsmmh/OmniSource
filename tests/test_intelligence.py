"""Tests for the derived intelligence documents and static app pages."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from omnisource.analytics import build_analytics_doc, remember_analytics_snapshot
from omnisource.app_pages import build_app_pages, render_app_page
from omnisource.discovery import build_discovery_doc, build_sources_doc
from omnisource.domain import Catalog
from omnisource.duplicates import build_duplicates_doc, group_for_app
from omnisource.monitor import build_status_doc, remember_probe
from omnisource.verification import build_verification_doc

CATALOG = {
    "source": {
        "name": "OmniSource",
        "identifier": "com.omnisource",
        "baseURL": "https://iamsmmh.github.io/OmniSource",
        "icon": "OmniSource.png",
    },
    "clients": [
        {"id": "altstore", "name": "AltStore", "icon": "AltStore.png"},
        {"id": "esign", "name": "ESign", "icon": "E-Sign.png"},
    ],
    "apps": [
        {
            "slug": "alpha",
            "name": "Alpha Tweak",
            "subtitle": "Official alpha build",
            "bundleIdentifier": "com.example.alpha",
            "developerName": "Alpha Dev",
            "category": "utilities",
            "tags": ["tweak", "utility"],
            "icon": "Alpha.png",
            "status": "stable",
            "featured": True,
            "localizedDescription": "An app with a long description.",
            "shortDescription": "Official alpha build",
            "screenshots": [],
            "upstreamURL": "https://github.com/alpha/alpha",
            "verification": {
                "method": "github-release",
                "publisher": "Alpha Dev",
                "checksumPublished": True,
            },
            "compatibility": {"minOSVersion": "16.0", "clients": ["altstore", "esign"], "notes": "Official."},
            "upstream": {"provider": "github", "repo": "alpha/alpha"},
        },
        {
            "slug": "beta",
            "name": "Alpha Tweak Plus",
            "subtitle": "Community build",
            "bundleIdentifier": "com.example.alpha",
            "developerName": "Community Builder",
            "category": "utilities",
            "tags": ["tweak"],
            "icon": "Beta.png",
            "status": "manual",
            "localizedDescription": "Community packaged build.",
            "upstreamURL": "https://github.com/beta/beta",
            "verification": {
                "method": "manual-mirror",
                "publisher": "Community Builder",
                "checksumPublished": False,
            },
            "compatibility": {"minOSVersion": "15.0", "clients": ["altstore"]},
            "upstream": {"provider": "github", "repo": "beta/beta"},
        },
        {
            "slug": "gamma",
            "name": "Gamma Solo",
            "bundleIdentifier": "com.example.gamma",
            "developerName": "Gamma Dev",
            "category": "music",
            "icon": "Gamma.png",
            "status": "stable",
            "localizedDescription": "A standalone music app.",
            "upstreamURL": "https://github.com/gamma/gamma",
            "verification": {"method": "github-release", "publisher": "Gamma Dev"},
            "compatibility": {"minOSVersion": "16.0", "clients": ["altstore"]},
            "upstream": {"provider": "github", "repo": "gamma/gamma"},
        },
    ],
}

STATE = {
    "alpha": {
        "versions": [
            {
                "version": "2.0.0",
                "date": "2026-09-08",
                "localizedDescription": "Big release",
                "downloadURL": "https://example.com/alpha.ipa",
                "size": 1000,
                "sha256": "a" * 64,
                "downloads": 42,
            },
            {
                "version": "1.0.0",
                "date": "2026-08-01",
                "localizedDescription": "First",
                "downloadURL": "https://example.com/alpha-1.ipa",
                "size": 900,
            },
        ],
        "health": {"reachable": True, "detail": "HTTP 200", "since": "2026-09-09", "latencyMs": 120},
        "syncedAt": "2026-09-09",
    },
    "beta": {
        "versions": [
            {
                "version": "2.5.0",
                "date": "2026-09-09",
                "localizedDescription": "Newer community build",
                "downloadURL": "https://example.com/beta.ipa",
                "size": 2000,
            }
        ],
        "health": {"reachable": True, "detail": "HTTP 302", "since": "2026-09-09", "latencyMs": 300},
        "syncedAt": "2026-09-09",
    },
    "gamma": {
        "versions": [
            {
                "version": "1.2.0",
                "date": "2026-07-01",
                "localizedDescription": "Music",
                "downloadURL": "https://example.com/gamma.ipa",
                "size": 3000,
            }
        ],
        "health": {"reachable": False, "detail": "HTTP 404", "since": "2026-09-09", "latencyMs": 50},
        "syncedAt": "2026-09-07",
    },
    "updateHistory": [
        {
            "appId": "beta",
            "name": "Alpha Tweak Plus",
            "version": "2.5.0",
            "releaseDate": "2026-09-09",
            "kind": "updated",
        },
        {
            "appId": "gamma",
            "name": "Gamma Solo",
            "version": "1.2.0",
            "releaseDate": "2026-09-08",
            "kind": "new",
        },
        {
            "appId": "alpha",
            "name": "Alpha Tweak",
            "version": "2.0.0",
            "releaseDate": "2026-06-01",
            "kind": "updated",
        },
    ],
}


def catalog() -> Catalog:
    return Catalog.from_dict(CATALOG)


class TestDiscovery(unittest.TestCase):
    def test_discovery_doc(self) -> None:
        doc = build_discovery_doc(catalog(), STATE)
        self.assertEqual(doc["count"], 3)
        alpha = next(item for item in doc["apps"] if item["id"] == "alpha")
        self.assertEqual(alpha["bundleId"], "com.example.alpha")
        self.assertEqual(alpha["tags"], ["tweak", "utility"])
        self.assertEqual(alpha["downloads"], 42)
        self.assertEqual(alpha["pageURL"], "https://iamsmmh.github.io/OmniSource/apps/alpha/")

    def test_sources_doc(self) -> None:
        doc = build_sources_doc(catalog(), STATE)
        self.assertEqual(doc["count"], 3)
        self.assertEqual(len(doc["clients"]), 2)
        self.assertEqual(doc["feed"]["appsURL"], "https://iamsmmh.github.io/OmniSource/apps.json")


class TestVerification(unittest.TestCase):
    def test_levels(self) -> None:
        health_doc = {
            "apps": [
                {"slug": "alpha", "downloadReachable": True},
                {"slug": "beta", "downloadReachable": True},
                {"slug": "gamma", "downloadReachable": False},
            ]
        }
        doc = build_verification_doc(catalog(), STATE, health_doc)
        by_slug = {item["app"]: item for item in doc["apps"]}
        self.assertEqual(by_slug["alpha"]["status"], "VERIFIED")
        self.assertTrue(by_slug["alpha"]["hash_verified"])
        self.assertEqual(by_slug["beta"]["status"], "COMMUNITY VERIFIED")
        self.assertFalse(by_slug["beta"]["hash_verified"])
        self.assertEqual(by_slug["gamma"]["status"], "UNVERIFIED")
        self.assertEqual(doc["totals"]["verified"], 1)
        self.assertEqual(doc["totals"]["communityVerified"], 1)
        self.assertEqual(doc["totals"]["unverified"], 1)


class TestMonitor(unittest.TestCase):
    def test_status_doc(self) -> None:
        health_doc = {
            "apps": [
                {"slug": "alpha", "downloadReachable": True, "stale": False},
                {"slug": "beta", "downloadReachable": True, "stale": False},
                {"slug": "gamma", "downloadReachable": False, "stale": True},
            ]
        }
        doc = build_status_doc(catalog(), STATE, health_doc)
        by_slug = {item["id"]: item for item in doc["sources"]}
        self.assertEqual(by_slug["alpha"]["status"], "healthy")
        self.assertEqual(by_slug["alpha"]["latencyMs"], 120)
        self.assertEqual(by_slug["gamma"]["status"], "unavailable")
        self.assertEqual(doc["totals"]["healthy"], 2)
        self.assertEqual(doc["totals"]["unavailable"], 1)

    def test_remember_probe_appends_history(self) -> None:
        state: dict = {}
        remember_probe(state, "alpha", reachable=True, detail="HTTP 200", latency_ms=99.4)
        self.assertEqual(state["alpha"]["health"]["latencyMs"], 99)
        self.assertEqual(len(state["alpha"]["healthHistory"]), 1)


class TestDuplicates(unittest.TestCase):
    def test_bundle_group_and_recommendation(self) -> None:
        doc = build_duplicates_doc(catalog(), STATE)
        self.assertEqual(doc["count"], 1)
        group = doc["groups"][0]
        self.assertIn("bundle-id", group["type"])
        self.assertEqual(len(group["apps"]), 2)
        # Beta 2.5.0 is newer than Alpha 2.0.0.
        self.assertEqual(group["recommended"]["app"], "beta")
        self.assertIn("Newest version", group["recommended"]["reason"])
        info = group_for_app(doc, "alpha")
        self.assertEqual(info["recommended"]["app"], "beta")


class TestAnalytics(unittest.TestCase):
    def test_totals_and_week_counts(self) -> None:
        health_doc = {
            "totals": {"apps": 3, "reachable": 2, "unreachable": 1, "featured": 1},
            "apps": [
                {"slug": "alpha", "downloadReachable": True},
                {"slug": "beta", "downloadReachable": True},
                {"slug": "gamma", "downloadReachable": False},
            ],
        }
        verification = build_verification_doc(catalog(), STATE, health_doc)
        doc = build_analytics_doc(catalog(), STATE, health_doc, verification)
        totals = doc["totals"]
        self.assertEqual(totals["apps"], 3)
        self.assertEqual(totals["sources"], 3)
        self.assertEqual(totals["verifiedApps"], 1)
        self.assertEqual(totals["newAppsThisWeek"], 1)
        self.assertEqual(totals["updatedAppsThisWeek"], 1)
        self.assertEqual(totals["deadLinks"], 1)
        self.assertEqual(doc["lastSync"], "2026-09-09")

    def test_snapshot_history(self) -> None:
        state: dict = {}
        snapshot = {
            "totals": {
                "apps": 3,
                "sources": 3,
                "verifiedApps": 1,
                "deadLinks": 0,
                "newAppsThisWeek": 0,
                "updatedAppsThisWeek": 0,
            }
        }
        remember_analytics_snapshot(state, snapshot)
        remember_analytics_snapshot(state, snapshot)
        # Same-day snapshots collapse into one entry.
        self.assertEqual(len(state["analyticsHistory"]), 1)


class TestAppPages(unittest.TestCase):
    def test_render_page(self) -> None:
        catalog_obj = catalog()
        verification = build_verification_doc(catalog_obj, STATE)
        duplicates = build_duplicates_doc(catalog_obj, STATE)
        html_doc = render_app_page(
            catalog_obj,
            catalog_obj.app_by_slug("alpha"),
            STATE,
            {"apps": []},
            verification,
            duplicates,
        )
        self.assertIn("<title>Alpha Tweak — OmniSource</title>", html_doc)
        self.assertIn("app-page.css", html_doc)
        self.assertIn("Download IPA", html_doc)
        self.assertIn("VERIFIED", html_doc)
        self.assertIn("https://example.com/alpha.ipa", html_doc)
        self.assertIn("altstore://source?url=", html_doc)

    def test_build_pages_writes_and_cleans(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pages_dir = Path(tmpdir)
            (pages_dir / "stale").mkdir(parents=True)
            (pages_dir / "stale" / "index.html").write_text("old", encoding="utf-8")
            catalog_obj = catalog()
            changed = build_app_pages(
                catalog_obj,
                STATE,
                {"apps": []},
                build_verification_doc(catalog_obj, STATE),
                build_duplicates_doc(catalog_obj, STATE),
                pages_dir=pages_dir,
            )
            self.assertTrue((pages_dir / "alpha" / "index.html").is_file())
            self.assertFalse((pages_dir / "stale").exists())
            self.assertGreaterEqual(len(changed), 3)


if __name__ == "__main__":
    unittest.main()
