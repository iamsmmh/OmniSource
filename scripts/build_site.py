#!/usr/bin/env python3
"""Assemble the static GitHub Pages site from its organized source directories.

The builder publishes every generated artifact at three URL families so
existing subscribers and future API consumers both keep working:

* organized   ``/feeds/<file>``           — canonical generated location
* flat        ``/<file>``                 — historical subscriber URLs
* API         ``/api/<file>``             — machine-readable endpoints
* app pages   ``/apps/<slug>/``           — static detail pages

JSON API documents are also emitted as gzip-compressed copies (``.json.gz``)
for API consumers that want the smallest possible payload; GitHub Pages itself
serves the uncompressed originals. The website remains dependency-free and
loads only the documents it renders.
"""

from __future__ import annotations

import argparse
import gzip
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
    "trending.json": "Phase 1: trending apps, rising apps, recently updated.",
    "related.json": "Phase 2: per-app relationship graph (bundle, category, developer, tags).",
    "reputation.json": "Phase 6: source reputation (TRUSTED / RELIABLE / AVERAGE / EXPERIMENTAL).",
    "download-intelligence.json": "Phase 7: per-app historical availability, latency, mirror count.",
    "community.json": "Phase 13: popular, recently added, rising, requested apps.",
    "install.json": "Phase 9: install cards for every app and the master feed.",
    "search-index.json": "Phase 4: Fuse.js-compatible search index.",
    "compare.json": "Phase 5: side-by-side comparison matrix.",
    "screenshots.json": "Phase 3: screenshot catalog + mirror URLs + WebP thumbnails.",
}


def _api_manifest(base_url: str, generated_at: str) -> dict:
    endpoints = [
        {"path": f"/api/{name}", "description": description, "format": "json"}
        for name, description in sorted(API_DOCUMENTS.items())
    ]
    # Alias: clients may treat /api/catalog.json as the discovery index.
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


def build_site(output: Path) -> None:
    """Build a complete, deployable site without changing source files."""
    output = output.resolve()
    if output == ROOT or ROOT not in output.parents:
        raise ValueError("output must be a directory inside the repository")

    shutil.rmtree(output, ignore_errors=True)
    shutil.copytree(ROOT / "website", output, ignore=shutil.ignore_patterns("README.md"))
    shutil.copytree(ROOT / "assets", output / "assets")
    shutil.copytree(ROOT / "feeds", output / "feeds", ignore=shutil.ignore_patterns("state.json"))

    # Keep the historical flat source URLs working for existing subscribers.
    for feed in (ROOT / "feeds").glob("*.json"):
        if feed.name != "state.json":
            shutil.copy2(feed, output / feed.name)
    for feed in (ROOT / "feeds").glob("*.xml"):
        shutil.copy2(feed, output / feed.name)

    shutil.copy2(ROOT / "catalog.json", output / "catalog.json")

    # Static app detail pages.
    if (ROOT / "apps").is_dir():
        shutil.copytree(ROOT / "apps", output / "apps")

    # Machine-readable API surface plus a small manifest.
    api_dir = output / "api"
    api_dir.mkdir(exist_ok=True)
    base_url = _base_url_from_catalog()
    for name in API_DOCUMENTS:
        source = ROOT / "feeds" / name
        if not source.exists():
            continue
        destinations = [api_dir / name]
        if name == "discovery.json":
            # The discovery index is also the API consumer's catalog: document
            # it at both names so clients can pick either convention.
            destinations.append(api_dir / "catalog.json")
        for destination in destinations:
            shutil.copy2(source, destination)
            _write_gzip(destination)

    _atomic_json(api_dir / "index.json", _api_manifest(base_url, _today()))
    _write_gzip(api_dir / "index.json")

    (output / ".nojekyll").touch()


def _base_url_from_catalog() -> str:
    try:
        raw = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        return str(raw.get("source", {}).get("baseURL", ""))
    except (OSError, ValueError):
        return "https://iamsmmh.github.io/OmniSource"


def _today() -> str:
    from datetime import date

    return date.today().isoformat()


def _write_gzip(path: Path) -> None:
    """Write a gzip-compressed copy next to ``path`` (``.json.gz``)."""
    if not path.exists():
        Path(str(path) + ".gz").unlink(missing_ok=True)
        return
    gz_path = Path(str(path) + ".gz")
    with path.open("rb") as source, gzip.GzipFile(filename=str(gz_path), mode="wb", compresslevel=9, mtime=0) as target:
        shutil.copyfileobj(source, target)


def _atomic_json(path: Path, data: dict) -> None:
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="site output directory")
    args = parser.parse_args()
    build_site(args.output)
    print(f"Built site at {args.output.resolve()}")


if __name__ == "__main__":
    main()
