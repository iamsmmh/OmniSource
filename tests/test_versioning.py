"""Tests for version parsing, comparison, and ordering."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import unittest

from omnisource.utils.versioning import Version, compare_versions, is_newer, parse_version


class TestVersioning(unittest.TestCase):
    def test_parse_version_numeric(self) -> None:
        self.assertEqual(parse_version("1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("v4.9.6"), (4, 9, 6))
        self.assertEqual(parse_version("ytl-ipa4"), (4,))
        self.assertEqual(parse_version(""), (0,))

    def test_version_parse_semver(self) -> None:
        v1 = Version.parse("1.2.3")
        self.assertTrue(v1.semver)
        self.assertEqual(v1.numbers, (1, 2, 3))
        self.assertEqual(v1.prerelease, ())

        v2 = Version.parse("v2.0.0-alpha.1")
        self.assertTrue(v2.semver)
        self.assertEqual(v2.numbers, (2, 0, 0))
        self.assertEqual(v2.prerelease, ("alpha", 1))

    def test_version_parse_non_semver(self) -> None:
        v = Version.parse("custom-tag-2026.09")
        self.assertFalse(v.semver)
        self.assertEqual(v.numbers, (2026, 9))

    def test_semver_ordering(self) -> None:
        # Standard SemVer 2.0.0 ordering test cases
        cases = [
            ("1.0.0-alpha", "1.0.0-alpha.1"),
            ("1.0.0-alpha.1", "1.0.0-alpha.beta"),
            ("1.0.0-alpha.beta", "1.0.0-beta"),
            ("1.0.0-beta", "1.0.0-beta.2"),
            ("1.0.0-beta.2", "1.0.0-beta.11"),
            ("1.0.0-beta.11", "1.0.0-rc.1"),
            ("1.0.0-rc.1", "1.0.0"),
            ("1.0.0", "1.0.1"),
            ("1.0.1", "1.1.0"),
            ("1.1.0", "2.0.0"),
        ]
        for lower, higher in cases:
            with self.subTest(lower=lower, higher=higher):
                v_lower = Version.parse(lower)
                v_higher = Version.parse(higher)
                self.assertLess(v_lower, v_higher)
                self.assertGreater(v_higher, v_lower)
                self.assertNotEqual(v_lower, v_higher)
                self.assertEqual(compare_versions(lower, higher), -1)
                self.assertEqual(compare_versions(higher, lower), 1)
                self.assertTrue(is_newer(higher, lower))
                self.assertFalse(is_newer(lower, higher))

    def test_version_equality(self) -> None:
        self.assertEqual(Version.parse("1.2.3"), Version.parse("v1.2.3"))
        self.assertEqual(Version.parse("1.0.0-alpha"), Version.parse("v1.0.0-alpha"))
        self.assertEqual(compare_versions("1.2.3", "v1.2.3"), 0)
        self.assertFalse(is_newer("1.2.3", "1.2.3"))

    def test_non_semver_comparison(self) -> None:
        self.assertEqual(compare_versions("ytl-ipa2", "ytl-ipa4"), -1)
        self.assertEqual(compare_versions("ytl-ipa4", "ytl-ipa2"), 1)
        self.assertEqual(compare_versions("app_1.0", "app_2.0"), -1)


if __name__ == "__main__":
    unittest.main()
