#!/usr/bin/env python3
"""Merge the modular feeds in feeds/ into a single unified apps.json.

``feeds/`` is the single source of truth for distribution. Every app ships its
own feed at ``feeds/<slug>.json``; this script reads those per-app feeds and
reassembles ``feeds/apps.json``, the unified master feed. The Pages builder
publishes these canonical files at both organized and historical flat URLs.

The per-app feeds win: whatever they contain is what the master feed contains.
Source metadata (name, identifier, tintColor, icon, website) is taken from
``catalog.json`` when present, and derived from the first feed otherwise, so
the merge never depends on a network call or a prior pipeline run.

This is a subset of the main build stage, factored out so the merge can run as
a standalone safety net on every change to ``feeds/``. Output is byte-identical
to what the full pipeline produces.

Usage
-----
    python3 scripts/merge_feeds.py            # rebuild feeds/apps.json
    python3 scripts/merge_feeds.py --check    # fail if it is out of date
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_SCRIPTS = str(Path(__file__).resolve().parent)
if _SCRIPTS in sys.path:
    sys.path.remove(_SCRIPTS)
_SRC = str(Path(__file__).resolve().parents[1] / "src")
if _SRC in sys.path:
    sys.path.remove(_SRC)
sys.path.insert(0, _SRC)

from omnisource.constants import ALTSTORE_NON_FEED
from omnisource.io import atomic_write_text, read_json

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPO_ROOT / "catalog.json"
FEEDS_DIR = REPO_ROOT / "feeds"
MASTER_NAME = "apps.json"
# Pipeline state, health snapshots, badges and derived intelligence documents
# are not distributable feeds. Shared with the pipeline so the merge can never
# mistake an intelligence document for a per-app feed.
NON_FEED_FILES = ALTSTORE_NON_FEED


def envelope_from_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    source = catalog.get("source", {})
    base = str(source.get("baseURL", "")).rstrip("/")
    if not base:
        raise SystemExit("merge: catalog.json source.baseURL is required")
    return {
        "name": str(source.get("name", "OmniSource")),
        "identifier": str(source.get("identifier", "com.omnisource")),
        "apiVersion": "v2",
        "subtitle": str(source.get("subtitle", "")),
        "description": str(source.get("description", "")),
        "iconURL": f"{base}/assets/{source.get('icon', 'OmniSource.png')}",
        "bannerURL": f"{base}/assets/{source.get('banner', 'OmniSource.png')}",
        "tintColor": str(source.get("tintColor", "5B5BD6")).lstrip("#"),
        "website": f"{base}/",
        "sourceURL": f"{base}/apps.json",
    }


def envelope_from_feed(feed: dict[str, Any]) -> dict[str, Any]:
    """Fallback envelope derived from a per-app feed when catalog.json is absent."""
    keep = (
        "name",
        "identifier",
        "apiVersion",
        "subtitle",
        "description",
        "iconURL",
        "bannerURL",
        "tintColor",
        "website",
        "sourceURL",
    )
    envelope = {key: feed[key] for key in keep if key in feed}
    # A per-app feed's sourceURL points at its own slug file; reset to the master.
    envelope["sourceURL"] = envelope.get("sourceURL", "").rsplit("/", 1)[0] + f"/{MASTER_NAME}"
    return envelope


def per_app_feeds() -> list[Path]:
    feeds = sorted(p for p in FEEDS_DIR.glob("*.json") if p.name not in NON_FEED_FILES and p.name != MASTER_NAME)
    if not feeds:
        raise SystemExit("merge: no per-app feeds found in feeds/")
    return feeds


def gather_apps() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    feeds = per_app_feeds()

    catalog = read_json(CATALOG_PATH) if CATALOG_PATH.exists() else None
    envelope = envelope_from_catalog(catalog) if isinstance(catalog, dict) else None

    apps: list[dict[str, Any]] = []
    for path in feeds:
        feed = read_json(path)
        if not isinstance(feed, dict):
            raise SystemExit(f"merge: {path.name} is not a JSON object")
        entries = feed.get("apps")
        if not isinstance(entries, list) or len(entries) != 1 or not isinstance(entries[0], dict):
            raise SystemExit(f"merge: {path.name} must contain exactly one app entry")
        app = entries[0]
        if not app.get("name") or not app.get("bundleIdentifier"):
            raise SystemExit(f"merge: {path.name} app entry is missing name/bundleIdentifier")
        if envelope is None:
            envelope = envelope_from_feed(feed)
        apps.append(app)

    # Match the full pipeline's deterministic ordering (case-insensitive name).
    apps.sort(key=lambda app: str(app.get("name", "")).lower())
    return envelope, apps


def build_master() -> dict[str, Any]:
    envelope, apps = gather_apps()
    master = dict(envelope)
    master["apps"] = apps
    existing_news = []
    if (FEEDS_DIR / MASTER_NAME).exists():
        existing_doc = read_json(FEEDS_DIR / MASTER_NAME)
        if isinstance(existing_doc, dict) and isinstance(existing_doc.get("news"), list):
            existing_news = existing_doc["news"]
    master["news"] = existing_news
    return master


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail instead of writing when outputs are stale")
    args = parser.parse_args(argv)

    master = build_master()
    payload = json.dumps(master, indent=2, ensure_ascii=False) + "\n"
    target = FEEDS_DIR / MASTER_NAME
    current = target.read_text(encoding="utf-8") if target.exists() else None
    if current != payload:
        if args.check:
            print(f"merge: out of date: {target.relative_to(REPO_ROOT)} - run scripts/merge_feeds.py")
            return 1
        atomic_write_text(target, payload)
        print(f"merge: wrote {target.relative_to(REPO_ROOT)}")
    print(f"merge: apps.json unified from {len(master['apps'])} modular feed(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
