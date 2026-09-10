"""Invariants for the static website shell (Liquid Glass + GH Pages).

The repository root holds the site *sources* (index.html, install/, js/,
feeds/, apps/, …) and ``scripts/build_site.py`` assembles the deployable
site into ``_site/``, which ``sync.yml`` publishes via GitHub Actions
deployment. These invariants protect the pieces the builder and the
deployed site depend on.
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SRC = ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


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

    def test_source_feed_is_a_link_and_stacks_on_small_screens(self) -> None:
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        install = (ROOT / "install" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "assets" / "design-system" / "components.css").read_text(encoding="utf-8")
        self.assertIn('id="sourceUrlLink" href="https://iamsmmh.github.io/OmniSource/apps.json"', home)
        self.assertIn('id="installFeedUrlLink" href="https://iamsmmh.github.io/OmniSource/apps.json"', install)
        self.assertIn("@media (max-width: 620px)", css)
        self.assertIn("flex-direction: column", css)
        self.assertIn("overflow-wrap: anywhere", css)

    def test_service_worker_version(self) -> None:
        sw = (ROOT / "sw.js").read_text(encoding="utf-8")
        self.assertIn("omnisource-v6", sw)
        # The shell precaches the lightweight WebP logo; the PNG stays for
        # favicons, feed iconURLs and non-WebP fallbacks only.
        self.assertIn("'./assets/OmniSource.webp'", sw)
        self.assertNotIn("'./assets/OmniSource.png'", sw)

    def test_homepage_stat_markers(self) -> None:
        # The site builder (site._inject_homepage_stats) rewrites these
        # markers in the deployed _site/index.html copy and fails loudly
        # when one disappears — keep them stable.
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

    def test_pages_deploys_from_site_artifact(self) -> None:
        # Single-publisher invariant: Pages deploys the _site/ artifact that
        # sync.yml assembles — never the repository root. A Jekyll config
        # must not come back, or a managed branch build would serve the raw
        # root (without the flat feed URLs) and fight the Actions deploy.
        self.assertFalse(
            (ROOT / "_config.yml").exists(),
            "_config.yml must stay deleted: Pages deploys _site/ via GitHub Actions, not a Jekyll branch build",
        )
        sync = (ROOT / ".github" / "workflows" / "sync.yml").read_text(encoding="utf-8")
        self.assertIn("scripts/build_site.py", sync)
        self.assertIn("actions/upload-pages-artifact", sync)
        self.assertIn("actions/deploy-pages", sync)

    def test_repo_root_carries_no_generated_flat_copies(self) -> None:
        # The flat subscriber URLs (/<feed>.json, /<feed>.xml, badges) are
        # assembled into _site/ at deploy time; committing them at the root
        # again would resurrect the ~70 duplicate files this layout removed.
        # catalog.json is the hand-edited source of truth, not a copy.
        for path in sorted(ROOT.glob("*.json")):
            self.assertEqual(path.name, "catalog.json", f"unexpected root JSON: {path.name}")
        self.assertEqual(list(ROOT.glob("*.xml")), [], "no generated XML belongs at the repository root")
        self.assertFalse((ROOT / "robots.txt").exists(), "robots.txt is generated into _site/, not committed")

    def test_site_build_publishes_flat_subscriber_urls(self) -> None:
        # /apps.json is the installable source URL for existing clients; the
        # builder must publish it (and every other flat URL) byte-identical
        # to feeds/, plus sitemap/robots and live homepage statistics.
        from omnisource.site import build_site

        tmp = Path(tempfile.mkdtemp(prefix="omnisource-site-test-", dir=ROOT))
        try:
            summary = build_site(tmp)
            self.assertGreater(summary["flat_files"], 0)
            for pattern in ("*.json", "*.xml"):
                for canonical in sorted((ROOT / "feeds").glob(pattern)):
                    if canonical.name == "state.json":
                        continue
                    flat = tmp / canonical.name
                    self.assertTrue(flat.is_file(), f"flat URL missing from the built site: {canonical.name}")
                    self.assertEqual(
                        flat.read_bytes(),
                        canonical.read_bytes(),
                        f"flat URL diverged from feeds/: {canonical.name}",
                    )
            self.assertTrue((tmp / "catalog.json").is_file())
            self.assertTrue((tmp / "sitemap.xml").is_file())
            self.assertTrue((tmp / "robots.txt").is_file())
            self.assertTrue((tmp / "feeds" / "apps.json").is_file())
            self.assertTrue((tmp / "api" / "apps.json").is_file())
            home = (tmp / "index.html").read_text(encoding="utf-8")
            self.assertNotIn('id="statApps" data-count>0<', home)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_nav_never_pushes_controls_off_page(self) -> None:
        # The header row is wider than the 1200px shell on desktops (11
        # links + controls); the nav links must absorb the squeeze so the
        # controls (search/theme/install/language) always stay on-page.
        css = (ROOT / "assets" / "design-system" / "components.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.nav-links \{[^}]*flex: 0 1 auto;[^}]*min-width: 0;")
        self.assertRegex(css, r"\.nav-links a \{[^}]*text-overflow: ellipsis;")
        self.assertRegex(css, r"\.nav-controls \{[^}]*flex: none;")
        self.assertIn("@media (max-width: 560px)", css)
        self.assertIn("@media (max-width: 430px)", css)

    def test_language_selector_has_a_home_at_every_breakpoint(self) -> None:
        # features.js renders the language switcher in the header row AND in
        # the hamburger menu; the CSS swap keeps exactly one visible so it
        # can never overflow the row (it used to sit past the page edge).
        features = (ROOT / "js" / "features.js").read_text(encoding="utf-8")
        self.assertIn("nav-lang", features)
        self.assertIn(".nav-controls .language-selector { display: none; }", features)
        self.assertIn(".nav-links .nav-lang { display: flex; }", features)
        self.assertIn("syncLanguageSelects", features)

    def test_os_search_engine_is_not_shadowed_by_features(self) -> None:
        # js/core.js publishes the search *engine* as OS.Search and js/site.js
        # plus core.js call OS.Search.load()/search()/highlight()/.docs.
        # js/features.js runs last, so when it also assigned OS.Search it
        # replaced the engine with its operator UI and every engine call threw
        # "OS.Search.load is not a function" (the /search/ page died). The UI
        # now lives at OS.SearchUI; keep the namespaces disjoint.
        core = (ROOT / "js" / "core.js").read_text(encoding="utf-8")
        features = (ROOT / "js" / "features.js").read_text(encoding="utf-8")
        site = (ROOT / "js" / "site.js").read_text(encoding="utf-8")

        self.assertIn("OS.Search = Search;", core, "core.js must publish the search engine")
        self.assertNotIn("OS.Search =", features, "features.js must not reassign OS.Search")
        self.assertIn("OS.SearchUI = SearchUI;", features, "features.js must export its UI as OS.SearchUI")

        engine_members = {"load", "search", "highlight", "fetchTrending", "score", "popular", "topCategories", "docs"}
        for name in sorted(engine_members):
            self.assertRegex(core, rf"\b{name}: (function|\[)", f"core.js search engine lost {name}")

        # Every OS.Search.<member> call site must resolve on the engine.
        called = {m.group(1) for m in re.finditer(r"OS\.Search\.([A-Za-z_$][\w$]*)", core + features + site)}
        self.assertTrue(called, "expected OS.Search call sites in the client scripts")
        for name in sorted(called):
            self.assertIn(name, engine_members, f"OS.Search.{name} is not part of the core engine")

        # Every OS.SearchUI.<member> call site must resolve on the UI module.
        ui_called = {m.group(1) for m in re.finditer(r"OS\.SearchUI\.([A-Za-z_$][\w$]*)", core + features + site)}
        for name in sorted(ui_called):
            self.assertRegex(features, rf"\b{name}\(\) \{{", f"OS.SearchUI.{name} is not defined in features.js")

    def test_collections_pages_extend_os_collections_after_features_init(self) -> None:
        # features.js only assigns OS.Collections from its DOMContentLoaded
        # init, but these two pages load core.js/features.js synchronously and
        # then extend OS.Collections from an inline <script>. Running that at
        # parse time threw "Cannot set properties of undefined (setting
        # 'showCreateModal')", which aborted the rest of the block — so the
        # catalog fetch never ran and the page rendered empty. The inline
        # block must therefore defer to DOMContentLoaded.
        for rel in ("collections/index.html", "collections/collection.html"):
            html = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("OS.Collections.", html, f"{rel}: expected page-specific Collections extensions")
            body = html.split("<script>", 1)[1].split("</script>", 1)[0]
            self.assertIn("document.addEventListener('DOMContentLoaded'", body, f"{rel}: inline block is not deferred")
            # The guard must precede the first assignment, not follow it.
            self.assertLess(
                body.index("document.addEventListener('DOMContentLoaded'"),
                body.index("OS.Collections."),
                f"{rel}: OS.Collections is touched before the DOMContentLoaded guard",
            )
            self.assertIn("if (!window.OS || !OS.Collections)", body, f"{rel}: missing OS.Collections guard")

    def test_client_scripts_reference_only_shipped_assets(self) -> None:
        # Only the WebP twins plus OmniSource.png are deployed (see
        # site._deployable_asset), so a literal asset reference that resolves
        # to anything else is a guaranteed 404 in production. This catches the
        # 'assets/unknown.png' icon fallback, which never shipped, and the
        # OS.asset('../assets/...') values that the helper turned into
        # 'assets/../assets/...' because it only strips a leading 'assets/'.
        from omnisource.site import _deployable_asset

        asset_arg = re.compile(r"""OS\.asset\(\s*['"]([^'"${}]+?)['"]""")
        html_ref = re.compile(
            r"""(?:href|src|srcset)\s*=\s*["']((?:\.\./)*assets/[^"'${}]+?\.(?:png|webp|svg|jpg|ico))["']"""
        )
        checked = 0

        def resolve_asset(arg: str) -> Path:
            """Mirror js/core.js asset(): strip one leading 'assets/', re-add it."""
            return ROOT / "assets" / re.sub(r"^assets/", "", arg)

        for source in [ROOT / "js" / "core.js", ROOT / "js" / "features.js", ROOT / "js" / "site.js"]:
            for arg in asset_arg.findall(source.read_text(encoding="utf-8")):
                target = resolve_asset(arg)
                checked += 1
                where = f"{source.name}: OS.asset({arg!r})"
                self.assertFalse(arg.startswith(("../", "/")), f"{where} must not be path-prefixed")
                self.assertTrue(target.is_file(), f"{where} resolves to a missing file")
                self.assertTrue(_deployable_asset(target), f"{where} is not deployed to _site/")

        # Static markup resolves ../assets/ against the page's own directory.
        for page in sorted(ROOT.rglob("*.html")):
            if "_site" in page.parts:
                continue
            for raw in html_ref.findall(page.read_text(encoding="utf-8")):
                target = (page.parent / raw).resolve()
                checked += 1
                self.assertTrue(target.is_file(), f"{page.relative_to(ROOT)}: missing asset {raw}")
                self.assertTrue(_deployable_asset(target), f"{page.relative_to(ROOT)}: {raw} is not deployed to _site/")

        self.assertGreater(checked, 10, "expected the asset-reference scan to find the icon literals")

    def test_exported_favorites_page_links_real_stylesheets(self) -> None:
        # getFavoritesPageHTML() writes a standalone document; it used to link
        # css/site.css and css/design-system.css, which have never existed in
        # this repository, so every exported page came out unstyled.
        features = (ROOT / "js" / "features.js").read_text(encoding="utf-8")
        self.assertNotIn("css/site.css", features)
        self.assertNotIn("css/design-system.css", features)
        for sheet in ("tokens.css", "utilities.css", "animations.css", "components.css"):
            self.assertIn(f"design-system/{sheet}", features, f"exported favorites page is missing {sheet}")
            self.assertTrue((ROOT / "assets" / "design-system" / sheet).is_file(), f"{sheet} is not a real stylesheet")

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
