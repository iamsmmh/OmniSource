#!/usr/bin/env python3
"""Build analytics windows (``data/analytics_rollup.json``).

Rolls ``feeds/analytics.json`` history (+ the monitoring ledger when
present) into daily / weekly / monthly windows for the Statistics page
and API v3. Content-stable: unchanged output is not rewritten.

Usage
-----
    python3 scripts/analytics_rollup.py
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

from omnisource.analytics_rollup import build_rollup
from omnisource.io import read_json, write_json_stable

ROOT = Path(__file__).resolve().parents[1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--analytics", default=str(ROOT / "feeds" / "analytics.json"))
    parser.add_argument("--monitoring", default=str(ROOT / "data" / "status.json"))
    parser.add_argument("--out", default=str(ROOT / "data" / "analytics_rollup.json"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    analytics = read_json(Path(args.analytics))
    monitoring = read_json(Path(args.monitoring))
    history = monitoring.get("history", []) if isinstance(monitoring, dict) else []
    doc = build_rollup(
        analytics if isinstance(analytics, dict) else {},
        [entry for entry in history if isinstance(entry, dict)],
    )
    changed = write_json_stable(Path(args.out), doc)
    print(
        f"analytics_rollup: {doc['coverageDays']} day(s), "
        f"{len(doc['weekly'])} week(s), {len(doc['monthly'])} month(s)"
        f"{'' if changed else ' (unchanged)'} -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
