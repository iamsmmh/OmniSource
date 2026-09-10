"""Guards against the package version drifting from ``pyproject.toml``."""

from __future__ import annotations

import tomllib
from pathlib import Path
from unittest import TestCase

from omnisource import __version__

_REPO_ROOT = Path(__file__).resolve().parents[1]


class VersionDriftTests(TestCase):
    def test_package_version_matches_pyproject(self):
        pyproject = _REPO_ROOT / "pyproject.toml"
        with pyproject.open("rb") as handle:
            data = tomllib.load(handle)
        declared = data["project"]["version"]
        self.assertEqual(__version__, declared)


if __name__ == "__main__":
    import unittest

    unittest.main()
