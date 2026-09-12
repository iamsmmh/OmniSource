"""Tests for the per-client feed variants."""

from __future__ import annotations

from unittest import TestCase

from omnisource.feeds.clients import CLIENTS, filter_for_client, render_all, render_client_feed


def _envelope() -> dict:
    return {
        "name": "Test",
        "identifier": "com.test",
        "apps": [
            {
                "name": "Good",
                "bundleIdentifier": "com.good",
                "downloadURL": "https://example.com/good.ipa",
                "iconURL": "https://example.com/icon.png",
                "size": 100,
            },
            {
                "name": "Nolink",
                "bundleIdentifier": "com.nolink",
                "downloadURL": "https://github.com/octo/repo",
                "iconURL": "icon.png",
                "size": 0,
            },
        ],
    }


class ClientFeedTests(TestCase):
    def test_all_clients_render(self) -> None:
        feeds = render_all(_envelope())
        self.assertEqual(set(feeds), set(CLIENTS))
        for client, feed in feeds.items():
            self.assertEqual(feed["client"], client)
            self.assertIn("apps", feed)

    def test_esign_filters_weak_entries(self) -> None:
        feed = render_client_feed(_envelope(), "esign")
        self.assertEqual([app["name"] for app in feed["apps"]], ["Good"])

    def test_feather_drops_relative_icons(self) -> None:
        feed = render_client_feed(_envelope(), "feather")
        by_name = {app["name"]: app for app in feed["apps"]}
        self.assertEqual(by_name["Nolink"]["iconURL"], "")

    def test_livecontainer_tags_bundle_alias(self) -> None:
        feed = render_client_feed(_envelope(), "livecontainer")
        self.assertEqual(feed["apps"][0]["omnisource"]["bundleAlias"], "com.good")

    def test_unknown_client_rejected(self) -> None:
        with self.assertRaises(ValueError):
            render_client_feed(_envelope(), "nope")

    def test_filter_for_client_passthrough(self) -> None:
        app = _envelope()["apps"][0]
        self.assertIsNotNone(filter_for_client(app, "altstore"))
        self.assertIsNone(filter_for_client(_envelope()["apps"][1], "esign"))


if __name__ == "__main__":
    import unittest

    unittest.main()
