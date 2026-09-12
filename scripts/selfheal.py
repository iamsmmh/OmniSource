#!/usr/bin/env python3
"""Detect breakage and plan repairs (``data/selfheal_report.json``).

Reads the feed + health documents, detects broken downloads, missing
metadata and removed releases (via ``data/release_history.json``), and
writes repair plans. ``--apply`` additionally applies the safe fixes
(fallback-URL swaps) to a patched feed copy for review —
``data/healed_apps.json`` — never to the pipeline outputs directly.

Usage
-----
    python3 scripts/selfheal.py
    python3 scripts/selfheal.py --apply --reprobe
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

from omnisource.io import read_json, write_json, write_json_stable
from omnisource.probes import check_downloads
from omnisource.selfheal import apply_safe_fixes, build_report, detect_issues, plan_repairs

ROOT = Path(__file__).resolve().parents[1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--feed", default=str(ROOT / "feeds" / "apps.json"))
    parser.add_argument("--health", default=str(ROOT / "feeds" / "health.json"))
    parser.add_argument("--history", default=str(ROOT / "data" / "release_history.json"))
    parser.add_argument("--out", default=str(ROOT / "data" / "selfheal_report.json"))
    parser.add_argument("--apply", action="store_true", help="write data/healed_apps.json with safe fixes")
    parser.add_argument("--reprobe", action="store_true", help="re-probe downloads live before planning")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    feed = read_json(Path(args.feed))
    apps = list(feed.get("apps", [])) if isinstance(feed, dict) else []
    for app in apps:
        app.setdefault("slug", str(app.get("id") or app.get("bundleIdentifier") or ""))
    health: dict = {}
    if args.reprobe:
        probed = check_downloads(apps)
        health = {
            "apps": [
                {
                    "slug": item["id"],
                    "status": "healthy" if item["ok"] else "unavailable",
                    "error": item.get("error", ""),
                }
                for item in probed
            ]
        }
    else:
        stored = read_json(Path(args.health))
        health = stored if isinstance(stored, dict) else {}
    ledger = read_json(Path(args.history))
    removed: dict[str, list[dict]] = {}
    if isinstance(ledger, dict) and isinstance(ledger.get("apps"), dict):
        for slug, entries in ledger["apps"].items():
            gone = [entry for entry in entries if isinstance(entry, dict) and entry.get("status") == "removed"]
            if gone:
                removed[slug] = gone
    plans = plan_repairs(detect_issues(apps=apps, health=health, removed=removed))
    applied = 0
    if args.apply:
        _fixed, applied = apply_safe_fixes(apps, plans)
        write_json(Path(ROOT / "data" / "healed_apps.json"), {"count": len(_fixed), "apps": _fixed})
    report = build_report(plans, applied=applied)
    changed = write_json_stable(Path(args.out), report)
    print(
        f"selfheal: {report['issues']} issue(s), {report['autoFixable']} auto-fixable, "
        f"{applied} applied{'' if changed else ' (unchanged)'} -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
