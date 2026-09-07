"""Tests for RSS/Atom feed generator."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from omnisource.domain import Catalog
from omnisource.feeds.rss import render_rss_feed


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


if __name__ == "__main__":
    unittest.main()
