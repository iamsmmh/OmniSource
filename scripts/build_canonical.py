#!/usr/bin/env python3
"""Build the canonical app database (``data/canonical_apps.json``).

Merges duplicate app records from ``feeds/apps.json`` by bundle
identifier, app ID, repository URL and release URL. Content-stable:
exits without writing when nothing changed.

Usage
-----
    python3 scripts/build_canonical.py
    python3 scripts/build_canonical.py --report  # print duplicate groups only
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

from omnisource.canonical import build_canonical, find_duplicates
from omnisource.io import read_json, write_json_stable

ROOT = Path(__file__).resolve().parents[1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--feed", default=str(ROOT / "feeds" / "apps.json"))
    parser.add_argument("--out", default=str(ROOT / "data" / "canonical_apps.json"))
    parser.add_argument("--report", action="store_true", help="print duplicate groups, write nothing")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    feed = read_json(Path(args.feed))
    apps = feed.get("apps", []) if isinstance(feed, dict) else []
    records = [dict(app, slug=app.get("slug", "")) for app in apps if isinstance(app, dict)]
    if args.report:
        for dupe in find_duplicates(records):
            print(f"{dupe['count']}x {dupe['key']} :: {', '.join(dupe['names'][:5])}")
        return 0
    doc = build_canonical(records)
    changed = write_json_stable(Path(args.out), doc)
    print(
        f"canonical: {doc['count']} canonical app(s) from {doc['inputRecords']} record(s) "
        f"({doc['mergedDuplicates']} merged){'' if changed else ' (unchanged)'} -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
