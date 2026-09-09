"""Source health monitoring.

Runs inside the feed build (no separate daemon): every sync probes each app's
primary download URL, records latency and reachability in pipeline state, and
this module renders ``feeds/status.json`` — the machine-readable health board
consumed by the website and monitoring dashboards.

Per-source history is stored in ``state.json`` (``healthHistory``, capped), so
the status document can carry a rolling window without an external database.
History is only appended when the pipeline actually probes (``--no-health``
builds keep the previous window untouched, which also keeps offline
reproducibility checks stable).
"""

from __future__ import annotations

from typing import Any

from omnisource.discovery import newest_version, source_label
from omnisource.domain import Catalog, today

STATUS_SCHEMA_VERSION = 1
HISTORY_LIMIT = 30
WINDOW = 14

# status values
HEALTHY = "healthy"
DEGRADED = "degraded"
UNAVAILABLE = "unavailable"
UNKNOWN = "unknown"


def _status(reachable: bool | None, stale: bool) -> str:
    if reachable is None:
        return UNKNOWN
    if not reachable:
        return UNAVAILABLE
    return DEGRADED if stale else HEALTHY


def build_status_doc(
    catalog: Catalog,
    state: dict[str, Any],
    health_doc: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Render ``status.json`` from the pipeline state and health document."""
    health_doc = health_doc or {}
    health_by_slug = {item.get("slug"): item for item in health_doc.get("apps", []) if isinstance(item, dict)}
    entries: list[dict[str, Any]] = []
    totals = {HEALTHY: 0, DEGRADED: 0, UNAVAILABLE: 0, UNKNOWN: 0}

    for app in catalog.apps:
        app_state = state.get(app.slug, {}) if isinstance(state.get(app.slug), dict) else {}
        health = app_state.get("health", {}) if isinstance(app_state.get("health"), dict) else {}
        health_item = health_by_slug.get(app.slug, {})
        reachable = health.get("reachable")
        raw_latency = health.get("latencyMs")
        latency = None if raw_latency is None else int(raw_latency)
        status = _status(reachable, bool(health_item.get("stale", False)))
        totals[status] += 1

        history = [item for item in app_state.get("healthHistory", []) if isinstance(item, dict)][-WINDOW:]
        entries.append(
            {
                "id": app.slug,
                "app": app.slug,
                "name": app.name,
                "source": source_label(app),
                "sourceURL": app.source_url,
                "type": app.source_type.value,
                "status": status,
                "reachable": reachable,
                "latency": latency,
                "latencyMs": latency,
                "checkedAt": health.get("since", ""),
                "lastUpdate": str(newest_version(state, app.slug).get("date") or ""),
                "valid": True,  # the feed JSON was parsed and rebuilt on this run
                "detail": health.get("detail", ""),
                "history": history,
            }
        )

    entries.sort(key=lambda item: (item["status"] != HEALTHY, str(item["name"]).casefold()))
    return {
        "schemaVersion": STATUS_SCHEMA_VERSION,
        "generatedAt": today(),
        "totals": {"sources": len(entries), **totals},
        "sources": entries,
    }


def remember_probe(state: dict[str, Any], slug: str, *, reachable: bool, detail: str, latency_ms: float) -> None:
    """Record one probe in memory; the pipeline persists ``state`` afterwards."""
    entry = state.setdefault(slug, {})
    if not isinstance(entry, dict):
        entry = {}
        state[slug] = entry
    health = entry.setdefault("health", {})
    if not isinstance(health, dict):
        health = {}
        entry["health"] = health
    health["reachable"] = bool(reachable)
    health["detail"] = str(detail)
    health["latencyMs"] = int(latency_ms)
    health["measuredAt"] = today()

    history = entry.setdefault("healthHistory", [])
    if not isinstance(history, list):
        history = []
        entry["healthHistory"] = history
    history.append(
        {
            "at": today(),
            "reachable": bool(reachable),
            "latencyMs": int(latency_ms),
            "detail": str(detail)[:120],
        }
    )
    del history[:-HISTORY_LIMIT]
