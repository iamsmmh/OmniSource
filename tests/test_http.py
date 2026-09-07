"""Tests for HTTP client, auth rules, and URL helpers."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import unittest

from omnisource.http import AuthRule, HttpClient, is_http_url


class TestHttp(unittest.TestCase):
    def test_is_http_url(self) -> None:
        self.assertTrue(is_http_url("https://github.com/owner/repo"))
        self.assertTrue(is_http_url("http://example.com/feed.json"))
        self.assertFalse(is_http_url("ftp://example.com"))
        self.assertFalse(is_http_url("not-a-url"))
        self.assertFalse(is_http_url(""))
        self.assertFalse(is_http_url(None))

    def test_auth_rule_matching(self) -> None:
        rule = AuthRule("https://api.github.com", "Authorization", "Bearer token123")
        self.assertTrue(rule.matches("https://api.github.com/repos/owner/repo"))
        self.assertTrue(rule.matches("https://api.github.com/"))
        self.assertFalse(rule.matches("https://github.com/owner/repo"))
        self.assertFalse(rule.matches("https://other-api.com"))

    def test_http_client_auth_headers(self) -> None:
        rule = AuthRule("https://api.github.com", "Authorization", "Bearer token123")
        client = HttpClient(user_agent="OmniSource/Test", auth_rules=(rule,))

        headers_gh = client._auth_headers("https://api.github.com/user")
        self.assertEqual(headers_gh.get("Authorization"), "Bearer token123")
        self.assertEqual(headers_gh.get("User-Agent"), "OmniSource/Test")

        headers_other = client._auth_headers("https://archive.org/download/item.ipa")
        self.assertNotIn("Authorization", headers_other)
        self.assertEqual(headers_other.get("User-Agent"), "OmniSource/Test")


if __name__ == "__main__":
    unittest.main()
