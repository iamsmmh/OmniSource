"""Shared date and release-cadence helpers.

Extracted from five near-identical private copies (``analytics``,
``community``, ``compare``, ``download_intel``, ``reputation``) — this is the
single implementation; the intelligence modules import from here.
"""

from __future__ import annotations

from datetime import date
from itertools import pairwise
from typing import Any


def parse_date(value: Any) -> date | None:
    """Parse the first 10 characters of ``value`` as an ISO date, or ``None``."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def version_dates(state: dict[str, Any], slug: str) -> list[date]:
    """Sorted list of parseable release dates recorded for ``slug``.

    Combines the resolved ``versions`` retained in ``state[slug]`` with the
    global ``updateHistory`` release log. ``upstream.keepVersions`` retains a
    single newest version for most apps, so the per-app ``versions`` list is
    usually one entry deep; the release log keeps every update event the sync
    has ever recorded, which is what makes cadence and release-activity
    signals meaningful without retaining historical versions.
    """
    parsed: set[date] = set()
    versions = (state.get(slug) or {}).get("versions")
    if isinstance(versions, list):
        for version in versions:
            if isinstance(version, dict):
                when = parse_date(version.get("date"))
                if when is not None:
                    parsed.add(when)
    history = state.get("updateHistory")
    if isinstance(history, list):
        for event in history:
            if isinstance(event, dict) and str(event.get("appId") or "") == slug:
                when = parse_date(event.get("releaseDate"))
                if when is not None:
                    parsed.add(when)
    return sorted(parsed)


def average_update_gap_days(state: dict[str, Any], slug: str) -> float:
    """Average gap (days) between consecutive releases; 0.0 without history."""
    dates = version_dates(state, slug)
    if len(dates) < 2:
        return 0.0
    deltas = [(later - earlier).days for earlier, later in pairwise(dates) if (later - earlier).days > 0]
    if not deltas:
        return 0.0
    return sum(deltas) / len(deltas)


def days_since(value: Any, *, today_iso: str) -> int:
    """Days between ``value`` and ``today_iso``; a large sentinel when unparsable."""
    when = parse_date(value)
    if when is None:
        return 3650
    end = parse_date(today_iso)
    if end is None:
        return 3650
    return max(0, (end - when).days)
