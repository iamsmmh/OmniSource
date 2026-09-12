#!/usr/bin/env python3
"""Probe every upstream source URL and print a reachability table.

Reads ``feeds/sources.json``. Used by ``monitoring.yml``; the merged
``data/status.json`` is written by ``report_status.py``.

Usage
-----
    python3 scripts/monitoring/check_sources.py
    python3 scripts/monitoring/check_sources.py --workers 32 --timeout 8
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from omnisource.io import read_json
from omnisource.probes import check_sources

ROOT = Path(__file__).resolve().parents[2]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sources", default=str(ROOT / "feeds" / "sources.json"))
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--timeout", type=int, default=12)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    doc = read_json(Path(args.sources))
    sources = doc.get("sources", []) if isinstance(doc, dict) else []
    results = check_sources(
        [item for item in sources if isinstance(item, dict)],
        timeout=max(5, args.timeout),
        workers=max(1, args.workers),
    )
    failing = [item for item in results if not item.get("ok")]
    for item in results:
        mark = "ok " if item.get("ok") else "FAIL"
        print(f"{mark} {item['id']}  {item.get('status', 0)}  {item.get('latency_ms', '?')}ms  {item['url']}")
    print(f"check_sources: {len(results) - len(failing)}/{len(results)} reachable")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
