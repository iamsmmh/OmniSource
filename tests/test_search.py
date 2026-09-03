"""Search index tests."""

from __future__ import annotations

import unittest

from omnisource.domain import StandardizedApp
from omnisource.search import InMemoryIndex, SearchDocument, build_search_index, tokenize


def _app(app_id: str, name: str, developer: str, category: str, description: str) -> StandardizedApp:
    return StandardizedApp(
        app_id=app_id,
        name=name,
        developer=developer,
        description=description,
        icon="https://example.com/icon.png",
        screenshots=(),
        category=category,
        version="1.0",
        build_number=None,
        release_date="2026-01-01",
        bundle_id=f"com.example.{app_id}",
        minimum_os_version="16.0",
        source_type="github",
        repository_url="https://github.com/example/app",
        changelog="",
        download_url="https://example.com/app.ipa",
        sha256=None,
        tags=(category,),
    )


class SearchTests(unittest.TestCase):
    def test_tokenize_drops_stopwords(self) -> None:
        self.assertEqual(tokenize("The FLAC Downloader for iOS"), ["flac", "downloader", "ios"])

    def test_name_outranks_description(self) -> None:
        apps = [
            _app("spotiflac", "SpotiFLAC Mobile", "zarzet", "utilities", "a music downloader"),
            _app("utm", "UTM", "UTM Team", "utilities", "virtual machines and flac mention"),
        ]
        index = InMemoryIndex()
        index.index([SearchDocument.from_app(app) for app in apps])
        hits = index.search("spotiflac")
        self.assertEqual(hits[0].app_id, "spotiflac")
        hits = index.search("utilities")
        self.assertEqual({hit.app_id for hit in hits}, {"spotiflac", "utm"})

    def test_dump_is_client_friendly(self) -> None:
        apps = [_app("utm", "UTM", "UTM Team", "utilities", "virtual machines")]
        dumped = build_search_index(apps)
        self.assertEqual(dumped["documentCount"], 1)
        self.assertIn("utm", dumped["index"])
        self.assertEqual(dumped["documents"][0]["appId"], "utm")


if __name__ == "__main__":
    unittest.main()
