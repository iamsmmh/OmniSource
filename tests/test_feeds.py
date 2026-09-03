"""AltStore + OmniStore renderer tests."""

from __future__ import annotations

import unittest

from omnisource.domain import Catalog, UpdateEvent
from omnisource.feeds.altstore import render_altstore_app
from omnisource.feeds.omnistore import render_omnistore_bundle, standardize_app


def _catalog() -> Catalog:
    return Catalog.from_dict(
        {
            "source": {
                "name": "OmniSource",
                "identifier": "com.example.omnisource",
                "baseURL": "https://example.com/OmniSource",
                "icon": "OmniSource.png",
                "tintColor": "5B5BD6",
            },
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
                    "screenshots": ["https://example.com/shot.png"],
                    "featured": True,
                    "status": "stable",
                    "upstreamURL": "https://github.com/owner/demo",
                    "tags": ["utilities", "demo"],
                    "verification": {"method": "github-release", "publisher": "owner/demo"},
                    "compatibility": {"minOSVersion": "16.0", "clients": ["altstore"]},
                    "upstream": {"repo": "owner/demo"},
                }
            ],
        }
    )


VERSIONS = [
    {
        "version": "1.2.3",
        "date": "2026-01-02",
        "localizedDescription": "Demo 1.2.3 | notes",
        "downloadURL": "https://github.com/owner/demo/releases/download/v1.2.3/Demo.ipa",
        "size": 100,
        "minOSVersion": "16.0",
    }
]


class AltStoreRenderTests(unittest.TestCase):
    def test_flat_fields_mirror_versions_zero(self) -> None:
        catalog = _catalog()
        health = {"reachable": True, "detail": "HTTP 302", "since": "2026-01-02"}
        entry = render_altstore_app(catalog, catalog.apps[0], VERSIONS, health)
        self.assertEqual(entry["version"], "1.2.3")
        self.assertEqual(entry["versionDate"], entry["versions"][0]["date"])
        self.assertEqual(entry["downloadURL"], entry["versions"][0]["downloadURL"])
        self.assertEqual(entry["size"], 100)
        self.assertEqual(entry["omnisource"]["slug"], "demo")
        self.assertTrue(entry["omnisource"]["health"]["downloadReachable"])
        self.assertEqual(entry["iconURL"], "https://example.com/OmniSource/assets/Demo.png")


class OmniStoreRenderTests(unittest.TestCase):
    def test_standardize_and_bundle(self) -> None:
        catalog = _catalog()
        app = standardize_app(catalog, catalog.apps[0], VERSIONS)
        self.assertEqual(app.app_id, "demo")
        self.assertEqual(app.bundle_id, "com.example.demo")
        self.assertEqual(app.source_type, "github")
        payload = app.to_json()
        self.assertEqual(payload["downloadUrl"], VERSIONS[0]["downloadURL"])
        bundle = render_omnistore_bundle(
            catalog,
            versions_by_slug={"demo": VERSIONS},
            updates=[
                UpdateEvent(
                    app_id="demo",
                    name="Demo",
                    version="1.2.3",
                    previous_version="1.2.2",
                    release_date="2026-01-02",
                    download_url=VERSIONS[0]["downloadURL"],
                    changelog="notes",
                    kind="updated",
                )
            ],
        )
        self.assertEqual(bundle["apps.json"]["count"], 1)
        self.assertEqual(bundle["featured.json"]["count"], 1)
        self.assertEqual(bundle["categories.json"]["categories"][0]["id"], "utilities")
        self.assertEqual(bundle["updates.json"]["count"], 1)
        self.assertEqual(bundle["repositories.json"]["count"], 1)
        self.assertIn("demo", bundle["search-index.json"]["index"])


if __name__ == "__main__":
    unittest.main()
