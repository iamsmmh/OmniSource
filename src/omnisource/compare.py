"""Comparison engine.

Builds ``feeds/compare.json`` — a precomputed lookup of every pair of apps
the website's ``compare.html`` page can render. The structure is dense but
flat enough to be consumed by any framework.

Each comparison row carries:

* **version**           — newer / older / equal
* **source**            — which upstream published each
* **verification**      — VERIFIED / COMMUNITY / MANUAL / UNVERIFIED
* **updateFrequency**   — average gap in days between versions
* **compatibility**     — minOSVersion + clients that can install
* **screenshots**       — both apps' icon URLs (so compare.html can render
                          the icon gallery when the screenshot gallery is
                          empty)
"""

from __future__ import annotations

from datetime import date
from itertools import combinations
from typing import Any

from omnisource.discovery import newest_version, source_label
from omnisource.domain import Catalog, today

COMPARE_SCHEMA_VERSION = 1


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _update_frequency(state: dict[str, Any], slug: str) -> float:
    versions = (state.get(slug) or {}).get("versions") or []
    if not isinstance(versions, list) or len(versions) < 2:
        return 0.0
    dates: list[date] = []
    for v in versions:
        if isinstance(v, dict):
            parsed = _parse_date(v.get("date"))
            if parsed is not None:
                dates.append(parsed)
    dates.sort()
    deltas = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates)) if (dates[i] - dates[i - 1]).days > 0]
    return round(sum(deltas) / len(deltas), 1) if deltas else 0.0


def _compatibility(app: Any) -> dict[str, Any]:
    compat = app.raw.get("compatibility") if isinstance(app.raw.get("compatibility"), dict) else {}
    return {
        "minOSVersion": app.minimum_ios_version or "",
        "devices": list(compat.get("devices") or []),
    }


def _summary(app: Any, state: dict[str, Any], verification_level: str, health_ok: bool) -> dict[str, Any]:
    newest = newest_version(state, app.slug)
    return {
        "slug": app.slug,
        "name": app.name,
        "icon": f"assets/{app.icon}" if app.icon else "",
        "category": app.category,
        "version": str(newest.get("version") or ""),
        "releaseDate": str(newest.get("date") or ""),
        "source": source_label(app),
        "verificationLevel": verification_level,
        "updateFrequencyDays": _update_frequency(state, app.slug),
        "downloadReachable": health_ok,
        "compatibility": _compatibility(app),
    }


def build_compare_doc(
    catalog: Catalog,
    state: dict[str, Any],
    health_doc: dict[str, Any] | None = None,
    verification_doc: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``feeds/compare.json``."""
    health_doc = health_doc or {}
    health_by_slug = {item.get("slug"): item for item in health_doc.get("apps", []) if isinstance(item, dict)}
    verification_by_slug = {
        item.get("app"): item for item in (verification_doc or {}).get("apps", []) if isinstance(item, dict)
    }

    pairs: list[dict[str, Any]] = []
    for left, right in combinations(catalog.apps, 2):
        left_summary = _summary(
            left,
            state,
            str((verification_by_slug.get(left.slug) or {}).get("status") or "UNVERIFIED"),
            bool((health_by_slug.get(left.slug) or {}).get("downloadReachable")),
        )
        right_summary = _summary(
            right,
            state,
            str((verification_by_slug.get(right.slug) or {}).get("status") or "UNVERIFIED"),
            bool((health_by_slug.get(right.slug) or {}).get("downloadReachable")),
        )

        # "winner" is the recommended pick: verified > community > manual,
        # then most recent release, then better download health.
        def _rank(summary: dict[str, Any]) -> tuple[int, str, int]:
            order = {"VERIFIED": 3, "COMMUNITY": 2, "MANUAL": 1, "UNVERIFIED": 0}
            return (
                order.get(summary["verificationLevel"], 0),
                summary["releaseDate"],
                1 if summary["downloadReachable"] else 0,
            )

        left_rank = _rank(left_summary)
        right_rank = _rank(right_summary)
        if left_rank > right_rank:
            winner = left_summary["slug"]
        elif right_rank > left_rank:
            winner = right_summary["slug"]
        else:
            winner = ""
        pairs.append(
            {
                "left": left_summary,
                "right": right_summary,
                "winner": winner,
                "shareBundle": left.bundle_id == right.bundle_id and bool(left.bundle_id),
                "shareCategory": left.category == right.category and bool(left.category),
            }
        )

    pairs.sort(
        key=lambda item: (
            -int(item["shareBundle"]),
            -int(item["shareCategory"]),
            item["left"]["name"].casefold(),
            item["right"]["name"].casefold(),
        )
    )

    return {
        "schemaVersion": COMPARE_SCHEMA_VERSION,
        "generatedAt": today(),
        "count": len(pairs),
        "pairs": pairs,
    }
