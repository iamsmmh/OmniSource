"""Static site assembler for GitHub Pages.

Builds the complete deployable site into ``_site/`` (default) from the
organized source directories. The published site exposes every generated
artifact at three URL families so existing subscribers and future API
consumers both keep working:

* organized   ``/feeds/<file>``           — canonical generated location
* flat        ``/<file>``                 — historical subscriber URLs
* API         ``/api/<file>``             — machine-readable endpoints
* app pages   ``/apps/<slug>/``           — static detail pages

On top of the copy, the builder adds the pieces that make the site a
first-class web app: ``sitemap.xml`` (every page, regenerated each build),
``robots.txt``, gzip copies of the JSON API documents (``.json.gz``) for
consumers that want the smallest payload, and minified copies of the
design-system stylesheets (comments/blank lines stripped — no structural
rewriting, so the source of truth stays readable).

GitHub Pages itself serves the uncompressed originals; the ``.gz`` twins
are for API consumers who can request them explicitly.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "_site"

# Files published under both the flat root and /api/ (the machine API surface).
# NOTE: the hand-maintained catalog.json is published only at /catalog.json;
# /api/catalog.json is the auto-generated discovery index (see docs/API.md).
API_DOCUMENTS = {
    "apps.json": "The unified AltStore Source v2 feed (the installable source URL).",
    "discovery.json": "Searchable discovery catalog, generated every build. Also exposed as api/catalog.json.",
    "sources.json": "Source index: upstreams, publisher, clients and feed metadata.",
    "verification.json": "Trust levels and checks per app.",
    "status.json": "Source health board: reachability, latency, update age.",
    "duplicates.json": "Duplicate groups and recommended source per group.",
    "analytics.json": "Repository-derived metrics: totals, weekly changes, trends.",
    "updates.json": "Release timeline for the website.",
    "health.json": "Per-app download health and staleness annotations.",
    "trending.json": "Trending apps, rising apps, recently updated.",
    "related.json": "Per-app relationship graph (bundle, category, developer, tags).",
    "reputation.json": "Source reputation (TRUSTED / RELIABLE / AVERAGE / EXPERIMENTAL).",
    "download-intelligence.json": "Per-app historical availability, latency, mirror count.",
    "community.json": "Popular, recently added, rising and requested apps.",
    "install.json": "Install cards for every app and the master feed.",
    "search-index.json": "Fuse.js-compatible search index.",
    "compare.json": "Side-by-side comparison matrix.",
    "screenshots.json": "Screenshot catalog + mirror URLs + WebP thumbnails.",
}

# Hand-maintained website sections (besides the home page), in sitemap order.
SITE_PAGES = (
    ("/compare/", 0.8, "weekly"),
    ("/status/", 0.6, "daily"),
    ("/analytics/", 0.5, "weekly"),
    ("/install/", 0.7, "weekly"),
    ("/search/", 0.7, "weekly"),
)


def _api_manifest(base_url: str, generated_at: str) -> dict[str, Any]:
    endpoints = [
        {"path": f"/api/{name}", "description": description, "format": "json"}
        for name, description in sorted(API_DOCUMENTS.items())
    ]
    discovery = next(item["description"] for item in endpoints if item["path"] == "/api/discovery.json")
    endpoints.append(
        {
            "path": "/api/catalog.json",
            "description": f"Alias of /api/discovery.json. {discovery}",
            "format": "json",
        }
    )
    return {
        "name": "OmniSource API",
        "version": "1",
        "baseURL": base_url.rstrip("/"),
        "generatedAt": generated_at,
        "endpoints": sorted(endpoints, key=lambda item: item["path"]),
        "docs": "https://github.com/iamsmmh/OmniSource/blob/main/docs/API.md",
    }


def _base_url_from_catalog(root: Path) -> str:
    try:
        raw = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
        return str(raw.get("source", {}).get("baseURL", ""))
    except (OSError, ValueError):
        return "https://iamsmmh.github.io/OmniSource"


def _app_slugs(root: Path) -> list[str]:
    apps_dir = root / "apps"
    if not apps_dir.is_dir():
        return []
    return sorted(p.name for p in apps_dir.iterdir() if p.is_dir() and (p / "index.html").is_file())


def _sitemap(base_url: str, slugs: list[str], today: str) -> str:
    base = base_url.rstrip("/")
    urls = [(f"{base}/", "1.0", "daily")]
    for path, priority, changefreq in SITE_PAGES:
        urls.append((f"{base}{path}", str(priority), changefreq))
    for slug in slugs:
        urls.append((f"{base}/apps/{slug}/", "0.9", "weekly"))

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, priority, changefreq in urls:
        lines += [
            "  <url>",
            f"    <loc>{loc}</loc>",
            f"    <lastmod>{today}</lastmod>",
            f"    <changefreq>{changefreq}</changefreq>",
            f"    <priority>{priority}</priority>",
            "  </url>",
        ]
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def _robots(base_url: str) -> str:
    base = base_url.rstrip("/")
    return (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {base}/sitemap.xml\n"
    )


def _minify_css(text: str) -> str:
    """Conservative CSS minification: drop comments and blank lines only.

    No token rewriting — the result stays diffable against the source and
    cannot change selector specificity or cascade order.
    """
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line.strip()).strip() + "\n"


def _write_gzip(path: Path) -> Path | None:
    """Write a deterministic gzip copy next to ``path`` (``.json.gz``)."""
    if not path.exists():
        Path(str(path) + ".gz").unlink(missing_ok=True)
        return None
    gz_path = Path(str(path) + ".gz")
    with path.open("rb") as source, gzip.GzipFile(filename=str(gz_path), mode="wb", compresslevel=9, mtime=0) as target:
        shutil.copyfileobj(source, target)
    return gz_path


def _write_text(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(data, encoding="utf-8")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def build_site(output: Path, *, root: Path | None = None) -> dict[str, Any]:
    """Build a complete, deployable site without changing source files."""
    root = (root or ROOT).resolve()
    output = output.resolve()
    if output == root or root not in output.parents:
        raise ValueError("output must be a directory inside the repository")

    today = date.today().isoformat()
    base_url = _base_url_from_catalog(root)
    slugs = _app_slugs(root)

    shutil.rmtree(output, ignore_errors=True)
    shutil.copytree(root / "website", output, ignore=shutil.ignore_patterns("README.md"))
    shutil.copytree(root / "assets", output / "assets")
    shutil.copytree(root / "feeds", output / "feeds", ignore=shutil.ignore_patterns("state.json"))

    # Keep the historical flat source URLs working for existing subscribers.
    for feed in (root / "feeds").glob("*.json"):
        if feed.name != "state.json":
            shutil.copy2(feed, output / feed.name)
    for feed in (root / "feeds").glob("*.xml"):
        shutil.copy2(feed, output / feed.name)

    shutil.copy2(root / "catalog.json", output / "catalog.json")

    # Static app detail pages.
    if (root / "apps").is_dir():
        shutil.copytree(root / "apps", output / "apps")

    # Machine-readable API surface plus a small manifest.
    api_dir = output / "api"
    api_dir.mkdir(exist_ok=True)
    gz_count = 0
    for name in API_DOCUMENTS:
        source = root / "feeds" / name
        if not source.exists():
            continue
        destinations = [api_dir / name]
        if name == "discovery.json":
            # The discovery index is also the API consumer's catalog: document
            # it at both names so clients can pick either convention.
            destinations.append(api_dir / "catalog.json")
        for destination in destinations:
            shutil.copy2(source, destination)
            if _write_gzip(destination) is not None:
                gz_count += 1

    manifest = _api_manifest(base_url, today)
    manifest_path = api_dir / "index.json"
    _write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    if _write_gzip(manifest_path) is not None:
        gz_count += 1

    # SEO / discoverability.
    _write_text(output / "sitemap.xml", _sitemap(base_url, slugs, today))
    _write_text(output / "robots.txt", _robots(base_url))

    # Minify the design-system stylesheets in the deployed copy only.
    minified = 0
    css_dir = output / "assets" / "design-system"
    if css_dir.is_dir():
        for css in sorted(css_dir.glob("*.css")):
            before = css.stat().st_size
            minified_text = _minify_css(css.read_text(encoding="utf-8"))
            css.write_text(minified_text, encoding="utf-8")
            minified += before - css.stat().st_size

    (output / ".nojekyll").touch()

    return {
        "output": str(output),
        "pages": 6 + len(slugs),
        "app_pages": len(slugs),
        "gz_files": gz_count,
        "css_minified_bytes": minified,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="site output directory")
    args = parser.parse_args(argv)
    summary = build_site(args.output)
    print(
        f"Built site at {summary['output']}: {summary['pages']} pages "
        f"({summary['app_pages']} app pages), {summary['gz_files']} gz API copies, "
        f"{summary['css_minified_bytes'] // 1024} KB CSS minified, sitemap + robots written."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
