"""Tests for the translation coverage document builder."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from omnisource.translations import build_translation_status_doc, flatten_locale, js_round


def _write_locales(root: Path, files: dict[str, object]) -> Path:
    locales = root / "locales"
    locales.mkdir(parents=True, exist_ok=True)
    for name, doc in files.items():
        (locales / f"{name}.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return locales


class TestFlattenLocale(unittest.TestCase):
    def test_nested_objects_flatten_with_dotted_keys(self) -> None:
        data = {"nav": {"home": "Home", "compare": "Compare"}, "version": 3}
        self.assertEqual(flatten_locale(data), {"nav.home": "Home", "nav.compare": "Compare", "version": 3})

    def test_deep_nesting(self) -> None:
        self.assertEqual(flatten_locale({"a": {"b": {"c": 1}}}), {"a.b.c": 1})

    def test_arrays_and_scalars_are_leaves(self) -> None:
        data = {"list": [1, 2], "n": None, "flag": False, "empty": ""}
        self.assertEqual(flatten_locale(data), {"list": [1, 2], "n": None, "flag": False, "empty": ""})


class TestJsRound(unittest.TestCase):
    def test_matches_javascript_math_round(self) -> None:
        # JS Math.round rounds halves up; Python's round() uses banker's
        # rounding and would disagree on the .5 boundaries.
        self.assertEqual(js_round(98.5), 99)
        self.assertEqual(js_round(99.5), 100)
        self.assertEqual(js_round(74.9), 75)
        self.assertEqual(js_round(74.4), 74)
        self.assertEqual(js_round(0.0), 0)
        self.assertEqual(js_round(100.0), 100)


class TestBuildTranslationStatusDoc(unittest.TestCase):
    def test_full_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            locales = _write_locales(root, {"en": {"nav": {"home": "Home"}}, "es": {"nav": {"home": "Inicio"}}})
            self.assertEqual(build_translation_status_doc(locales), {"en": 100, "es": 100})

    def test_missing_keys_lower_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            en = {"a": "1", "b": "2", "c": "3", "d": "4"}
            es = {"a": "1", "b": "2", "c": "3"}
            locales = _write_locales(root, {"en": en, "es": es})
            self.assertEqual(build_translation_status_doc(locales), {"en": 100, "es": 75})

    def test_rounding_boundary_matches_node(self) -> None:
        # 200 canonical keys, 3 missing -> 98.5 -> 99 under JS Math.round
        # (Python's round(98.5) would give 98 and desync the engines).
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            en = {f"key{i:03d}": "value" for i in range(200)}
            partial = {f"key{i:03d}": "value" for i in range(197)}
            locales = _write_locales(root, {"en": en, "es": partial})
            self.assertEqual(build_translation_status_doc(locales), {"en": 100, "es": 99})

    def test_locale_keys_are_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            locales = _write_locales(root, {"zz": {"a": "1"}, "aa": {"a": "1"}, "en": {"a": "1"}})
            doc = build_translation_status_doc(locales)
            self.assertEqual(list(doc), sorted(doc))

    def test_extra_locale_keys_do_not_inflate_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            locales = _write_locales(root, {"en": {"a": "1"}, "es": {"a": "1", "extra": "2"}})
            self.assertEqual(build_translation_status_doc(locales), {"en": 100, "es": 100})

    def test_missing_locales_dir_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, self.assertRaises(ValueError):
            build_translation_status_doc(Path(tmpdir) / "locales")

    def test_missing_canonical_locale_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            locales = _write_locales(root, {"es": {"a": "1"}})
            with self.assertRaises(ValueError):
                build_translation_status_doc(locales)

    def test_empty_canonical_locale_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            locales = _write_locales(root, {"en": {}})
            with self.assertRaises(ValueError):
                build_translation_status_doc(locales)

    def test_non_object_locale_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            locales = _write_locales(root, {"en": ["a", "b"]})
            with self.assertRaises(ValueError):
                build_translation_status_doc(locales)

    def test_invalid_json_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            locales = _write_locales(root, {"en": {"a": "1"}})
            (locales / "es.json").write_text("{not json", encoding="utf-8")
            with self.assertRaises(ValueError):
                build_translation_status_doc(locales)

    def test_serialization_matches_node_output(self) -> None:
        # Node writes JSON.stringify(report, null, 2) + '\n'; the build's
        # dumps_pretty must agree so both engines produce identical bytes.
        payload = json.dumps({"en": 100, "es": 98}, indent=2, ensure_ascii=False) + "\n"
        self.assertEqual(payload, '{\n  "en": 100,\n  "es": 98\n}\n')

    def test_real_repository_locales(self) -> None:
        root = Path(__file__).resolve().parents[1]
        doc = build_translation_status_doc(root / "locales")
        self.assertEqual(doc["en"], 100)
        for name in ("ar", "bn", "de", "es", "fr", "ja", "zh"):
            self.assertIn(name, doc)
        for value in doc.values():
            self.assertIsInstance(value, int)
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100)


if __name__ == "__main__":
    unittest.main()
