"""Transparent application and repository health signals."""

from __future__ import annotations

from datetime import UTC, date, datetime
from itertools import pairwise
from typing import Any

from omnisource.domain import App


def calculate_app_health(
    app: App,
    state_entry: dict[str, Any] | None,
    *,
    as_of: date | None = None,
    repository: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Calculate explainable signals, never an opaque security score."""
    state_entry = state_entry if isinstance(state_entry, dict) else {}
    health_entry = state_entry.get("health") if isinstance(state_entry.get("health"), dict) else {}
    versions = state_entry.get("versions") if isinstance(state_entry.get("versions"), list) else []
    latest_date = _date_from(versions[0].get("date")) if versions and isinstance(versions[0], dict) else None
    today = as_of or datetime.now(UTC).date()
    days_since_release = (today - latest_date).days if latest_date else None
    release_dates = [
        parsed for item in versions if isinstance(item, dict) if (parsed := _date_from(item.get("date"))) is not None
    ]
    frequency = _average_interval(release_dates)
    completeness_fields = (
        bool(app.name),
        bool(app.developer),
        bool(app.description),
        bool(app.icon),
        bool(app.repository_url),
        bool(app.bundle_id or app.package_name),
        bool(versions),
    )
    completeness = round(sum(completeness_fields) / len(completeness_fields), 3)
    repository_ok = None
    if repository:
        repository_ok = repository.get("lastError") in (None, "")
    return {
        "downloadReachable": bool(health_entry.get("reachable", True)),
        "downloadDetail": str(health_entry.get("detail") or "not probed"),
        "repositoryReachable": repository_ok,
        "lastReleaseDate": latest_date.isoformat() if latest_date else None,
        "daysSinceRelease": days_since_release,
        "releaseFrequencyDays": frequency,
        "repositoryActivity": {
            "lastSync": repository.get("lastSync") if repository else None,
            "lastSuccess": repository.get("lastSuccess") if repository else None,
        },
        "brokenDownloadLinks": 0 if health_entry.get("reachable", True) else 1,
        "metadataCompleteness": completeness,
        "integrityAvailable": bool(versions and isinstance(versions[0], dict) and versions[0].get("sha256")),
        "integrityVerified": None,
        "status": lifecycle_status(app, download_reachable=bool(health_entry.get("reachable", True))),
        "signalsVersion": 1,
    }


def lifecycle_status(app: App, *, download_reachable: bool = True) -> str:
    """Map editorial status plus observed reachability to the platform state."""
    if not download_reachable:
        return "broken"
    return app.lifecycle_status


def _date_from(value: object) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def _average_interval(values: list[date]) -> float | None:
    if len(values) < 2:
        return None
    ordered = sorted(set(values), reverse=True)
    intervals = [(left - right).days for left, right in pairwise(ordered)]
    return round(sum(intervals) / len(intervals), 2) if intervals else None
