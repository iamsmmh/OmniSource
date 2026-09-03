"""Offline pipeline integration tests against a temporary tree."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from omnisource.assets import DirectoryCache, inspect_catalog
from omnisource.constants import Paths
from omnisource.di import build_container
from omnisource.domain import Catalog
from omnisource.http import HttpClient
from omnisource.io import write_json
from omnisource.pipeline import run
from omnisource.validation import validate_omnistore_apps, validate_tree


def _write_png(path: Path) -> None:
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)


class PipelineOfflineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(self._tmp())
        assets = self.tmp / "assets"
        assets.mkdir(parents=True)
        _write_png(assets / "OmniSource.png")
        _write_png(assets / "Demo.png")
        catalog = {
            "source": {
                "name": "OmniSource",
                "identifier": "com.example.omnisource",
                "baseURL": "https://example.com/OmniSource",
                "icon": "OmniSource.png",
                "banner": "OmniSource.png",
                "tintColor": "5B5BD6",
            },
            "clients": [],
            "apps": [
                {
                    "slug": "demo",
                    "name": "Demo",
                    "subtitle": "A demo",
                    "bundleIdentifier": "com.example.demo",
                    "developerName": "dev",
                    "category": "utilities",
                    "tintColor": "FF0000",
                    "icon": "Demo.png",
                    "localizedDescription": "Hello",
                    "screenshots": [],
                    "featured": True,
                    "status": "manual",
                    "upstreamURL": "https://github.com/owner/demo",
                    "verification": {
                        "method": "manual-mirror",
                        "publisher": "owner/demo",
                        "codeSigned": False,
                        "checksumPublished": False,
                    },
                    "compatibility": {
                        "minOSVersion": "16.0",
                        "maxOSVersion": None,
                        "devices": ["iphone"],
                        "clients": ["altstore"],
                    },
                    "upstream": None,
                    "manualRelease": {
                        "version": "1.0.0",
                        "date": "2026-01-01",
                        "localizedDescription": "first",
                        "downloadURL": "https://example.com/demo.ipa",
                        "size": 1234,
                        "minOSVersion": "16.0",
                    },
                }
            ],
        }
        write_json(self.tmp / "catalog.json", catalog)
        (self.tmp / "README.md").write_text(
            "<!-- omnisource:catalog:start -->\n\n<!-- omnisource:catalog:end -->\n",
            encoding="utf-8",
        )
        self.paths = Paths.from_root(self.tmp)
        self.container = build_container(paths=self.paths, http=HttpClient(auth_rules=()))

    def _tmp(self) -> str:
        import tempfile

        self._dir = tempfile.TemporaryDirectory()
        return self._dir.name

    def tearDown(self) -> None:
        self._dir.cleanup()

    def test_offline_build_is_idempotent(self) -> None:
        # upstream is null, so sync uses manualRelease and needs no network.
        code, report = run(container=self.container, no_sync=False, no_health=True, no_mirror=False)
        self.assertEqual(code, 0)
        self.assertGreaterEqual(report.files_changed, 1)
        altstore = json.loads((self.paths.feeds / "demo.json").read_text(encoding="utf-8"))
        self.assertEqual(altstore["apps"][0]["version"], "1.0.0")
        self.assertEqual(altstore["apps"][0]["size"], 1234)
        omni = json.loads((self.paths.omnistore / "apps.json").read_text(encoding="utf-8"))
        self.assertEqual(omni["apps"][0]["appId"], "demo")
        self.assertEqual(omni["apps"][0]["downloadUrl"], "https://example.com/demo.ipa")
        self.assertTrue((self.paths.api / "openapi.json").is_file())
        self.assertTrue((self.paths.api / "apps" / "demo.json").is_file())
        self.assertTrue((self.tmp / "demo.json").is_file())

        code2, report2 = run(container=self.container, no_sync=True, no_health=True)
        self.assertEqual(code2, 0)
        self.assertEqual(report2.files_changed, 0)

        tree = validate_tree(self.paths, skip_mirrors=False)
        self.assertEqual(tree.errors, [], tree.errors)
        omni_report = validate_omnistore_apps(self.paths.omnistore / "apps.json", omni, root=self.tmp)
        self.assertEqual(omni_report.errors, [])

    def test_sync_uses_manual_release_without_upstream(self) -> None:
        code, _report = run(container=self.container, no_sync=False, no_health=True)
        self.assertEqual(code, 0)
        state = json.loads((self.paths.feeds / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["demo"]["versions"][0]["version"], "1.0.0")

    def test_asset_inspector_and_cache(self) -> None:
        catalog = Catalog.from_dict(json.loads((self.tmp / "catalog.json").read_text(encoding="utf-8")))
        report = inspect_catalog(catalog, assets_dir=self.paths.assets)
        self.assertEqual(report.icons_ok, 1)
        cache = DirectoryCache(self.paths.cache)
        cache.put("hello", b"world")
        self.assertEqual(cache.get("hello"), b"world")
        self.assertTrue(cache.has("hello"))


if __name__ == "__main__":
    unittest.main()
