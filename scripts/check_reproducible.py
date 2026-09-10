#!/usr/bin/env python3
"""Verify that generated artifacts are reproducible from committed state.

The offline build (``python3 scripts/omnisource.py --no-sync --no-health``)
must not change anything that is committed. This script snapshots the
generated outputs (feeds JSON, app pages, README blocks), runs the offline
build, snapshots again and compares.

Volatile values that are correct to refresh on every build are normalized
before comparing — the build/sync date (``generatedAt``, ``lastSync``), the
README ``last sync`` line, the rolling analytics history (which legitimately
gains a new day's entry) and the screenshot-mirror state
(``mirrored``/``size``/``sha256``/``thumbnailSize``), which depends on
whether *this* machine could reach the remote screenshot hosts. Any *other*
difference means a hand-edit or a bug in the generators and fails the check.
Untracked files under ``feeds/``/``apps/`` are also reported, because a
generated artifact that is not committed would silently diverge after deploy.

Usage
-----
    python3 scripts/check_reproducible.py          # exit 0 = reproducible
    python3 scripts/check_reproducible.py --diff   # print differing files
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The offline build may legitimately rewrite these; nothing else is checked.
# The pipeline commits only the canonical generated outputs (feeds/, app
# pages, README blocks). Deployed-only artifacts — flat feed URLs, sitemap,
# robots, homepage stats — are assembled into _site/ by scripts/build_site.py
# and never touch the repository root, so they are intentionally not tracked.
TRACKED_PATTERNS = (
    "feeds/*.json",
    "apps/*/index.html",
    "compare/*/index.html",
    "collections/*/index.html",
    "README.md",
)
# state.json is runtime state (syncedAt, health history) and changes whenever
# the scheduler runs a real sync, so it is intentionally not compared.

# (pattern, replacement): values that are date-derived and therefore differ
# between two builds on different days without indicating drift.
NORMALIZERS = (
    (re.compile(rb'"generatedAt":\s*"[^"]*"'), b'"generatedAt": "<DATE>"'),
    (re.compile(rb'"lastSync":\s*"[^"]*"'), b'"lastSync": "<DATE>"'),
    (re.compile(rb"last sync \*\*[\d-]+\*\*"), b"last sync **<DATE>**"),
    (re.compile(rb"last sync \d{4}-\d{2}-\d{2}"), b"last sync <DATE>"),
    (re.compile(rb"<lastBuildDate>[^<]*</lastBuildDate>"), b"<lastBuildDate>DATE</lastBuildDate>"),
    (re.compile(rb"<lastmod>[^<]*</lastmod>"), b"<lastmod>DATE</lastmod>"),
    # Analytics history gains an entry per day; its dates are derived from the
    # snapshot date, not from content.
    (re.compile(rb'"history":\s*\[.*?\]', re.DOTALL), b'"history": [...]'),
)


def _matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/*.json"):
        prefix = pattern[: -len("/*.json")]
        return path.startswith(prefix + "/") and path.rsplit("/", 1)[-1].endswith(".json")
    if pattern.endswith("/*/index.html"):
        parts = path.split("/")
        return len(parts) == 3 and parts[0] in {"apps", "compare", "collections"} and parts[2] == "index.html"
    if "*" in pattern and "/" not in pattern:
        # Root-level glob (e.g. the flat feed copies at the repository root).
        return "/" not in path and fnmatch.fnmatch(path, pattern)
    return path == pattern


def _norm(data: bytes) -> bytes:
    for pattern, replacement in NORMALIZERS:
        data = pattern.sub(replacement, data)
    return data


def _norm_screenshots(data: bytes) -> bytes:
    """Blank the network-dependent mirror state in ``feeds/screenshots.json``.

    Whether a screenshot could be mirrored depends on the build machine's
    reachability to third-party hosts (a fresh CI runner downloads, an
    offline or sandboxed build cannot), so ``mirrored``/``size``/``sha256``
    /``thumbnailSize`` are environment state, not generated content. The
    URLs and thumbnail metadata stay fully checked.
    """
    try:
        doc = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return data
    if not isinstance(doc, dict):
        return data
    for entry in doc.get("screenshots", []):
        if isinstance(entry, dict):
            for key in ("mirrored", "size", "sha256", "thumbnailSize"):
                entry.pop(key, None)
    return json.dumps(doc, indent=2, sort_keys=True).encode("utf-8")


def _snapshot() -> dict[str, bytes]:
    """Map path -> normalized hash for every generated file on disk."""
    snapshot: dict[str, bytes] = {}
    for pattern in TRACKED_PATTERNS:
        prefix = pattern[: pattern.find("*")]
        glob = pattern[len(prefix) :]
        for path in (ROOT / prefix).glob(glob):
            if path.is_file() and path.name != "state.json":
                data = _norm(path.read_bytes())
                if path.name == "screenshots.json":
                    data = _norm_screenshots(data)
                snapshot[str(path.relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
    return snapshot


def _untracked_generated() -> list[str]:
    listed = (
        subprocess.run(
            [shutil.which("git") or "git", "-C", str(ROOT), "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            check=True,
        )
        .stdout.decode("utf-8")
        .splitlines()
    )
    return [rel for rel in listed if any(_matches(rel, p) for p in TRACKED_PATTERNS)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--diff", action="store_true", help="print paths that differ")
    args = parser.parse_args(argv)

    before = _snapshot()
    if not before:
        print("check_reproducible: no generated files found", file=sys.stderr)
        return 2

    result = subprocess.run(
        [shutil.which("python3") or "python3", "scripts/omnisource.py", "--no-sync", "--no-health"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("check_reproducible: offline build failed", file=sys.stderr)
        print(result.stderr[-2000:], file=sys.stderr)
        return 3

    after = _snapshot()
    differing = sorted(rel for rel in before if before[rel] != after.get(rel))
    untracked = _untracked_generated()

    if differing or untracked:
        if differing:
            print(f"check_reproducible: {len(differing)} generated file(s) changed on rebuild:")
            for rel in differing:
                print(f"  {rel}")
        if untracked:
            print(f"check_reproducible: {len(untracked)} untracked generated file(s):")
            for rel in untracked:
                print(f"  {rel}")
            print("  (commit them or remove them; generated files must not be hand-edited)")
        if args.diff:
            subprocess.run(
                [shutil.which("git") or "git", "-C", str(ROOT), "diff", "--stat", "--", *differing],
                check=False,
            )
        return 1

    print(f"check_reproducible: {len(before)} generated file(s) stable after offline rebuild")
    return 0


if __name__ == "__main__":
    sys.exit(main())
