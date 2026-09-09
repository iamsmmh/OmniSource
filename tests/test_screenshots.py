"""Tests for the screenshot mirror step (feeds/screenshots.json).

The mirror state must be reproducible offline: a mirror already on disk is
trusted, so an offline rebuild never flips ``mirrored`` based on this
machine's network reachability. Real sync runs pass ``refresh=True`` to
re-download and pick up upstream changes. When no mirror is on disk (a fresh
CI checkout never has them — mirrors are not committed to git), entries
whose remote URL is unchanged keep the last committed mirror metadata via
``previous`` instead of degrading to ``mirrored: false``.
"""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from omnisource.screenshots import process_screenshots

URL = "https://example.com/screens/shot-1.png"
PAYLOAD = b"\x89PNG fake screenshot bytes"


def _catalog() -> SimpleNamespace:
    app = SimpleNamespace(slug="demo", icon="Demo.png", screenshots=[URL])
    return SimpleNamespace(base_url="https://example.invalid/OmniSource", apps=[app])


class _FakeHttp:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.requests: list[str] = []

    def fetch_bytes(self, url: str) -> bytes:
        self.requests.append(url)
        return self.payload


def _screenshot_entries(report) -> list:
    return [entry for entry in report.entries if not entry.get("iconFallback")]


class TestScreenshotMirror(unittest.TestCase):
    def test_existing_local_mirror_is_trusted_offline(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            assets = Path(tmpdir) / "assets"
            assets.mkdir()
            mirror = assets / "screenshots" / "demo" / "demo-01.png"
            mirror.parent.mkdir(parents=True)
            mirror.write_bytes(PAYLOAD)
            # No network at all: http=None.
            report = process_screenshots(_catalog(), "https://example.invalid", assets)
        (entry,) = _screenshot_entries(report)
        self.assertTrue(entry["mirrored"])
        self.assertEqual(entry["size"], len(PAYLOAD))
        self.assertEqual(entry["sha256"], hashlib.sha256(PAYLOAD).hexdigest())

    def test_missing_mirror_without_network_stays_unmirrored(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            assets = Path(tmpdir) / "assets"
            assets.mkdir()
            report = process_screenshots(_catalog(), "https://example.invalid", assets)
        (entry,) = _screenshot_entries(report)
        self.assertFalse(entry["mirrored"])
        self.assertEqual(entry["size"], 0)
        self.assertEqual(entry["sha256"], "")

    def test_refresh_replaces_stale_local_mirror(self) -> None:
        fresh = b"\x89PNG updated screenshot bytes"
        with tempfile.TemporaryDirectory() as tmpdir:
            assets = Path(tmpdir) / "assets"
            assets.mkdir()
            mirror = assets / "screenshots" / "demo" / "demo-01.png"
            mirror.parent.mkdir(parents=True)
            mirror.write_bytes(PAYLOAD)
            http = _FakeHttp(fresh)
            report = process_screenshots(_catalog(), "https://example.invalid", assets, http=http, refresh=True)
            (entry,) = _screenshot_entries(report)
            self.assertEqual(mirror.read_bytes(), fresh)
        self.assertTrue(entry["mirrored"])
        self.assertEqual(entry["sha256"], hashlib.sha256(fresh).hexdigest())
        self.assertEqual(http.requests, [URL])

    def test_no_refresh_does_not_call_the_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            assets = Path(tmpdir) / "assets"
            assets.mkdir()
            mirror = assets / "screenshots" / "demo" / "demo-01.png"
            mirror.parent.mkdir(parents=True)
            mirror.write_bytes(PAYLOAD)
            http = _FakeHttp(b"other")
            report = process_screenshots(_catalog(), "https://example.invalid", assets, http=http)
            (entry,) = _screenshot_entries(report)
        self.assertEqual(http.requests, [])  # local mirror wins, no download
        self.assertEqual(entry["sha256"], hashlib.sha256(PAYLOAD).hexdigest())


_PREVIOUS = {
    "schemaVersion": 1,
    "screenshots": [
        {
            "slug": "demo",
            "index": 0,
            "originalURL": URL,
            "mirroredURL": "https://example.invalid/assets/screenshots/demo/demo-01.png",
            "thumbnailURL": "https://example.invalid/assets/screenshots/thumbnails/demo/demo-01.webp",
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
                base_url="https://example.invalid",
                assets_dir=Path(tmpdir),
                http=None,  # offline: no downloads possible
                previous=_PREVIOUS,
            )
        (entry,) = _screenshot_entries(report)
        self.assertTrue(entry["mirrored"])
        self.assertEqual(entry["size"], 12345)
        self.assertEqual(entry["sha256"], "abc123")
        self.assertEqual(entry["thumbnailSize"], 999)

    def test_changed_url_does_not_reuse_stale_mirror(self) -> None:
        """A new remote URL must not inherit another URL's mirror metadata."""
        previous = {"screenshots": [{**_PREVIOUS["screenshots"][0], "originalURL": "https://example.com/old.png"}]}
        with tempfile.TemporaryDirectory() as tmpdir:
            report = process_screenshots(
                _catalog(),
                base_url="https://example.invalid",
                assets_dir=Path(tmpdir),
                http=None,
                previous=previous,
            )
        (entry,) = _screenshot_entries(report)
        self.assertFalse(entry["mirrored"])
        self.assertEqual(entry["size"], 0)
        self.assertEqual(entry["sha256"], "")

    def test_first_build_without_previous(self) -> None:
        """A first build with no previous doc degrades gracefully, offline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = process_screenshots(
                _catalog(),
                base_url="https://example.invalid",
                assets_dir=Path(tmpdir),
                http=None,
            )
        (entry,) = _screenshot_entries(report)
        self.assertFalse(entry["mirrored"])
        self.assertEqual(entry["originalURL"], URL)


if __name__ == "__main__":
    unittest.main()
