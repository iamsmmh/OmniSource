"""Unit tests for version comparison, changelog extraction and asset selection."""

from __future__ import annotations

import unittest

from omnisource.domain import RemoteAsset, RemoteRelease, RepositoryRef, SourceType
from omnisource.tracking import (
    build_version_entry,
    compare_versions,
    detect_update,
    extract_changelog,
    extract_sha256,
    is_newer,
    parse_version,
    pick_asset,
    select_versions,
    tag_number,
    validate_version_entry,
)


class VersionComparisonTests(unittest.TestCase):
    def test_parse_version(self) -> None:
        self.assertEqual(parse_version("1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("v21.24.3"), (21, 24, 3))
        self.assertEqual(parse_version("no-digits"), (0,))

    def test_compare(self) -> None:
        self.assertEqual(compare_versions("1.2.3", "1.2.3"), 0)
        self.assertEqual(compare_versions("1.2.4", "1.2.3"), 1)
        self.assertEqual(compare_versions("1.2", "1.2.1"), -1)
        self.assertTrue(is_newer("4.9.5", "4.9.0"))
        self.assertFalse(is_newer("4.9.0", "4.9.5"))

    def test_tag_number(self) -> None:
        self.assertEqual(tag_number("ytl-ipa4"), 4)
        self.assertEqual(tag_number("release"), -1)


class ChecksumAndChangelogTests(unittest.TestCase):
    def test_extract_sha256_from_digest(self) -> None:
        digest = "sha256:" + ("ab" * 32)
        self.assertEqual(extract_sha256(digest), "ab" * 32)

    def test_extract_sha256_from_body(self) -> None:
        body = "SHA256: " + ("cd" * 32) + "\n"
        self.assertEqual(extract_sha256(body), "cd" * 32)

    def test_changelog_truncated(self) -> None:
        text = extract_changelog("hello\r\nworld", limit=8)
        self.assertTrue(text.startswith("hello"))
        self.assertLessEqual(len(text), 8)


class AssetSelectionTests(unittest.TestCase):
    def _release(self, *names: str) -> RemoteRelease:
        assets = tuple(RemoteAsset(name=name, download_url=f"https://example.com/{name}", size=10) for name in names)
        return RemoteRelease(
            tag="v1.0.0", name="1.0.0", body="notes", published_at="2026-01-01T00:00:00Z", assets=assets
        )

    def test_pick_suffix_priority(self) -> None:
        release = self._release("app-ios-unsigned.ipa", "app.ipa")
        asset = pick_asset(release, ("-ios-unsigned.ipa", ".ipa"))
        assert asset is not None
        self.assertEqual(asset.name, "app-ios-unsigned.ipa")

    def test_select_versions_keep_one(self) -> None:
        ref = RepositoryRef(provider=SourceType.GITHUB_RELEASES, repo="o/r", keep_versions=1)
        releases = [
            self._release("App_2.0.0.ipa"),
            RemoteRelease(
                tag="v1.0.0",
                name="1.0.0",
                body="",
                published_at="2025-01-01T00:00:00Z",
                assets=(RemoteAsset(name="App_1.0.0.ipa", download_url="https://example.com/old.ipa", size=1),),
            ),
        ]
        versions = select_versions(app_name="App", ref=ref, releases=releases)
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0]["version"], "2.0.0")
        self.assertNotIn("sha256", versions[0])

    def test_build_version_entry_iso_dates(self) -> None:
        ref = RepositoryRef(
            provider=SourceType.GITHUB_RELEASES,
            repo="o/r",
            iso_dates=True,
            description_template="{name} {version}",
        )
        release = RemoteRelease(
            tag="v4.7.5",
            name="4.7.5",
            body="Highlights",
            published_at="2026-01-03T17:51:54Z",
            assets=(RemoteAsset(name="UTM.ipa", download_url="https://example.com/UTM.ipa", size=12),),
        )
        entry = build_version_entry(app_name="UTM", ref=ref, release=release, asset=release.assets[0])
        self.assertEqual(entry["date"], "2026-01-03T17:51:54Z")
        self.assertIn("Highlights", entry["localizedDescription"])

    def test_detect_update(self) -> None:
        old = [{"version": "1.0.0", "downloadURL": "https://a"}]
        new = [{"version": "1.1.0", "downloadURL": "https://b"}]
        self.assertEqual(detect_update(old, new), "updated")
        self.assertEqual(detect_update(None, new), "new")
        self.assertEqual(detect_update(old, old), "unchanged")

    def test_validate_version_entry(self) -> None:
        self.assertEqual(
            validate_version_entry(
                {
                    "version": "1",
                    "downloadURL": "https://x",
                    "size": 1,
                    "localizedDescription": "d",
                    "date": "2026-01-01",
                }
            ),
            [],
        )
        problems = validate_version_entry({"version": "", "downloadURL": "", "size": -1})
        self.assertTrue(problems)


if __name__ == "__main__":
    unittest.main()
