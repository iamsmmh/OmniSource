#!/usr/bin/env python3
"""Enrich and normalize app metadata (``data/enriched_apps.json``).

Offline normalization of names, descriptions, categories, URLs and
subtitles. Advisory output: the pipeline keeps serving raw upstream
metadata until enriched values are promoted into ``catalog.json``.

Usage
-----
    python3 scripts/enrich_metadata.py
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

from omnisource.enrichment import enrich_apps
from omnisource.io import read_json, write_json_stable

ROOT = Path(__file__).resolve().parents[1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--feed", default=str(ROOT / "feeds" / "apps.json"))
    parser.add_argument("--out", default=str(ROOT / "data" / "enriched_apps.json"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    feed = read_json(Path(args.feed))
    apps = feed.get("apps", []) if isinstance(feed, dict) else []
    doc = enrich_apps([app for app in apps if isinstance(app, dict)])
    changed = write_json_stable(Path(args.out), doc)
    print(
        f"enrichment: {doc['count']} app(s), {doc['incomplete']} incomplete"
        f"{'' if changed else ' (unchanged)'} -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
