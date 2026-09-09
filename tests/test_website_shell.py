"""Invariants for the static website shell (Liquid Glass + GH Pages root)."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestWebsiteShell(unittest.TestCase):
    def test_core_resolves_root_without_current_script(self) -> None:
        core = (ROOT / "website" / "js" / "core.js").read_text(encoding="utf-8")
        self.assertIn("function detectRoot()", core)
        self.assertIn("document.getElementsByTagName('script')", core)
        self.assertIn("function asset(name)", core)
        self.assertIn("asset: asset", core)
        self.assertIn("setupMobileNav()", core)
        self.assertIn("OS.closeNav", core)

    def test_site_uses_asset_helper_and_compare_query(self) -> None:
        site = (ROOT / "website" / "js" / "site.js").read_text(encoding="utf-8")
        self.assertIn("OS.asset(", site)
        self.assertIn("?left=", site)
        self.assertIn("&right=", site)
        self.assertNotIn("#/' + Compare.left", site)

    def test_install_page_has_title(self) -> None:
        html = (ROOT / "website" / "install" / "index.html").read_text(encoding="utf-8")
        self.assertIn("<title>Installation Center — OmniSource</title>", html)
        self.assertIn('content="#e8eef8"', html)

    def test_service_worker_version(self) -> None:
        sw = (ROOT / "website" / "sw.js").read_text(encoding="utf-8")
        self.assertIn("omnisource-v5", sw)

    def test_liquid_glass_tokens(self) -> None:
        tokens = (ROOT / "assets" / "design-system" / "tokens.css").read_text(encoding="utf-8")
        self.assertIn("--glass-nav:", tokens)
        self.assertIn("--blur-liquid:", tokens)
        self.assertIn("--bg: #e8eef8", tokens)
        self.assertIn("--bg: #06060e", tokens)
        self.assertIn("--highlight-inset: inset 0 1px 0 rgba(255, 255, 255, 0.16)", tokens)

    def test_liquid_glass_nav(self) -> None:
        css = (ROOT / "assets" / "design-system" / "components.css").read_text(encoding="utf-8")
        self.assertIn("LIQUID GLASS layer", css)
        self.assertIn(".nav-toggle", css)
        self.assertIn("@media (max-width: 1100px)", css)
        self.assertIn("var(--glass-nav)", css)


if __name__ == "__main__":
    unittest.main()
