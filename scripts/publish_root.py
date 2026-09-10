#!/usr/bin/env python3
"""Publish the generated public URLs into the repository root.

GitHub Pages serves this repository in *branch* mode, so the live site is the
repository tree: a file that is not committed does not exist on the web. This
script mirrors the canonical generated artifacts into the root so the
installable source URL (``/apps.json``) and every other generated URL resolve:

    /apps.json            /<slug>.json   /<slug>.xml   /feed.xml
    /badge-*.json         /<intelligence>.json         /catalog.min.json
    /api/*.json + .gz     /api/<route>   /api/index.json
    /sitemap.xml          /robots.txt    /.nojekyll

Every copy is byte-identical to its ``feeds/`` original (git stores the shared
blob once, and ``check_reproducible.py`` fails the build if one drifts), and
files that are no longer generated are removed from the mirror.

The sync pipeline already calls this (see :func:`omnisource.pipeline.run`), so
scheduled builds keep the root in step. Run it directly after a manual edit to
``feeds/`` — e.g. the ``merge.yml`` safety net — or to repair the mirror:

    python3 scripts/publish_root.py
    python3 scripts/publish_root.py --check   # fail if the mirror is stale
"""

from __future__ import annotations

import argparse
import filecmp
import sys
from pathlib import Path

_SCRIPTS = str(Path(__file__).resolve().parent)
if _SCRIPTS in sys.path:
    sys.path.remove(_SCRIPTS)
_SRC = str(Path(__file__).resolve().parents[1] / "src")
if _SRC in sys.path:
    sys.path.remove(_SRC)
sys.path.insert(0, _SRC)

from omnisource.site import API_DOCUMENTS, API_ROUTES, publish_repo_artifacts

REPO_ROOT = Path(__file__).resolve().parents[1]


def find_stale_mirror_files() -> list[str]:
    """Root/API mirror files that are missing, stale or no longer generated."""
    feeds = REPO_ROOT / "feeds"
    feed_files = list(feeds.glob("*.json")) + list(feeds.glob("*.xml"))
    flat = sorted(path.name for path in feed_files if path.name != "state.json")
    stale: list[str] = []

    def differs(mirror: Path, source: Path) -> bool:
        return not mirror.exists() or not filecmp.cmp(mirror, source, shallow=False)

    for name in flat:
        if differs(REPO_ROOT / name, feeds / name):
            stale.append(name)

    # A root JSON/XML that no feed or fixed publisher output owns is stale: the
    # publisher prunes it on the next run.
    owned = set(flat) | {"catalog.json", "catalog.min.json", "sitemap.xml"}
    for path in sorted(REPO_ROOT.glob("*")):
        if path.is_file() and path.suffix.lower() in {".json", ".xml"} and path.name not in owned:
            stale.append(f"{path.name} (stale generated copy)")

    # API mirror: every documented endpoint must exist and be byte-identical to
    # the canonical feed it mirrors (api/catalog.json + .min point at discovery).
    api_expected = {name: name for name in API_DOCUMENTS}
    api_expected.update({"catalog.json": "discovery.json", "catalog.min.json": "discovery.json"})
    api_expected.update(dict(API_ROUTES))
    api_expected["index.json"] = ""
    for name, source_name in sorted(api_expected.items()):
        target = REPO_ROOT / "api" / name
        if not source_name:
            if not target.exists():
                stale.append(f"api/{name}")
            continue
        source = feeds / source_name
        if name == "catalog.min.json":
            if not target.exists():
                stale.append("api/catalog.min.json")
            continue
        if source.exists() and differs(target, source):
            stale.append(f"api/{name}")

    for name in ("sitemap.xml", "robots.txt", ".nojekyll", "catalog.min.json"):
        if not (REPO_ROOT / name).exists():
            stale.append(name)
    return sorted(set(stale))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="report drift instead of writing")
    args = parser.parse_args(argv)

    if args.check:
        stale = find_stale_mirror_files()
        if stale:
            print(f"publish_root: {len(stale)} root artifact(s) missing or stale:", file=sys.stderr)
            for name in stale:
                print(f"  {name}", file=sys.stderr)
            print("  run: python3 scripts/publish_root.py", file=sys.stderr)
            return 1
        print("publish_root: repository root mirrors feeds/ byte-for-byte")
        return 0

    summary = publish_repo_artifacts(REPO_ROOT)
    print(
        f"publish_root: {summary['flat_files']} flat feed URL(s), "
        f"{summary['api_documents']} API document(s) (+{summary['api_gz_files']} gz), "
        f"sitemap + robots + .nojekyll; {len(summary['written'])} file(s) refreshed, "
        f"{len(summary['removed'])} stale file(s) removed"
    )
    for name in summary["removed"]:
        print(f"  removed {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
