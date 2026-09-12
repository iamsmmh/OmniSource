#!/usr/bin/env python3
"""Build ``data/security.json`` and gate the pipeline on critical findings.

Verifies SHA-256 / SHA-512 coverage, detects duplicate binaries, rolls up
download integrity and audits provenance. Exits 1 when a *critical*
finding exists (``security.yml`` blocks publication in that case).

Usage
-----
    python3 scripts/security/scan.py
    python3 scripts/security/scan.py --fail-on high  # also fail on high findings
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from omnisource.io import read_json, write_json
from omnisource.security import build_security_report

ROOT = Path(__file__).resolve().parents[2]

SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--feed", default=str(ROOT / "feeds" / "apps.json"))
    parser.add_argument("--catalog", default=str(ROOT / "catalog.json"))
    parser.add_argument("--health", default=str(ROOT / "feeds" / "health.json"))
    parser.add_argument("--out", default=str(ROOT / "data" / "security.json"))
    parser.add_argument("--fail-on", default="critical", choices=sorted(SEVERITY_RANK))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    feed = read_json(Path(args.feed))
    apps = feed.get("apps", []) if isinstance(feed, dict) else []
    catalog = read_json(Path(args.catalog))
    catalog_apps = catalog.get("apps", []) if isinstance(catalog, dict) else []
    health = read_json(Path(args.health))
    report = build_security_report(
        apps=[item for item in apps if isinstance(item, dict)],
        catalog_apps=[item for item in catalog_apps if isinstance(item, dict)],
        health=health if isinstance(health, dict) else None,
    )
    write_json(Path(args.out), report)
    floor = SEVERITY_RANK[args.fail_on]
    blocking = [item for item in report["findings"] if SEVERITY_RANK[item["severity"]] >= floor]
    for item in report["findings"]:
        print(f"{item['severity']}: [{item['check']}] {item['id']} — {item['detail']}")
    summary = report["summary"]
    print(
        f"security: verdict={report['verdict']} "
        f"(sha256 {summary['sha256']}/{summary['apps']}, "
        f"dupes={summary['duplicateBinaries']}, failing={summary['downloadsFailing']}) -> {args.out}"
    )
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
