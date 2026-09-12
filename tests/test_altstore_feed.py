"""Tests for AltStore Source v2 feed rendering."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from omnisource.domain import App, Catalog
from omnisource.feeds.altstore import (
    feed_envelope,
    render_altstore_app,
    render_badge_docs,
    render_health_doc,
    render_news_items,
)


class TestAltStoreFeed(unittest.TestCase):
    def setUp(self) -> None:
        self.raw_catalog = {
            "source": {
                "name": "OmniSource",
                "identifier": "com.iamsmmh.omnisource",
                "subtitle": "Curated iOS Apps",
                "description": "AltStore feed aggregator",
                "baseURL": "https://iamsmmh.github.io/OmniSource",
                "tintColor": "5B5BD6",
                "icon": "OmniSource.png",
                "banner": "OmniSource.png",
            },
            "clients": [],
            "apps": [
                {
                    "slug": "spotiflac",
                    "name": "SpotiFLAC Mobile",
                    "bundleIdentifier": "com.zarz.spotiflacAndroid",
                    "developerName": "zarzet",
                    "icon": "SpotiFLAC.png",
                    "status": "stable",
                    "compatibility": {"minOSVersion": "16.0", "clients": ["altstore"]},
                }
            ],
        }
        self.catalog = Catalog.from_dict(self.raw_catalog)

    def test_feed_envelope(self) -> None:
        envelope = feed_envelope(
            self.catalog,
            name="OmniSource",
            identifier="com.iamsmmh.omnisource",
            subtitle="Curated apps",
            description="All apps",
        )
        self.assertEqual(envelope["name"], "OmniSource")
        self.assertEqual(envelope["apiVersion"], "v2")
        self.assertEqual(envelope["tintColor"], "5B5BD6")
        self.assertEqual(envelope["iconURL"], "https://iamsmmh.github.io/OmniSource/assets/OmniSource.png")
        self.assertEqual(envelope["sourceURL"], "https://iamsmmh.github.io/OmniSource/apps.json")

    def test_render_altstore_app(self) -> None:
        raw_app = {
            "slug": "spotiflac",
            "name": "SpotiFLAC Mobile",
            "bundleIdentifier": "com.zarz.spotiflacAndroid",
            "developerName": "zarzet",
            "subtitle": "FLAC Downloader for iOS",
            "localizedDescription": "Download high quality FLAC audio.",
            "category": "utilities",
            "tintColor": "1DB954",
            "icon": "SpotiFLAC.png",
            "status": "stable",
            "screenshots": ["https://example.com/screen1.png"],
        }
        app = App(slug="spotiflac", raw=raw_app)
        versions = [
            {
                "version": "4.9.6",
                "date": "2026-09-07",
                "localizedDescription": "SpotiFLAC 4.9.6",
                "downloadURL": "https://example.com/SpotiFLAC.ipa",
                "size": 34171700,
                "minOSVersion": "16.0",
            }
        ]
        health = {"reachable": True, "detail": "HTTP 302", "since": "2026-09-07"}

        rendered = render_altstore_app(self.catalog, app, versions, health)
        self.assertEqual(rendered["name"], "SpotiFLAC Mobile")
        self.assertEqual(rendered["bundleIdentifier"], "com.zarz.spotiflacAndroid")
        self.assertEqual(rendered["version"], "4.9.6")
        self.assertEqual(rendered["downloadURL"], "https://example.com/SpotiFLAC.ipa")
        self.assertEqual(rendered["tintColor"], "1DB954")
        self.assertTrue(rendered["omnisource"]["health"]["downloadReachable"])

    def test_render_health_doc(self) -> None:
        raw_app = {
            "slug": "test",
            "name": "Test",
            "bundleIdentifier": "com.test",
            "developerName": "Tester",
            "icon": "Test.png",
            "status": "stable",
            "featured": True,
        }
        app = App(slug="test", raw=raw_app)
        entry = {
            "version": "1.0",
            "versionDate": "2026-09-07",
            "size": 1000,
            "omnisource": {
                "featured": True,
                "health": {
                    "downloadReachable": True,
                    "detail": "HTTP 200",
                    "statusSince": "2026-09-07",
                },
            },
        }
        doc = render_health_doc([(app, entry)])
        self.assertEqual(doc["totals"]["apps"], 1)
        self.assertEqual(doc["totals"]["reachable"], 1)
        self.assertEqual(doc["totals"]["unreachable"], 0)

    def test_render_news_items(self) -> None:
        state = {
            "spotiflac": {
                "versions": [
                    {
                        "version": "4.9.6",
                        "date": "2026-09-07",
                        "localizedDescription": "Release",
                    }
                ]
            },
            "updateHistory": [
                {
                    "appId": "spotiflac",
                    "version": "4.9.6",
                    "releaseDate": "2026-09-07",
                }
            ],
        }
        news = render_news_items(self.catalog, state, limit=5)
        self.assertEqual(len(news), 1)
        self.assertEqual(news[0]["appID"], "com.zarz.spotiflacAndroid")
        self.assertEqual(news[0]["title"], "SpotiFLAC Mobile v4.9.6")
        self.assertTrue(news[0]["identifier"].startswith("news-spotiflac"))

    def test_render_badge_docs(self) -> None:
        raw_app = {
            "slug": "test",
            "name": "Test",
            "bundleIdentifier": "com.test",
            "developerName": "Tester",
            "icon": "Test.png",
            "status": "stable",
        }
        app = App(slug="test", raw=raw_app)
        entry = {
            "version": "1.0",
            "versionDate": "2026-09-07",
            "size": 1000,
            "omnisource": {
                "featured": False,
                "health": {"downloadReachable": True, "detail": "HTTP 200", "statusSince": "2026-09-07"},
            },
        }
        health_doc = render_health_doc([(app, entry)])
        badges = render_badge_docs([(app, entry)], health_doc)
        self.assertIn("badge-apps.json", badges)
        self.assertIn("badge-health.json", badges)
        self.assertIn("badge-version.json", badges)
        self.assertEqual(badges["badge-apps.json"]["message"], "1")
        self.assertEqual(badges["badge-health.json"]["message"], "1/1 healthy")


if __name__ == "__main__":
    unittest.main()


class TestCompatibilityEmission(unittest.TestCase):
    """Compatibility must reach the clients, not just the website (#Tier1-2)."""

    def setUp(self) -> None:
        self.catalog = Catalog.from_dict(
            {
                "source": {
                    "name": "OmniSource",
                    "identifier": "com.iamsmmh.omnisource",
                    "baseURL": "https://iamsmmh.github.io/OmniSource",
                    "icon": "OmniSource.png",
                    "banner": "OmniSource.png",
                },
                "apps": [
                    {
                        "slug": "demo",
                        "name": "Demo",
                        "bundleIdentifier": "com.example.demo",
                        "developerName": "Dev",
                        "icon": "Demo.png",
                        "status": "stable",
                        "compatibility": {
                            "minOSVersion": "17.0",
                            "maxOSVersion": "18.2",
                            "clients": ["altstore"],
                        },
                    }
                ],
            }
        )
        self.app = self.catalog.apps[0]

    def test_versions_inherit_the_catalog_minimum(self) -> None:
        versions = [
            {
                "version": "2.0",
                "date": "2026-09-01",
                "downloadURL": "https://e.com/2.ipa",
                "size": 10,
                "localizedDescription": "Release 2.0",
            },
            {
                "version": "1.0",
                "date": "2026-08-01",
                "downloadURL": "https://e.com/1.ipa",
                "size": 9,
                "minOSVersion": "16.0",
                "localizedDescription": "Release 1.0",
            },
        ]
        entry = render_altstore_app(self.catalog, self.app, versions, {})
        self.assertEqual(entry["versions"][0]["minOSVersion"], "17.0")
        # An upstream-declared minimum is authoritative and never overwritten.
        self.assertEqual(entry["versions"][1]["minOSVersion"], "16.0")
        for version in entry["versions"]:
            self.assertEqual(version["maxOSVersion"], "18.2")

    def test_health_document_reports_the_build_date(self) -> None:
        entry = render_altstore_app(
            self.catalog,
            self.app,
            [
                {
                    "version": "2.0",
                    "date": "2026-09-01",
                    "downloadURL": "https://e.com/2.ipa",
                    "size": 10,
                    "localizedDescription": "Release 2.0",
                }
            ],
            {"reachable": True, "detail": "HTTP 200", "since": "2026-08-20"},
        )
        doc = render_health_doc([(self.app, entry)], generated_at="2026-09-12")
        self.assertEqual(doc["generatedAt"], "2026-09-12")
        self.assertEqual(doc["contentUpdatedAt"], "2026-09-01")
        self.assertEqual(doc["totals"]["apps"], 1)
