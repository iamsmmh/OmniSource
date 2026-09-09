"""Tests for the discovery v2 modules (Phases 1-9, 13)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from omnisource.community import build_community_doc
from omnisource.compare import build_compare_doc
from omnisource.domain import Catalog
from omnisource.download_intel import build_download_intel_doc
from omnisource.install import build_install_doc
from omnisource.related import build_related_doc
from omnisource.reputation import build_reputation_doc
from omnisource.search_index import build_search_index
from omnisource.trending import build_trending_doc

CATALOG = {
    "source": {
        "name": "OmniSource",
        "identifier": "com.omnisource",
        "baseURL": "https://example.test/OmniSource",
        "icon": "OmniSource.png",
    },
    "clients": [
        {"id": "altstore", "name": "AltStore", "icon": "AltStore.png"},
        {"id": "sidestore", "name": "SideStore", "icon": "SideStore.png"},
        {"id": "feather", "name": "Feather", "icon": "Feather.png"},
        {"id": "esign", "name": "ESign", "icon": "E-Sign.png"},
        {"id": "livecontainer", "name": "LiveContainer", "icon": "LiveContainer.png"},
    ],
    "apps": [
        {
            "slug": "spotiflac",
            "name": "SpotiFLAC",
            "bundleIdentifier": "com.zarz.spotiflacAndroid",
            "developerName": "zarzet",
            "icon": "SpotiFLAC.png",
            "status": "stable",
            "compatibility": {"minOSVersion": "16.0", "clients": ["altstore", "sidestore"]},
            "verification": {"method": "github-release", "publisher": "spotiflacapp/SpotiFLAC-Mobile"},
            "tags": ["music", "flac"],
            "featured": True,
            "upstream": {
                "provider": "github",
                "repo": "spotiflacapp/SpotiFLAC-Mobile",
                "assetSuffixes": [".apk", ".ipa"],
            },
        },
        {
            "slug": "uyouenhanced",
            "name": "uYouEnhanced",
            "bundleIdentifier": "com.google.ios.youtube",
            "developerName": "arichornlover",
            "icon": "uYouEnhanced.png",
            "status": "stable",
            "compatibility": {"minOSVersion": "15.0", "clients": ["altstore", "sidestore"]},
            "verification": {"method": "manual-mirror", "publisher": "arichornlover/uYouEnhanced"},
            "tags": ["photo-video", "youtube"],
            "featured": True,
            "upstream": {"provider": "github", "repo": "arichornlover/uYouEnhanced", "assetSuffixes": [".ipa"]},
        },
        {
            "slug": "ytlite",
            "name": "YouTubePlus",
            "bundleIdentifier": "com.google.ios.youtube",
            "developerName": "dayanch96",
            "icon": "YouTube.png",
            "status": "stable",
            "compatibility": {"minOSVersion": "15.0", "clients": ["altstore", "sidestore"]},
            "verification": {"method": "github-release", "publisher": "dayanch96/YTLite"},
            "tags": ["photo-video", "youtube"],
            "featured": True,
            "upstream": {"provider": "github", "repo": "dayanch96/YTLite", "assetSuffixes": [".ipa"]},
        },
    ],
}

STATE = {
    "spotiflac": {
        "versions": [
            {
                "version": "4.9.6",
                "date": "2026-09-07",
                "size": 1024,
                "downloadURL": "https://example.com/spotiflac.ipa",
            },
            {"version": "4.9.5", "date": "2026-08-15", "size": 1024, "downloadURL": "https://example.com/old.ipa"},
        ],
        "health": {"reachable": True, "latencyMs": 120},
    },
    "uyouenhanced": {
        "versions": [
            {"version": "21.14.4", "date": "2026-08-22", "size": 4096, "downloadURL": "https://example.com/uyou.ipa"},
        ],
        "health": {"reachable": True, "latencyMs": 200},
    },
    "ytlite": {
        "versions": [
            {"version": "21.24.3", "date": "2026-09-01", "size": 4096, "downloadURL": "https://example.com/ytlite.ipa"},
        ],
        "health": {"reachable": True, "latencyMs": 150},
    },
}

HEALTH_DOC = {
    "apps": [
        {"slug": "spotiflac", "downloadReachable": True, "status": "healthy", "updatedAt": "2026-09-07"},
        {"slug": "uyouenhanced", "downloadReachable": True, "status": "healthy", "updatedAt": "2026-08-22"},
        {"slug": "ytlite", "downloadReachable": True, "status": "healthy", "updatedAt": "2026-09-01"},
    ]
}

VERIFICATION_DOC = {
    "apps": [
        {"app": "spotiflac", "status": "VERIFIED", "checks": {}, "reasons": []},
        {"app": "uyouenhanced", "status": "COMMUNITY", "checks": {}, "reasons": []},
        {"app": "ytlite", "status": "VERIFIED", "checks": {}, "reasons": []},
    ]
}


def _catalog() -> Catalog:
    return Catalog.from_dict(CATALOG)


class TrendingTests(unittest.TestCase):
    def test_trending_doc_has_three_lists(self) -> None:
        catalog = _catalog()
        doc = build_trending_doc(catalog, STATE, HEALTH_DOC, VERIFICATION_DOC)
        self.assertIn("trending", doc)
        self.assertIn("rising", doc)
        self.assertIn("recentlyUpdated", doc)
        # All apps in our fixture end up in the trending list.
        self.assertEqual(doc["count"], 3)
        # Scores are 0..1.
        for entry in doc["all"]:
            self.assertGreaterEqual(entry["score"], 0.0)
            self.assertLessEqual(entry["score"], 1.0)
        # The signal breakdown is preserved.
        for entry in doc["all"]:
            self.assertIn("signals", entry)
            self.assertEqual(set(entry["signals"]), {"recency", "availability", "featured", "verification"})


class RelatedTests(unittest.TestCase):
    def test_related_links_same_bundle(self) -> None:
        catalog = _catalog()
        doc = build_related_doc(catalog, STATE)
        # uyouenhanced and ytlite share bundle id, so they must be related.
        uyou = doc["related"]["uyouenhanced"]
        ytlite = doc["related"]["ytlite"]
        self.assertTrue(any(r["slug"] == "ytlite" for r in uyou))
        self.assertTrue(any(r["slug"] == "uyouenhanced" for r in ytlite))
        # spotiflac shares no bundle, but shares the music category.
        self.assertTrue(any(r["slug"] == "ytlite" or r["slug"] == "uyouenhanced" for r in doc["related"]["spotiflac"]))
        # Media ecosystem contains all apps that target youtube or youtube music bundles.
        media_slugs = {m["slug"] for m in doc["media"]["apps"]}
        self.assertIn("uyouenhanced", media_slugs)
        self.assertIn("ytlite", media_slugs)


class ReputationTests(unittest.TestCase):
    def test_reputation_doc_has_sources(self) -> None:
        catalog = _catalog()
        doc = build_reputation_doc(catalog, STATE, HEALTH_DOC)
        self.assertIn("sources", doc)
        self.assertGreater(len(doc["sources"]), 0)
        for source in doc["sources"]:
            self.assertIn(source["level"], {"TRUSTED", "RELIABLE", "AVERAGE", "EXPERIMENTAL"})
            self.assertGreaterEqual(source["score"], 0.0)
            self.assertLessEqual(source["score"], 100.0)


class DownloadIntelTests(unittest.TestCase):
    def test_summary_present(self) -> None:
        catalog = _catalog()
        doc = build_download_intel_doc(catalog, STATE, HEALTH_DOC)
        self.assertIn("summary", doc)
        self.assertIn("apps", doc)
        self.assertEqual(len(doc["apps"]), 3)
        # Every app carries availability, mirrorCount, consistency.
        for app in doc["apps"]:
            self.assertIn("availability", app)
            self.assertIn("mirrorCount", app)
            self.assertIn("releaseConsistency", app)


class CommunityTests(unittest.TestCase):
    def test_community_lists_present(self) -> None:
        catalog = _catalog()
        doc = build_community_doc(catalog, STATE)
        for key in ("popular", "recentlyAdded", "rising", "requested"):
            self.assertIn(key, doc)
            self.assertIsInstance(doc[key], list)


class SearchIndexTests(unittest.TestCase):
    def test_documents_have_id_and_bundle(self) -> None:
        catalog = _catalog()
        doc = build_search_index(catalog, STATE, HEALTH_DOC, VERIFICATION_DOC)
        self.assertEqual(doc["count"], 3)
        for entry in doc["documents"]:
            self.assertIn("id", entry)
            self.assertIn("bundleId", entry)
        # Fuse config is present.
        self.assertIn("keys", doc["fuse"])


class InstallTests(unittest.TestCase):
    def test_install_cards_for_each_client(self) -> None:
        catalog = _catalog()
        doc = build_install_doc(catalog)
        self.assertGreater(len(doc["apps"]), 0)
        for app in doc["apps"]:
            cards = app["cards"]
            self.assertEqual(len(cards), len(catalog.clients))
            for card in cards:
                self.assertIn("client", card)
                self.assertIn("name", card)
                self.assertIn("compatible", card)
                self.assertIn("recommended", card)
                # Recommended clients must have a URL.
                if card["recommended"]:
                    self.assertTrue(card["url"])


class CompareTests(unittest.TestCase):
    def test_pairs_include_same_bundle_pair(self) -> None:
        catalog = _catalog()
        doc = build_compare_doc(catalog, STATE, HEALTH_DOC, VERIFICATION_DOC)
        # 3 apps → 3 pairs.
        self.assertEqual(doc["count"], 3)
        # At least one pair should share a bundle.
        self.assertTrue(any(p["shareBundle"] for p in doc["pairs"]))
        for pair in doc["pairs"]:
            self.assertIn("left", pair)
            self.assertIn("right", pair)
            self.assertIn("winner", pair)


if __name__ == "__main__":
    unittest.main()
