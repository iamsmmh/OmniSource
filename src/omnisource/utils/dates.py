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
    """Sorted list of parseable release dates recorded for ``slug``."""
    versions = (state.get(slug) or {}).get("versions") or []
    if not isinstance(versions, list):
        return []
    parsed: list[date] = []
    for version in versions:
        if isinstance(version, dict):
            when = parse_date(version.get("date"))
            if when is not None:
                parsed.append(when)
    parsed.sort()
    return parsed


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
