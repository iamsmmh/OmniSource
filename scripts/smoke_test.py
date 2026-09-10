#!/usr/bin/env python3
"""End-to-end smoke test for the assembled static site.

Builds the deployable site into a temporary directory (exactly what
``sync.yml`` publishes), serves it over local HTTP, then verifies the
contract the website and feed clients depend on:

* every page and feed URL returns HTTP 200;
* the live catalog data is reachable at all three URL families
  (flat ``/apps.json``, organized ``/feeds/apps.json``, API ``/api/apps.json``);
* each page carries the markers and ``#id`` elements its renderer needs;
* the client scripts are syntactically valid JavaScript (when ``node``
  is available);

Usage
-----
    python3 scripts/smoke_test.py            # build + serve + verify
    python3 scripts/smoke_test.py --no-build # verify an existing _site/
"""

from __future__ import annotations

import argparse
import http.server
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SITE = ROOT / "_site"

# (path, substring that must be present in the 200 response)
PAGES: list[tuple[str, str]] = [
    ("/", 'id="appsGrid"'),
    ("/compare/", 'id="compareForm"'),
    ("/status/", 'id="stTable"'),
    ("/analytics/", 'id="anKpis"'),
    ("/install/", 'id="installClients"'),
    ("/search/", 'id="searchPageInput"'),
    ("/collections/", 'id="collections-content"'),
    ("/favorites/", 'id="favorites-content"'),
    ("/apps/ytlite/", 'class="app-page"'),
    ("/manifest.webmanifest", '"name": "OmniSource'),
    ("/sw.js", "omnisource-v6"),
    ("/sitemap.xml", "<urlset"),
    ("/robots.txt", "User-agent"),
]

# Feed / API URLs that must resolve (they exist at all three families).
FEEDS: list[str] = [
    "apps.json",
    "discovery.json",
    "sources.json",
    "health.json",
    "updates.json",
    "analytics.json",
    "verification.json",
    "status.json",
    "trending.json",
    "related.json",
    "reputation.json",
    "download-intelligence.json",
    "community.json",
    "install.json",
    "search-index.json",
    "compare.json",
    "feed.xml",
    "rss.xml",
]

# The subset of #ids each page's renderer actually uses (site.js loads on
# every page but boot() only calls the renderer for the current data-page,
# so a page only needs the ids that renderer touches).
PAGE_IDS: dict[str, list[str]] = {
    "index.html": [
        "appsGrid",
        "searchInput",
        "sortSelect",
        "osSelect",
        "categoryFilters",
        "statusFilters",
        "clearFilters",
        "resultCount",
        "emptyState",
        "collisionSummary",
        "updatesList",
        "updatesNote",
        "footerClients",
        "guideClients",
        "installGuide",
        "clientButtons",
        "sourceUrl",
        "statApps",
        "statSources",
        "statOnline",
        "statVerified",
        "statSyncLabel",
        "healthLabel",
        "metricsGrid",
        "statistics",
        "sourceHealth",
        "sourceGrid",
        "sourceHealthMore",
        "trendingRail",
        "recentRail",
        "featuredRail",
        "verifiedRail",
        "trending",
        "recent",
        "featured",
        "verifiedApps",
        "appDialog",
        "dialogContent",
        "qrDialog",
        "qrTitle",
        "qrText",
        "qrImage",
        "qrCopy",
        "sourceQr",
    ],
    "compare/index.html": [
        "compareForm",
        "leftSelect",
        "rightSelect",
        "pairList",
        "pairs",
        "result",
        "cmpEmpty",
        "resultGrid",
        "cmpMetaRow",
    ],
    "status/index.html": [
        "stOverview",
        "stTableWrap",
        "stSyncGrid",
        "stTable",
        "stMetaRow",
        "statusContent",
    ],
    "analytics/index.html": [
        "anKpis",
        "trendChart",
        "updateBars",
        "categoryBars",
        "verificationDonut",
        "weekLists",
        "anMetaRow",
        "analyticsContent",
    ],
    "install/index.html": [
        "installClients",
        "installAppSelect",
        "installAppCards",
        "installAppFeed",
        "installQr",
    ],
    "search/index.html": ["searchPageInput", "searchResults", "searchCount"],
}


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(_SITE), **kwargs)

    def log_message(self, *args: object) -> None:
        pass


class _Server:
    def __init__(self) -> None:
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _QuietHandler)
        self.port = int(self.httpd.server_address[1])
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self) -> _Server:
        self.thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.port}"


def fetch(url: str) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except Exception:
        return 0, b""


def ids_in(html: str) -> set[str]:
    return set(re.findall(r'id="([A-Za-z0-9_-]+)"', html))


def check_js_syntax() -> list[str]:
    node = shutil.which("node")
    if not node:
        return []
    errors = []
    for script in ("js/core.js", "js/site.js", "js/features.js"):
        result = subprocess.run(
            [node, "--check", str(ROOT / script)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            errors.append(f"{script}: {result.stderr.strip()}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-build", action="store_true", help="verify an existing _site/ without rebuilding")
    args = parser.parse_args(argv)

    failures: list[str] = []

    if not args.no_build:
        sys.path.insert(0, str(ROOT / "src"))
        from omnisource.site import build_site

        tmp = Path(tempfile.mkdtemp(prefix="omnisource-smoke-", dir=ROOT))
        try:
            build_site(tmp)
            shutil.rmtree(_SITE, ignore_errors=True)
            shutil.copytree(tmp, _SITE)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    if not (_SITE / "index.html").is_file():
        print("smoke_test: _site/index.html missing — build the site first", file=sys.stderr)
        return 2

    with _Server() as server:
        print(f"smoke_test: serving {_SITE} at {server.base}")
        checked = 0
        for path, marker in PAGES:
            status, body = fetch(server.base + path)
            checked += 1
            if status != 200:
                failures.append(f"{path}: HTTP {status}")
                continue
            text = body.decode("utf-8", "replace")
            if marker not in text:
                failures.append(f"{path}: missing marker {marker!r}")

        for name in FEEDS:
            # The /api/ mirror is JSON-only; XML feeds live at the flat and
            # organized families but not under /api/.
            families = [f"/{name}", f"/feeds/{name}"]
            if name.endswith(".json"):
                families.append(f"/api/{name}")
            for path in families:
                status, body = fetch(server.base + path)
                checked += 1
                if status != 200:
                    failures.append(f"{path}: HTTP {status}")

        # Each page's renderer must find every #id it touches; catches broken
        # selectors after edits.
        for page, wanted in PAGE_IDS.items():
            page_html = (_SITE / page).read_text(encoding="utf-8")
            present = ids_in(page_html)
            for ref in sorted(set(wanted) - present):
                failures.append(f"{page}: missing id #{ref} used by its renderer")

        # The sources.json repositories index must be human-readable now.
        sources = json.loads((_SITE / "sources.json").read_text(encoding="utf-8"))
        raw = (_SITE / "sources.json").read_text(encoding="utf-8")
        if "\n  " not in raw:
            failures.append("sources.json is not indented (still one long line)")
        if sources.get("count") != len(sources.get("sources", [])):
            failures.append("sources.json: count does not match sources[] length")

    for error in check_js_syntax():
        failures.append(error)

    print(f"smoke_test: checked {checked} URL(s), {len(PAGES)} page(s), {len(FEEDS)} feed(s) x 3 families")
    if failures:
        print(f"smoke_test: {len(failures)} failure(s):", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print("smoke_test: all checks passed ✔")
    return 0


if __name__ == "__main__":
    sys.exit(main())
