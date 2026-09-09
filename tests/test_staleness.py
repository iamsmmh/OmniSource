"""Tests for the release-staleness annotations on the health document."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from omnisource.pipeline import _annotate_staleness, _days_since


class TestDaysSince(unittest.TestCase):
    def test_basic(self) -> None:
        self.assertEqual(_days_since("2026-09-01", today_iso="2026-09-09"), 8)

    def test_future_and_bad_dates_clamp_to_zero(self) -> None:
        self.assertEqual(_days_since("2026-09-20", today_iso="2026-09-09"), 0)
        self.assertEqual(_days_since("not-a-date", today_iso="2026-09-09"), 0)
        self.assertEqual(_days_since("", today_iso="2026-09-09"), 0)

    def test_full_iso_timestamp_uses_date_part(self) -> None:
        self.assertEqual(_days_since("2026-09-01T12:30:00Z", today_iso="2026-09-09"), 8)


class TestAnnotateStaleness(unittest.TestCase):
    def test_marks_old_releases_as_stale(self) -> None:
        health_doc = {
            "apps": [
                {"slug": "old", "status": "stable", "updatedAt": "2020-01-01"},
                {"slug": "fresh", "status": "stable", "updatedAt": "2026-09-08"},
                {"slug": "retired", "status": "unmaintained", "updatedAt": "2020-01-01"},
            ]
        }
        _annotate_staleness(health_doc, stale_after_days=90)
        entries = {entry["slug"]: entry for entry in health_doc["apps"]}
        self.assertTrue(entries["old"]["stale"])
        self.assertGreater(entries["old"]["updatedDaysAgo"], 90)
        self.assertFalse(entries["fresh"]["stale"])
        self.assertLess(entries["fresh"]["updatedDaysAgo"], 90)
        self.assertFalse(entries["retired"]["stale"])


if __name__ == "__main__":
    unittest.main()
