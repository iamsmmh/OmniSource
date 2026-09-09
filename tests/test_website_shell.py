"""Invariants for the static website shell (Liquid Glass + GH Pages root).

The repository root *is* the site: hand-maintained pages live at the root
(index.html, install/, js/, …) and GitHub's Jekyll-managed Pages build
publishes them directly (see _config.yml). These invariants protect the
pieces the pipeline and the Jekyll build depend on.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestWebsiteShell(unittest.TestCase):
    def test_core_resolves_root_without_current_script(self) -> None:
        core = (ROOT / "js" / "core.js").read_text(encoding="utf-8")
        self.assertIn("function detectRoot()", core)
        self.assertIn("document.getElementsByTagName('script')", core)
        self.assertIn("function asset(name)", core)
        self.assertIn("asset: asset", core)
        self.assertIn("setupMobileNav()", core)
        self.assertIn("OS.closeNav", core)

    def test_site_uses_asset_helper_and_compare_query(self) -> None:
        site = (ROOT / "js" / "site.js").read_text(encoding="utf-8")
        self.assertIn("OS.asset(", site)
        self.assertIn("?left=", site)
        self.assertIn("&right=", site)
        self.assertNotIn("#/' + Compare.left", site)

    def test_install_page_has_title(self) -> None:
        html = (ROOT / "install" / "index.html").read_text(encoding="utf-8")
        self.assertIn("<title>Installation Center — OmniSource</title>", html)
        self.assertIn('content="#e8eef8"', html)

    def test_service_worker_version(self) -> None:
        sw = (ROOT / "sw.js").read_text(encoding="utf-8")
        self.assertIn("omnisource-v6", sw)
        # The shell precaches the lightweight WebP logo; the PNG stays for
        # favicons, feed iconURLs and non-WebP fallbacks only.
        self.assertIn("'./assets/OmniSource.webp'", sw)
        self.assertNotIn("'./assets/OmniSource.png'", sw)

    def test_homepage_stat_markers(self) -> None:
        # The pipeline (site._inject_homepage_stats) rewrites these markers
        # in place and fails loudly when one disappears — keep them stable.
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        for marker in (
            'id="statApps" data-count>',
            'id="statSources" data-count>',
            'id="statOnline" data-count>',
            'id="statVerified" data-count>',
            'id="healthLabel">',
            'id="statSyncLabel"',
        ):
            self.assertIn(marker, home, f"home page stat marker missing: {marker}")
        # The committed home page carries the real values from the last build,
        # not the 0 placeholders (no-JS visitors and crawlers read these).
        self.assertNotIn('id="statApps" data-count>0<', home)

    def test_jekyll_excludes_cover_repo_internals(self) -> None:
        # If an excluded directory comes back into the Jekyll-managed build,
        # the public site would start serving repository internals.
        config = (ROOT / "_config.yml").read_text(encoding="utf-8")
        for entry in (
            "scripts",
            "src",
            "docs",
            "tests",
            "schemas",
            "config",
            "sdk",
            "feeds/state.json",
            "README.md",
            "Makefile",
        ):
            self.assertRegex(config, rf"(?m)^\s*- {re.escape(entry)}\s*$", f"_config.yml exclude missing: {entry}")

    def test_flat_apps_json_matches_canonical_feed(self) -> None:
        # /apps.json is the installable source URL for existing clients; it
        # must stay byte-identical to feeds/apps.json in the committed tree.
        flat = ROOT / "apps.json"
        canonical = ROOT / "feeds" / "apps.json"
        self.assertTrue(flat.is_file(), "flat apps.json missing at the repository root")
        self.assertEqual(flat.read_bytes(), canonical.read_bytes())

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
