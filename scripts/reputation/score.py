#!/usr/bin/env python3
"""Score every upstream source and write ``data/source_reputation.json``.

Reads the pipeline's ``feeds/reputation.json`` (0..100 scores) plus
``feeds/status.json`` health, maps each score onto the public
verified / trusted / good / warning / untrusted ladder, and lists the
quarantined sources that must never auto-publish.

Usage
-----
    python3 scripts/reputation/score.py
    python3 scripts/reputation/score.py --min-score 25  # quarantine floor (default)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from omnisource.io import read_json, write_json
from omnisource.reputation_labels import QUARANTINE_THRESHOLD, build_labels

ROOT = Path(__file__).resolve().parents[2]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reputation", default=str(ROOT / "feeds" / "reputation.json"))
    parser.add_argument("--status", default=str(ROOT / "feeds" / "status.json"))
    parser.add_argument("--out", default=str(ROOT / "data" / "source_reputation.json"))
    parser.add_argument("--min-score", type=int, default=QUARANTINE_THRESHOLD)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    reputation = read_json(Path(args.reputation))
    if not isinstance(reputation, dict):
        print(f"reputation: cannot read {args.reputation}")
        return 1
    status = read_json(Path(args.status))
    doc = build_labels(reputation, status if isinstance(status, dict) else None)
    if args.min_score != QUARANTINE_THRESHOLD:
        doc["quarantineThreshold"] = max(0, min(100, args.min_score))
        doc["quarantined"] = [
            item["id"] for item in doc["sources"] if float(item.get("score", 0) or 0) < doc["quarantineThreshold"]
        ]
    write_json(Path(args.out), doc)
    summary = ", ".join(f"{key}={value}" for key, value in sorted(doc["summary"].items()))
    print(f"reputation: {doc['count']} source(s) [{summary}], {len(doc['quarantined'])} quarantined -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
