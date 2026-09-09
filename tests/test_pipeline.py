"""Integration tests for pipeline execution and CLI wrappers."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from omnisource.constants import PNG_MAGIC, Paths
from omnisource.di import Container
from omnisource.domain import SyncReport
from omnisource.pipeline import load_catalog, load_state, stage_build
from omnisource.providers.registry import ProviderRegistry


class TestPipeline(unittest.TestCase):
    def test_pipeline_builds_canonical_feeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paths = Paths.from_root(root)
            paths.feeds.mkdir(parents=True, exist_ok=True)
            paths.assets.mkdir(parents=True, exist_ok=True)

            (paths.assets / "OmniSource.png").write_bytes(PNG_MAGIC + b"source-icon")
            (paths.assets / "TestApp.png").write_bytes(PNG_MAGIC + b"app-icon")

            catalog_data = {
                "source": {
                    "name": "OmniSource",
                    "identifier": "com.iamsmmh.omnisource",
                    "baseURL": "https://iamsmmh.github.io/OmniSource",
                    "icon": "OmniSource.png",
                    "banner": "OmniSource.png",
                },
                "apps": [
                    {
                        "slug": "testapp",
                        "name": "Test App",
                        "bundleIdentifier": "com.example.testapp",
                        "developerName": "Tester",
                        "icon": "TestApp.png",
                        "status": "stable",
                        "compatibility": {"minOSVersion": "16.0", "clients": ["altstore"]},
                        "upstream": {
                            "provider": "github",
                            "repo": "example/testapp",
                        },
                    }
                ],
            }
            import json

            paths.catalog.write_text(json.dumps(catalog_data, indent=2), encoding="utf-8")

            state_data = {
                "testapp": {
                    "versions": [
                        {
                            "version": "1.0.0",
                            "date": "2026-09-07",
                            "localizedDescription": "Test release",
                            "downloadURL": "https://example.com/app.ipa",
                            "size": 5000,
                            "minOSVersion": "16.0",
                        }
                    ],
                    "health": {"reachable": True, "detail": "HTTP 200", "since": "2026-09-07"},
                }
            }
            (paths.feeds / "state.json").write_text(json.dumps(state_data, indent=2), encoding="utf-8")

            container = Container(
                paths=paths,
                http=MagicMock(),
                providers=ProviderRegistry(),
            )

            catalog = load_catalog(container)
            state = load_state(container)
            report = SyncReport()

            changed_feeds, _health_doc, _analytics_doc = stage_build(container, catalog, state, report)
            self.assertGreater(len(changed_feeds), 0)
            self.assertTrue((paths.feeds / "testapp.json").exists())
            self.assertTrue((paths.feeds / "apps.json").exists())
            self.assertTrue((paths.feeds / "health.json").exists())
            self.assertFalse((paths.root / "testapp.json").exists())
            self.assertFalse((paths.root / "apps.json").exists())


if __name__ == "__main__":
    unittest.main()
