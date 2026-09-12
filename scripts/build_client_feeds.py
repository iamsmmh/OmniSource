#!/usr/bin/env python3
"""Render per-client distribution feeds (``feeds/clients/<client>.json``).

Builds the AltStore / SideStore / Feather / ESign / LiveContainer
variants from ``feeds/apps.json`` and validates each one as AltStore v2
before writing. Invalid output is never published.

Usage
-----
    python3 scripts/build_client_feeds.py
    python3 scripts/build_client_feeds.py --check  # fail if any variant is stale
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = str(Path(__file__).resolve().parent)
if _SCRIPTS in sys.path:
    sys.path.remove(_SCRIPTS)
_SRC = str(Path(__file__).resolve().parents[1] / "src")
if _SRC in sys.path:
    sys.path.remove(_SRC)
sys.path.insert(0, _SRC)

from omnisource.feeds.clients import CLIENTS, render_client_feed, render_collection_feed, render_single_app_feed
from omnisource.io import dumps_pretty, read_json
from omnisource.validation import validate_feed

ROOT = Path(__file__).resolve().parents[1]
CLIENTS_DIR = ROOT / "feeds" / "clients"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--feed", default=str(ROOT / "feeds" / "apps.json"))
    parser.add_argument("--out-dir", default=str(CLIENTS_DIR))
    parser.add_argument("--single-dir", default=str(ROOT / "feeds" / "single"))
    parser.add_argument("--collection-dir", default=str(ROOT / "feeds" / "collections"))
    parser.add_argument("--collections", default=str(ROOT / "feeds" / "collections.json"))
    parser.add_argument("--check", action="store_true", help="fail if any variant differs from disk")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    envelope = read_json(Path(args.feed))
    if not isinstance(envelope, dict):
        print(f"client_feeds: cannot read {args.feed}")
        return 1
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []
    for client in CLIENTS:
        feed = render_client_feed(envelope, client)
        report = validate_feed(out_dir / f"{client}.json", feed, root=ROOT)
        if report.errors:
            print(f"client_feeds: {client}: INVALID ({'; '.join(report.errors[:3])})")
            return 1
        payload = dumps_pretty(feed)
        target = out_dir / f"{client}.json"
        if args.check:
            if not target.is_file() or target.read_text(encoding="utf-8") != payload:
                stale.append(client)
            continue
        if not target.is_file() or target.read_text(encoding="utf-8") != payload:
            target.write_text(payload, encoding="utf-8")
            print(f"client_feeds: {client}: {len(feed['apps'])} app(s) -> {target}")
        else:
            print(f"client_feeds: {client}: {len(feed['apps'])} app(s) (unchanged)")
    # Single-app feeds are stable, explicit opt-in sources for bundle-ID
    # alternatives. Collection feeds are generated from committed appSlugs;
    # neither surface is influenced by user activity.
    single_dir = Path(args.single_dir)
    collection_dir = Path(args.collection_dir)
    single_dir.mkdir(parents=True, exist_ok=True)
    collection_dir.mkdir(parents=True, exist_ok=True)
    all_apps = [item for item in envelope.get("apps", []) if isinstance(item, dict)]
    for app in all_apps:
        app_id = str(app.get("id") or app.get("slug") or (app.get("omnisource") or {}).get("slug", ""))
        if not app_id:
            continue
        target = single_dir / f"{app_id}.json"
        feed = render_single_app_feed(envelope, app_id)
        payload = dumps_pretty(feed)
        if args.check:
            if not target.is_file() or target.read_text(encoding="utf-8") != payload:
                stale.append(f"single/{app_id}")
        elif not target.is_file() or target.read_text(encoding="utf-8") != payload:
            target.write_text(payload, encoding="utf-8")
    collection_doc = read_json(Path(args.collections))
    collections = collection_doc.get("collections", []) if isinstance(collection_doc, dict) else []
    for collection in collections if isinstance(collections, list) else []:
        if not isinstance(collection, dict) or not collection.get("slug"):
            continue
        slug = str(collection["slug"])
        target = collection_dir / f"{slug}.json"
        feed = render_collection_feed(envelope, collection)
        payload = dumps_pretty(feed)
        if args.check:
            if not target.is_file() or target.read_text(encoding="utf-8") != payload:
                stale.append(f"collections/{slug}")
        elif not target.is_file() or target.read_text(encoding="utf-8") != payload:
            target.write_text(payload, encoding="utf-8")
    if stale:
        print(f"client_feeds: stale variant(s): {', '.join(stale)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
