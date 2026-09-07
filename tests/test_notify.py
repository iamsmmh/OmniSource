"""Tests for Discord/Telegram webhook dispatchers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from omnisource.domain import UpdateEvent
from omnisource.notify import send_discord_notification, send_telegram_notification


class TestNotify(unittest.TestCase):
    def setUp(self) -> None:
        self.update = UpdateEvent(
            app_id="spotiflac",
            name="SpotiFLAC Mobile",
            version="4.9.6",
            previous_version="4.9.5",
            release_date="2026-09-07",
            download_url="https://example.com/SpotiFLAC.ipa",
            changelog="Lossless audio downloads.",
            kind="updated",
        )

    @patch("urllib.request.urlopen")
    def test_discord_notification(self, mock_urlopen: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        success = send_discord_notification("https://discord.com/api/webhooks/test", [self.update])
        self.assertTrue(success)
        mock_urlopen.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_telegram_notification(self, mock_urlopen: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        success = send_telegram_notification("token123", "chat456", [self.update])
        self.assertTrue(success)
        mock_urlopen.assert_called_once()

    def test_empty_updates(self) -> None:
        self.assertFalse(send_discord_notification("https://discord.com/api/webhooks/test", []))
        self.assertFalse(send_telegram_notification("token123", "chat456", []))


if __name__ == "__main__":
    unittest.main()
