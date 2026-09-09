#!/usr/bin/env python3
"""Assemble the static GitHub Pages site from its organized source directories."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "_site"


def build_site(output: Path) -> None:
    """Build a complete, deployable site without changing source files."""
    output = output.resolve()
    if output == ROOT or ROOT not in output.parents:
        raise ValueError("output must be a directory inside the repository")

    shutil.rmtree(output, ignore_errors=True)
    shutil.copytree(ROOT / "website", output)
    shutil.copytree(ROOT / "assets", output / "assets")
    shutil.copytree(ROOT / "feeds", output / "feeds", ignore=shutil.ignore_patterns("state.json"))

    # Keep the historical flat source URLs working for existing subscribers.
    for feed in (ROOT / "feeds").glob("*.json"):
        if feed.name != "state.json":
            shutil.copy2(feed, output / feed.name)
    for feed in (ROOT / "feeds").glob("*.xml"):
        shutil.copy2(feed, output / feed.name)

    shutil.copy2(ROOT / "catalog.json", output / "catalog.json")
    (output / ".nojekyll").touch()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="site output directory")
    args = parser.parse_args()
    build_site(args.output)
    print(f"Built site at {args.output.resolve()}")


if __name__ == "__main__":
    main()
