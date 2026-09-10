"""Tests for RSS/Atom feed generator."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from omnisource.domain import Catalog
from omnisource.feeds.rss import render_app_rss_feed, render_rss_feed


class TestRssFeed(unittest.TestCase):
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
            "apps": [
                {
                    "slug": "spotiflac",
                    "name": "SpotiFLAC Mobile",
                    "bundleIdentifier": "com.zarz.spotiflacAndroid",
                    "developerName": "zarzet",
                    "icon": "SpotiFLAC.png",
                    "status": "stable",
                }
            ],
        }
        self.catalog = Catalog.from_dict(self.raw_catalog)

    def test_render_rss_feed(self) -> None:
        state = {
            "spotiflac": {
                "versions": [
                    {
                        "version": "4.9.6",
                        "date": "2026-09-07",
                        "downloadURL": "https://example.com/SpotiFLAC.ipa",
                        "size": 34171700,
                        "localizedDescription": "SpotiFLAC 4.9.6 update with new lossless downloader.",
                    }
                ]
            },
            "updateHistory": [
                {
                    "appId": "spotiflac",
                    "version": "4.9.6",
                    "releaseDate": "2026-09-07",
                    "downloadUrl": "https://example.com/SpotiFLAC.ipa",
                    "changelog": "SpotiFLAC 4.9.6 update with new lossless downloader.",
                }
            ],
        }
        rss_xml = render_rss_feed(self.catalog, state)
        self.assertIn('<rss version="2.0"', rss_xml)
        self.assertIn("<title>OmniSource Updates</title>", rss_xml)
        self.assertIn("SpotiFLAC Mobile v4.9.6", rss_xml)
        self.assertIn("https://example.com/SpotiFLAC.ipa", rss_xml)
        self.assertIn("enclosure", rss_xml)


class TestAppRssFeed(unittest.TestCase):
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
            "apps": [
                {
                    "slug": "spotiflac",
                    "name": "SpotiFLAC Mobile",
                    "subtitle": "Lossless streaming",
                    "bundleIdentifier": "com.zarz.spotiflacAndroid",
                    "developerName": "zarzet",
                    "icon": "SpotiFLAC.png",
                    "status": "stable",
                },
                {
                    "slug": "feather",
                    "name": "Feather",
                    "bundleIdentifier": "thewonderofyou.Feather",
                    "developerName": "Feather Team",
                    "icon": "Feather.png",
                    "status": "stable",
                },
            ],
        }
        self.catalog = Catalog.from_dict(self.raw_catalog)
        self.state = {
            "spotiflac": {
                "versions": [
                    {
                        "version": "4.9.6",
                        "date": "2026-09-07",
                        "downloadURL": "https://example.com/SpotiFLAC.ipa",
                        "size": 34171700,
                        "localizedDescription": "Lossless downloader update.",
                    }
                ]
            },
            "updateHistory": [
                {
                    "appId": "feather",
                    "version": "2.9.0",
                    "releaseDate": "2026-09-01",
                    "downloadUrl": "https://example.com/Feather.ipa",
                    "changelog": "Feather 2.9.0 release.",
                }
            ],
        }

    def test_render_app_rss_feed_only_lists_matching_app(self) -> None:
        app_xml = render_app_rss_feed(self.catalog, self.state, "spotiflac")
        self.assertIn("<title>SpotiFLAC Mobile — Releases</title>", app_xml)
        self.assertIn('href="https://iamsmmh.github.io/OmniSource/feeds/spotiflac.xml"', app_xml)
        self.assertIn("SpotiFLAC Mobile v4.9.6", app_xml)
        # History from other apps must not leak into this feed.
        self.assertNotIn("Feather", app_xml)

    def test_render_app_rss_feed_uses_history(self) -> None:
        app_xml = render_app_rss_feed(self.catalog, self.state, "feather")
        self.assertIn("Feather v2.9.0", app_xml)
        self.assertNotIn("SpotiFLAC", app_xml)

    def test_render_app_rss_feed_unknown_slug_is_empty(self) -> None:
        self.assertEqual(render_app_rss_feed(self.catalog, self.state, "nope"), "")


if __name__ == "__main__":
    unittest.main()
