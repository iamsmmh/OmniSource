#!/usr/bin/env python3
"""Build source growth, package history, and source timeline documents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from omnisource.intelligence import build_package_intelligence, build_source_insights, build_timeline
from omnisource.io import read_json, write_json_stable

ROOT = Path(__file__).resolve().parents[2]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default=str(ROOT / "data" / "source_registry.json"))
    parser.add_argument("--apps", default=str(ROOT / "feeds" / "apps.json"))
    parser.add_argument("--history", default=str(ROOT / "data" / "release_history.json"))
    parser.add_argument("--previous", default=str(ROOT / "data" / "source_intelligence.json"))
    parser.add_argument("--out-dir", default=str(ROOT / "data"))
    return parser.parse_args(argv)


def _apps(path: str) -> list[dict]:
    value = read_json(Path(path))
    values = value.get("apps", []) if isinstance(value, dict) else value
    return [item for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    registry = read_json(Path(args.registry))
    if not isinstance(registry, dict):
        print(f"intelligence: missing registry {args.registry}")
        return 1
    previous = read_json(Path(args.previous))
    history = read_json(Path(args.history))
    insights = build_source_insights(
        registry,
        previous=previous if isinstance(previous, dict) else None,
        release_history=history if isinstance(history, dict) else None,
    )
    package = build_package_intelligence(
        _apps(args.apps),
        release_history=history if isinstance(history, dict) else None,
    )
    timeline = build_timeline(registry)
    out_dir = Path(args.out_dir)
    changed = [
        write_json_stable(out_dir / "source_intelligence.json", insights),
        write_json_stable(out_dir / "package_intelligence.json", package),
        write_json_stable(out_dir / "source_timeline.json", timeline),
    ]
    print(
        f"intelligence: {insights['count']} sources, {package['count']} apps, "
        f"{timeline['count']} events; changed={sum(changed)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
