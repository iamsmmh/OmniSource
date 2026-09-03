"""Analytics sink is a no-op by default and satisfies the protocol."""

from __future__ import annotations

import unittest

from omnisource.analytics import AnalyticsSink, NullAnalytics


class NullAnalyticsTests(unittest.TestCase):
    def test_protocol(self) -> None:
        sink: AnalyticsSink = NullAnalytics()
        sink.record_download("demo", "1.0")
        sink.record_update("demo", "1.0", "1.1")
        sink.record_repository_seen("https://github.com/o/r", 3)
        sink.record_health("demo", True)
        self.assertIsInstance(sink, NullAnalytics)


if __name__ == "__main__":
    unittest.main()
