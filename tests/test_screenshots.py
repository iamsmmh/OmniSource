"""Tests for screenshot mirror keep-last-good behavior."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from omnisource.domain import Catalog
from omnisource.screenshots import process_screenshots


def _catalog() -> Catalog:
    return Catalog.from_dict(
        {
            "source": {
                "name": "OmniSource",
                "identifier": "com.omnisource",
                "baseURL": "https://example.com/source",
            },
            "apps": [
                {
                    "slug": "demo",
                    "name": "Demo",
                    "bundleIdentifier": "com.example.demo",
                    "developerName": "Example",
                    "icon": "Demo.png",
                    "screenshots": ["https://example.com/shot-1.png"],
                }
            ],
        }
    )


_PREVIOUS = {
    "schemaVersion": 1,
    "screenshots": [
        {
            "slug": "demo",
            "index": 0,
            "originalURL": "https://example.com/shot-1.png",
            "mirroredURL": "https://example.com/source/assets/screenshots/demo/demo-01.png",
            "thumbnailURL": "https://example.com/source/assets/screenshots/thumbnails/demo/demo-01.webp",
            "thumbnailWidth": 480,
            "mirrored": True,
            "size": 12345,
            "sha256": "abc123",
            "thumbnailSize": 999,
        }
    ],
}


class TestScreenshotsKeepLastGood(unittest.TestCase):
    def test_offline_rebuild_reuses_previous_mirror(self) -> None:
        """An offline rebuild must not degrade known-good mirror metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = process_screenshots(
                _catalog(),
                base_url="https://example.com/source",
                assets_dir=Path(tmpdir),
                http=None,  # offline: no downloads possible
                previous=_PREVIOUS,
            )
        self.assertEqual(len(report.entries), 1)
        entry = report.entries[0]
        self.assertTrue(entry["mirrored"])
        self.assertEqual(entry["size"], 12345)
        self.assertEqual(entry["sha256"], "abc123")
        self.assertEqual(entry["thumbnailSize"], 999)

    def test_changed_url_does_not_reuse_stale_mirror(self) -> None:
        """A new remote URL must not inherit another URL's mirror metadata."""
        previous = {
            "screenshots": [
                {**_PREVIOUS["screenshots"][0], "originalURL": "https://example.com/old.png"}
            ]
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            report = process_screenshots(
                _catalog(),
                base_url="https://example.com/source",
                assets_dir=Path(tmpdir),
                http=None,
                previous=previous,
            )
        entry = report.entries[0]
        self.assertFalse(entry["mirrored"])
        self.assertEqual(entry["size"], 0)
        self.assertEqual(entry["sha256"], "")

    def test_first_build_without_previous(self) -> None:
        """A first build with no previous doc degrades gracefully, offline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = process_screenshots(
                _catalog(),
                base_url="https://example.com/source",
                assets_dir=Path(tmpdir),
                http=None,
            )
        entry = report.entries[0]
        self.assertFalse(entry["mirrored"])
        self.assertEqual(entry["originalURL"], "https://example.com/shot-1.png")


if __name__ == "__main__":
    unittest.main()
