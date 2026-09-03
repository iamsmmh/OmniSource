"""OpenAPI spec and static API snapshot tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from omnisource.api import openapi_spec
from omnisource.validation import validate_openapi


class OpenAPITests(unittest.TestCase):
    def test_required_paths(self) -> None:
        spec = openapi_spec(base_url="https://example.com/OmniSource")
        self.assertEqual(spec["openapi"], "3.1.0")
        for route in ("/apps", "/apps/{id}", "/updates", "/categories", "/repositories", "/search"):
            self.assertIn(route, spec["paths"], route)
        report = validate_openapi(Path("openapi.json"), spec, root=Path())
        self.assertEqual(report.errors, [])


if __name__ == "__main__":
    unittest.main()
