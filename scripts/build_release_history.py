#!/usr/bin/env python3
"""Build the append-only release ledger (``data/release_history.json``).

Merges the pipeline state (``feeds/state.json``) into the existing ledger
without ever deleting old releases. Supports rollback planning:

Usage
-----
    python3 scripts/build_release_history.py
    python3 scripts/build_release_history.py --rollback ytlite --to 2.1.0
"""

from __future__ import annotations

import argparse
import json
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
from omnisource.release_history import build_history, rollback_plan

ROOT = Path(__file__).resolve().parents[1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--state", default=str(ROOT / "feeds" / "state.json"))
    parser.add_argument("--out", default=str(ROOT / "data" / "release_history.json"))
    parser.add_argument("--rollback", default="", metavar="SLUG", help="print a rollback plan instead of building")
    parser.add_argument("--to", default="", metavar="VERSION", help="rollback target version")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out = Path(args.out)
    if args.rollback:
        ledger = read_json(out)
        apps = ledger.get("apps", {}) if isinstance(ledger, dict) else {}
        history = apps.get(args.rollback, [])
        print(json.dumps(rollback_plan(history, args.to), indent=2, ensure_ascii=False))
        return 0
    state = read_json(Path(args.state))
    if not isinstance(state, dict):
        print(f"release_history: cannot read {args.state}")
        return 1
    previous = read_json(out)
    doc = build_history(state, previous if isinstance(previous, dict) else None)
    changed = write_json_stable(out, doc)
    print(
        f"release_history: {doc['appCount']} app(s), {doc['releases']} release(s)"
        f"{'' if changed else ' (unchanged)'} -> {out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
