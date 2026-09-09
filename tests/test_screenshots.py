"""Tests for the screenshot mirror step (feeds/screenshots.json).

The mirror state must be reproducible offline: a mirror already on disk is
trusted, so an offline rebuild never flips ``mirrored`` based on this
machine's network reachability. Real sync runs pass ``refresh=True`` to
re-download and pick up upstream changes.
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
        (entry,) = [e for e in report.entries if not e.get("iconFallback")]
        self.assertTrue(entry["mirrored"])
        self.assertEqual(entry["size"], len(PAYLOAD))
        self.assertEqual(entry["sha256"], hashlib.sha256(PAYLOAD).hexdigest())

    def test_missing_mirror_without_network_stays_unmirrored(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            assets = Path(tmpdir) / "assets"
            assets.mkdir()
            report = process_screenshots(_catalog(), "https://example.invalid", assets)
        (entry,) = [e for e in report.entries if not e.get("iconFallback")]
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
            (entry,) = [e for e in report.entries if not e.get("iconFallback")]
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
            (entry,) = [e for e in report.entries if not e.get("iconFallback")]
        self.assertEqual(http.requests, [])  # local mirror wins, no download
        self.assertEqual(entry["sha256"], hashlib.sha256(PAYLOAD).hexdigest())


if __name__ == "__main__":
    unittest.main()
