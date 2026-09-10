"""App health engine (Phase 6).

A single explainable 0-100 score per app:

    Health Score =
        30% download success      uptime of health probes (30-day window;
                                  current probe when no history exists)
      + 25% update frequency      cadence curve: 7 days = best, 365 days = 0
      + 20% release availability  current download reachability
                                  (+0.1 bonus when mirrors are configured)
      + 15% metadata completeness share of identity/metadata fields present
      + 10% source reliability    source reputation score / 100

Statuses:

* ``archived`` — the catalog marks the app deprecated/archived
* ``healthy``  — score ≥ 70
* ``warning``  — 40 ≤ score < 70
* ``critical`` — score < 40

The score is rendered into ``feeds/health.json`` (``healthScore``,
``healthStatus``, ``scoreBreakdown`` per app), the app detail pages and the
status page.
"""

from __future__ import annotations

from typing import Any

from omnisource.domain import Catalog, today
from omnisource.utils.dates import average_update_gap_days
from omnisource.utils.health import probe_window

HEALTH_WEIGHTS = {
    "downloadSuccess": 0.30,
    "updateFrequency": 0.25,
    "releaseAvailability": 0.20,
    "metadataCompleteness": 0.15,
    "sourceReliability": 0.10,
}

HEALTHY_MIN = 70
WARNING_MIN = 40


def _download_success(app_state: dict[str, Any], reachable_now: bool | None) -> float:
    total, reachable, _ = probe_window(app_state)
    if total:
        return reachable / total
    if reachable_now is None:
        return 0.5  # never probed: neutral, do not punish manual apps
    return 1.0 if reachable_now else 0.0


def _update_frequency_component(state: dict[str, Any], slug: str) -> float:
    gap = average_update_gap_days(state, slug)
    if gap <= 0:
        return 0.5  # no history: neutral
    if gap <= 7:
        return 1.0
    if gap <= 90:
        # 1.0 at 7 days -> 0.3 at 90 days
        return round(1.0 - (gap - 7) / (90 - 7) * 0.7, 4)
    if gap <= 365:
        # 0.3 at 90 days -> 0.0 at 365 days
        return round(0.3 * (1 - (gap - 90) / (365 - 90)), 4)
    return 0.0


def _release_availability(reachable_now: bool | None) -> float:
    # Mirrors do not add points on their own: the failover chain already
    # decides whether the download is actually reachable.
    if reachable_now is None:
        return 0.5
    return 1.0 if reachable_now else 0.0


METADATA_FIELDS = (
    "name",
    "shortDescription",
    "description",
    "icon",
    "homepage",
    "screenshots",
    "compatibility",
    "verification",
)


def _field_present(field: str, value: Any, raw: dict[str, Any]) -> bool:
    if field == "homepage":
        return bool(value or raw.get("upstreamURL"))
    if field == "screenshots":
        return isinstance(value, list) and bool(value)
    if field in {"compatibility", "verification"}:
        return isinstance(value, dict) and bool(value)
    return bool(value)


def _metadata_completeness(app: Any) -> float:
    raw = app.raw
    present = sum(1 for field in METADATA_FIELDS if _field_present(field, raw.get(field), raw))
    return present / len(METADATA_FIELDS)


def _source_reliability(reputation_doc: dict[str, Any], app: Any) -> float:
    if not isinstance(reputation_doc, dict):
        return 0.5
    upstream = app.upstream
    identity = (upstream.identity if upstream is not None else None) or f"manual:{app.slug}"
    for source in reputation_doc.get("sources", []):
        if isinstance(source, dict) and source.get("id") == identity:
            try:
                return max(0.0, min(1.0, float(source.get("score") or 0) / 100))
            except (TypeError, ValueError):
                return 0.5
    return 0.5


def score_status(app: Any, score: int) -> str:
    if app.lifecycle_status == "archived" or app.status == "deprecated":
        return "archived"
    if score >= HEALTHY_MIN:
        return "healthy"
    if score >= WARNING_MIN:
        return "warning"
    return "critical"


def compute_health_score(
    app: Any,
    state: dict[str, Any],
    *,
    reachable_now: bool | None,
    reputation_doc: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return ``{health_score, status, breakdown}`` for one app."""
    app_state = state.get(app.slug) if isinstance(state.get(app.slug), dict) else {}
    download_success = _download_success(app_state, reachable_now)
    update_frequency = _update_frequency_component(state, app.slug)
    release_availability = _release_availability(reachable_now)
    metadata = _metadata_completeness(app)
    reliability = _source_reliability(reputation_doc or {}, app)

    score = round(
        100
        * (
            HEALTH_WEIGHTS["downloadSuccess"] * download_success
            + HEALTH_WEIGHTS["updateFrequency"] * update_frequency
            + HEALTH_WEIGHTS["releaseAvailability"] * release_availability
            + HEALTH_WEIGHTS["metadataCompleteness"] * metadata
            + HEALTH_WEIGHTS["sourceReliability"] * reliability
        )
    )
    return {
        "health_score": max(0, min(100, score)),
        "status": score_status(app, score),
        "breakdown": {
            "downloadSuccess": round(download_success, 4),
            "updateFrequency": round(update_frequency, 4),
            "releaseAvailability": round(release_availability, 4),
            "metadataCompleteness": round(metadata, 4),
            "sourceReliability": round(reliability, 4),
        },
        "weights": dict(HEALTH_WEIGHTS),
    }


def build_health_scores(
    catalog: Catalog,
    state: dict[str, Any],
    health_doc: dict[str, Any] | None = None,
    reputation_doc: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Score every app; keyed by slug."""
    health_doc = health_doc or {}
    reachable_by_slug: dict[str, bool | None] = {}
    for item in health_doc.get("apps", []):
        if isinstance(item, dict) and item.get("slug") is not None:
            value = item.get("downloadReachable")
            reachable_by_slug[str(item["slug"])] = value if isinstance(value, bool) else None
    out: dict[str, dict[str, Any]] = {}
    for app in catalog.apps:
        out[app.slug] = compute_health_score(app, state, reachable_now=reachable_by_slug.get(app.slug))
    return out


def annotate_health_doc(
    health_doc: dict[str, Any],
    scores: dict[str, dict[str, Any]],
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Inject health scores into a rendered ``health.json`` document (in place)."""
    for item in health_doc.get("apps", []):
        if not isinstance(item, dict):
            continue
        score = scores.get(str(item.get("slug")))
        if not score:
            continue
        item["healthScore"] = score["health_score"]
        item["healthStatus"] = score["status"]
        item["scoreBreakdown"] = score["breakdown"]
    totals = health_doc.setdefault("totals", {})
    for status in ("healthy", "warning", "critical"):
        totals[status] = sum(
            1 for item in health_doc.get("apps", []) if isinstance(item, dict) and item.get("healthStatus") == status
        )
    if generated_at:
        health_doc["generatedAt"] = generated_at or health_doc.get("generatedAt") or today()
    return health_doc
