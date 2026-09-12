#!/usr/bin/env python3
"""Probe every app's newest download URL and print a reachability table.

Reads ``feeds/apps.json``. Used by ``monitoring.yml``; the merged
``data/status.json`` is written by ``report_status.py``.

Usage
-----
    python3 scripts/monitoring/check_downloads.py
    python3 scripts/monitoring/check_downloads.py --workers 32 --timeout 8
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from omnisource.io import read_json
from omnisource.probes import check_downloads

ROOT = Path(__file__).resolve().parents[2]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--feed", default=str(ROOT / "feeds" / "apps.json"))
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--timeout", type=int, default=12)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    doc = read_json(Path(args.feed))
    apps = doc.get("apps", []) if isinstance(doc, dict) else []
    results = check_downloads(
        [item for item in apps if isinstance(item, dict)],
        timeout=max(5, args.timeout),
        workers=max(1, args.workers),
    )
    failing = [item for item in results if not item.get("ok")]
    for item in results:
        mark = "ok " if item.get("ok") else "FAIL"
        print(f"{mark} {item['id']}  {item.get('status', 0)}  {item.get('latency_ms', '?')}ms")
    print(f"check_downloads: {len(results) - len(failing)}/{len(results)} reachable")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
