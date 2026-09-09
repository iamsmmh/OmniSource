"""API mirror builder.

The repository publishes both ``feeds/`` (canonical artifacts consumed by
the pipeline and the website) and ``api/`` (developer-facing stable URLs).
This module makes sure every new document is mirrored at the matching
``api/`` URL so SDKs and third-party consumers do not have to keep up with
internal renames.

The mapping is purely a 1:1 copy. It is intentionally explicit (not glob
based) so a feed rename is a deliberate, reviewable change.
"""

from __future__ import annotations

import shutil
from collections.abc import Iterable
from pathlib import Path

# The full list of paths that should exist at both ``feeds/`` and ``api/``.
# Adding a new feed requires editing this list — by design.
MIRRORED_FEEDS: tuple[str, ...] = (
    "apps.json",
    "discovery.json",
    "sources.json",
    "verification.json",
    "status.json",
    "duplicates.json",
    "analytics.json",
    "trending.json",
    "related.json",
    "reputation.json",
    "download-intelligence.json",
    "community.json",
    "install.json",
    "search-index.json",
    "compare.json",
    "screenshots.json",
    "health.json",
    "updates.json",
)

# Auxiliary endpoints that the website and SDKs also rely on.
MIRRORED_AUX: tuple[str, ...] = (
    "feed.xml",
    "rss.xml",
)


def mirror_feeds(feeds_dir: Path, api_dir: Path, names: Iterable[str] = MIRRORED_FEEDS) -> list[Path]:
    """Copy every feed listed in ``names`` from ``feeds_dir`` to ``api_dir``.

    Returns the list of files written (so the caller can log the result).
    """
    api_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name in names:
        source = feeds_dir / name
        if not source.exists():
            continue
        destination = api_dir / name
        if destination.exists() and destination.read_bytes() == source.read_bytes():
            continue
        shutil.copyfile(source, destination)
        written.append(destination)
    return written
