"""Tests for offline validator."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import tempfile
import unittest
from pathlib import Path

from omnisource.constants import PNG_MAGIC
from omnisource.validation import (
    validate_catalog,
    validate_feed,
)


class TestValidation(unittest.TestCase):
    def test_validate_catalog_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            assets_dir = Path(tmpdir)
            (assets_dir / "Icon.png").write_bytes(PNG_MAGIC + b"data")

            catalog = {
                "source": {
                    "name": "OmniSource",
                    "identifier": "com.omnisource",
                    "baseURL": "https://example.com",
                    "icon": "Icon.png",
                },
                "apps": [
                    {
                        "slug": "app-one",
                        "name": "App One",
                        "bundleIdentifier": "com.example.appone",
                        "developerName": "Dev",
                        "icon": "Icon.png",
                        "status": "stable",
                        "localizedDescription": "A great app.",
                        "compatibility": {
                            "minOSVersion": "16.0",
                            "clients": ["altstore", "sidestore"],
                        },
                        "upstream": {
                            "provider": "github",
                            "repo": "owner/repo",
                        },
                    }
                ],
            }
            report = validate_catalog(catalog, assets_dir=assets_dir)
            self.assertEqual(len(report.errors), 0)

    def test_duplicate_bundle_identifiers_warn(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            assets_dir = Path(tmpdir)
            (assets_dir / "Icon.png").write_bytes(PNG_MAGIC + b"data")
            catalog = {
                "source": {
                    "name": "OmniSource",
                    "identifier": "com.omnisource",
                    "baseURL": "https://example.com",
                    "icon": "Icon.png",
                },
                "apps": [
                    {
                        "slug": "app-a",
                        "name": "App A",
                        "bundleIdentifier": "com.example.shared",
                        "developerName": "Dev",
                        "icon": "Icon.png",
                        "status": "stable",
                        "localizedDescription": "A great app.",
                        "compatibility": {"minOSVersion": "16.0", "clients": ["altstore"]},
                        "upstream": {"provider": "github", "repo": "owner/repo"},
                    },
                    {
                        "slug": "app-b",
                        "name": "App B",
                        "bundleIdentifier": "com.example.shared",
                        "developerName": "Dev",
                        "icon": "Icon.png",
                        "status": "stable",
                        "localizedDescription": "Another app.",
                        "compatibility": {"minOSVersion": "16.0", "clients": ["altstore"]},
                        "upstream": {"provider": "github", "repo": "owner/repo"},
                    },
                ],
            }
            report = validate_catalog(catalog, assets_dir=assets_dir)
            self.assertEqual(len(report.errors), 0)
            messages = " | ".join(report.warnings)
            self.assertIn("com.example.shared", messages)
            self.assertIn("app-a", messages)
            self.assertIn("app-b", messages)

    def test_validate_catalog_missing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            assets_dir = Path(tmpdir)
            catalog = {
                "source": {},
                "apps": [
                    {
                        "slug": "INVALID_SLUG",
                    }
                ],
            }
            report = validate_catalog(catalog, assets_dir=assets_dir)
            self.assertGreater(len(report.errors), 0)

    def test_validate_feed(self) -> None:
        valid_feed = {
            "name": "OmniSource",
            "identifier": "com.omnisource",
            "apps": [
                {
                    "name": "Test App",
                    "bundleIdentifier": "com.test.app",
                    "developerName": "Dev",
                    "version": "1.0.0",
                    "versionDate": "2026-09-07",
                    "localizedDescription": "Description",
                    "downloadURL": "https://example.com/app.ipa",
                    "size": 1000,
                    "iconURL": "https://example.com/icon.png",
                    "tintColor": "FF0000",
                    "versions": [
                        {
                            "version": "1.0.0",
                            "date": "2026-09-07",
                            "localizedDescription": "Description",
                            "downloadURL": "https://example.com/app.ipa",
                            "size": 1000,
                        }
                    ],
                }
            ],
        }
        report = validate_feed(Path("test.json"), valid_feed, root=Path())
        self.assertEqual(len(report.errors), 0)


if __name__ == "__main__":
    unittest.main()
