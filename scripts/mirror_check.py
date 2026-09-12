#!/usr/bin/env python3
"""Evaluate mirror failover readiness (``data/mirror_status.json``).

Probes the configured mirror roots (when reachable) and writes the
per-app protection snapshot. Offline-safe: with ``--offline`` the
registry alone decides coverage.

Usage
-----
    python3 scripts/mirror_check.py --offline
    python3 scripts/mirror_check.py
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

from omnisource.io import read_json, write_json_stable
from omnisource.mirrors import build_status, default_registry
from omnisource.probes import probe_url

ROOT = Path(__file__).resolve().parents[1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--registry", default=str(ROOT / "data" / "mirrors.json"))
    parser.add_argument("--feed", default=str(ROOT / "feeds" / "apps.json"))
    parser.add_argument("--out", default=str(ROOT / "data" / "mirror_status.json"))
    parser.add_argument("--offline", action="store_true", help="skip live probing of mirror roots")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    registry = read_json(Path(args.registry))
    if not isinstance(registry, dict):
        registry = default_registry()
    feed = read_json(Path(args.feed))
    apps = feed.get("apps", []) if isinstance(feed, dict) else []
    slugs = [
        str(app.get("slug") or app.get("id") or app.get("bundleIdentifier") or "")
        for app in apps
        if isinstance(app, dict)
    ]
    health: dict[str, bool] = {}
    if not args.offline:
        roots = set()
        for entry in registry.get("mirrors", []) or []:
            if isinstance(entry, dict):
                template = str(entry.get("urlTemplate") or entry.get("url") or "")
                if template.startswith("https://"):
                    roots.add(template.split("{")[0].rstrip("/") or template)
        for root in sorted(roots):
            health[root] = probe_url(root).get("ok", False)
    doc = build_status(registry, [slug for slug in slugs if slug], health=health)
    changed = write_json_stable(Path(args.out), doc)
    print(f"mirrors: {doc['protected']}/{doc['appCount']} protected{'' if changed else ' (unchanged)'} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
