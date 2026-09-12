"""Tests for the feed merge safety net and install deep links."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from omnisource.constants import ALTSTORE_NON_FEED
from omnisource.install import install_url

_SPEC = importlib.util.spec_from_file_location("merge_feeds", _ROOT / "scripts" / "merge_feeds.py")
assert _SPEC and _SPEC.loader, "cannot load scripts/merge_feeds.py"
MERGE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(MERGE)


def _app_entry(name: str, bundle: str) -> dict:
    return {"name": name, "bundleIdentifier": bundle, "version": "1.0"}


def _feed_doc(name: str, bundle: str) -> dict:
    return {
        "name": "OmniSource",
        "identifier": "com.example.omnisource",
        "apiVersion": "v2",
        "sourceURL": "https://example.com/old.json",
        "apps": [_app_entry(name, bundle)],
    }


class TestMergeFeeds(unittest.TestCase):
    def test_non_feed_set_covers_all_intelligence_docs(self) -> None:
        """Every derived document the pipeline writes must be excluded from the merge."""
        intelligence = {
            "state.json",
            "health.json",
            "updates.json",
            "discovery.json",
            "verification.json",
            "status.json",
            "duplicates.json",
            "analytics.json",
            "sources.json",
            "trending.json",
            "related.json",
            "reputation.json",
            "download-intelligence.json",
            "community.json",
            "install.json",
            "search-index.json",
            "compare.json",
            "screenshots.json",
        }
        self.assertTrue(
            intelligence <= set(ALTSTORE_NON_FEED),
            f"merge would treat as per-app feeds: {sorted(intelligence - set(ALTSTORE_NON_FEED))}",
        )

    def test_intelligence_docs_are_not_merged(self) -> None:
        """Regression test: trending/community/... docs must not break the merge."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feeds = Path(tmpdir)
            (feeds / "alpha.json").write_text(json.dumps(_feed_doc("Alpha", "com.example.alpha")))
            (feeds / "beta.json").write_text(json.dumps(_feed_doc("Beta", "com.example.beta")))
            # Intelligence-shaped documents: no single-app "apps" entry.
            (feeds / "trending.json").write_text(json.dumps({"trending": [{"slug": "alpha"}]}))
            (feeds / "community.json").write_text(json.dumps({"popular": []}))
            (feeds / "install.json").write_text(json.dumps({"apps": [_app_entry("A", "x"), _app_entry("B", "y")]}))

            previous_feeds, previous_catalog = MERGE.FEEDS_DIR, MERGE.CATALOG_PATH
            MERGE.FEEDS_DIR, MERGE.CATALOG_PATH = feeds, feeds / "catalog.json"
            try:
                names = sorted(p.name for p in MERGE.per_app_feeds())
                self.assertEqual(names, ["alpha.json", "beta.json"])
                master = MERGE.build_master()
            finally:
                MERGE.FEEDS_DIR, MERGE.CATALOG_PATH = previous_feeds, previous_catalog

            self.assertEqual([a["name"] for a in master["apps"]], ["Alpha", "Beta"])
            self.assertTrue(master["sourceURL"].endswith("/apps.json"))


class TestInstallUrl(unittest.TestCase):
    def test_deep_links(self) -> None:
        feed = "https://example.com/OmniSource/alpha.json"
        self.assertEqual(install_url("altstore", feed), f"altstore://source?url={feed}")
        self.assertEqual(install_url("sidestore", feed), f"sidestore://source?url={feed}")
        self.assertEqual(
            install_url("feather", feed),
            "feather://source/example.com/OmniSource/alpha.json",
        )
        self.assertEqual(install_url("esign", feed), f"esign://addsource?url={feed}")
        self.assertEqual(install_url("livecontainer", feed), f"livecontainer://sources?url={feed}")

    def test_unknown_clients_have_no_deep_link(self) -> None:
        feed = "https://example.com/OmniSource/alpha.json"
        self.assertEqual(install_url("unknown-client", feed), "")


if __name__ == "__main__":
    unittest.main()


class TestMasterFeedExclusion(unittest.TestCase):
    """One member of each bundle-ID collision group must not reach apps.json (#7)."""

    def _workspace(self, tmpdir: str) -> Path:
        root = Path(tmpdir)
        feeds = root / "feeds"
        feeds.mkdir(parents=True, exist_ok=True)
        catalog = {
            "source": {
                "name": "OmniSource",
                "identifier": "com.example.omnisource",
                "baseURL": "https://example.com",
                "icon": "Icon.png",
                "banner": "Icon.png",
            },
            "apps": [
                {"slug": "yt-a", "name": "YT A", "bundleIdentifier": "com.google.ios.youtube"},
                {"slug": "yt-b", "name": "YT B", "bundleIdentifier": "com.google.ios.youtube"},
            ],
        }
        (root / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
        for slug, name in (("yt-a", "YT A"), ("yt-b", "YT B")):
            (feeds / f"{slug}.json").write_text(json.dumps(_feed_doc(name, "com.google.ios.youtube")), encoding="utf-8")
        (feeds / "duplicates.json").write_text(
            json.dumps(
                {
                    "groups": [
                        {
                            "key": "com.google.ios.youtube",
                            "type": "bundle-id",
                            "replacementRisk": True,
                            "apps": [{"app": "yt-a"}, {"app": "yt-b"}],
                            "recommended": {"app": "yt-b"},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        return root

    def test_recommended_member_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._workspace(tmpdir)
            with (
                mock.patch.object(MERGE, "REPO_ROOT", root),
                mock.patch.object(MERGE, "CATALOG_PATH", root / "catalog.json"),
                mock.patch.object(MERGE, "FEEDS_DIR", root / "feeds"),
            ):
                _envelope, apps = MERGE.gather_apps()
            self.assertEqual([app["name"] for app in apps], ["YT B"])

    def test_annotation_is_used_when_duplicates_doc_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._workspace(tmpdir)
            (root / "feeds" / "duplicates.json").unlink()
            entry = _feed_doc("YT A", "com.google.ios.youtube")
            entry["apps"][0]["omnisource"] = {"slug": "yt-a", "masterFeed": False}
            (root / "feeds" / "yt-a.json").write_text(json.dumps(entry), encoding="utf-8")
            with (
                mock.patch.object(MERGE, "REPO_ROOT", root),
                mock.patch.object(MERGE, "CATALOG_PATH", root / "catalog.json"),
                mock.patch.object(MERGE, "FEEDS_DIR", root / "feeds"),
            ):
                _envelope, apps = MERGE.gather_apps()
            self.assertEqual([app["name"] for app in apps], ["YT B"])
