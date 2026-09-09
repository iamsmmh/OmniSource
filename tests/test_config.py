"""Tests for configuration and runtime settings loader."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from omnisource.config import RuntimeSettings, load_runtime_settings


class TestConfig(unittest.TestCase):
    def test_runtime_settings_defaults(self) -> None:
        settings = RuntimeSettings()
        self.assertEqual(settings.sync_workers, 8)
        self.assertEqual(settings.health_workers, 8)
        self.assertEqual(settings.request_timeout, 30.0)
        self.assertEqual(settings.request_retries, 3)

    def test_from_dict(self) -> None:
        raw = {
            "syncWorkers": 12,
            "requestTimeout": 45,
            "maxUpdateHistory": 50,
            "staleAfterDays": 60,
        }
        settings = RuntimeSettings.from_dict(raw)
        self.assertEqual(settings.sync_workers, 12)
        self.assertEqual(settings.request_timeout, 45.0)
        self.assertEqual(settings.max_update_history, 50)
        self.assertEqual(settings.stale_after_days, 60)

    def test_stale_after_days_defaults(self) -> None:
        self.assertEqual(RuntimeSettings().stale_after_days, 90)

    def test_environment_overrides(self) -> None:
        settings = RuntimeSettings(sync_workers=4)
        with patch.dict(os.environ, {"OMNISOURCE_SYNC_WORKERS": "16"}):
            loaded = settings.with_environment()
            self.assertEqual(loaded.sync_workers, 16)

    def test_load_runtime_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            cfg_dir = root / "config"
            cfg_dir.mkdir()
            (cfg_dir / "settings.json").write_text('{"syncWorkers": 6}', encoding="utf-8")

            settings = load_runtime_settings(root)
            self.assertEqual(settings.sync_workers, 6)


if __name__ == "__main__":
    unittest.main()
