#!/usr/bin/env python3
"""Advanced app search over ``feeds/discovery.json``.

Fuzzy multi-field matching with relevance ranking, filters and sorting
— the CLI twin of the ``/api/search`` endpoint.

Usage
-----
    python3 scripts/search_apps.py "youtube"
    python3 scripts/search_apps.py "trollstore" --category Utilities --sort updated --limit 5
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

from omnisource.io import read_json
from omnisource.search import search

ROOT = Path(__file__).resolve().parents[1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", nargs="?", default="", help="search query (empty = list all)")
    parser.add_argument("--index", default=str(ROOT / "feeds" / "discovery.json"))
    parser.add_argument("--category", default="")
    parser.add_argument("--developer", default="")
    parser.add_argument("--source", default="")
    parser.add_argument("--sort", default="relevance", choices=["relevance", "name", "updated", "version"])
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--offset", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    index = read_json(Path(args.index))
    apps = index.get("apps", []) if isinstance(index, dict) else []
    result = search(
        [app for app in apps if isinstance(app, dict)],
        args.query,
        filters={"category": args.category, "developer": args.developer, "source": args.source},
        sort=args.sort,
        limit=args.limit,
        offset=args.offset,
    )
    for hit in result["results"]:
        print(f"{hit.get('_score', 0):>7.2f}  {hit.get('name', '?')}  ({hit.get('bundleIdentifier', '?')})")
    print(f"-- {result['total']} match(es), showing {len(result['results'])} (offset {result['offset']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
