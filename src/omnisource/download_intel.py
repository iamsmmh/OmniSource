"""Download intelligence.

This module enriches the health board with three additional pieces of
information that are useful to clients deciding *which* mirror to use:

* **Historical availability** — fraction of probes that succeeded, per app.
* **Mirror availability** — every reachable mirror (primary + fallbacks).
* **Release consistency** — whether the app's release cadence is regular
  enough to be a reliable source of new versions.

The output is a single ``feeds/download-intelligence.json`` document plus a
short summary used by the website hero. Nothing here is hand-edited: every
metric is recomputed on every build from the pipeline state.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from omnisource.discovery import newest_version
from omnisource.domain import Catalog, today
from omnisource.utils.dates import parse_date as _parse_date
from omnisource.utils.health import WINDOW_DAYS
from omnisource.utils.health import probe_window as _window_probe

INTEL_SCHEMA_VERSION = 1


def release_consistency(state: dict[str, Any], slug: str) -> float:
    """0..1 release-cadence consistency (lower variance = more consistent)."""
    versions = (state.get(slug) or {}).get("versions") or []
    if not isinstance(versions, list) or len(versions) < 2:
        return 0.0
    deltas: list[int] = []
    dates: list[date] = []
    for v in versions:
        if isinstance(v, dict):
            parsed = _parse_date(v.get("date"))
            if parsed is not None:
                dates.append(parsed)
    dates.sort()
    for i in range(1, len(dates)):
        delta = (dates[i] - dates[i - 1]).days
        if delta > 0:
            deltas.append(delta)
    if not deltas:
        return 0.0
    avg = sum(deltas) / len(deltas)
    variance = sum((d - avg) ** 2 for d in deltas) / len(deltas)
    # Lower variance means a more consistent release cadence.
    score = max(0.0, 1.0 - (variance / (avg * avg + 1)))
    return round(score, 4)


def build_download_intel_doc(
    catalog: Catalog,
    state: dict[str, Any],
    health_doc: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``feeds/download-intelligence.json``."""
    apps: list[dict[str, Any]] = []
    total_probes = 0
    total_reachable = 0
    total_latency = 0.0
    latency_count = 0
    mirror_count = 0
    for app in catalog.apps:
        app_state = state.get(app.slug) if isinstance(state.get(app.slug), dict) else state
        newest = newest_version(state, app.slug)
        probes, reachable, avg_latency = _window_probe(app_state)
        availability = round((reachable / probes) * 100, 2) if probes else 0.0
        if avg_latency is not None:
            total_latency += avg_latency
            latency_count += 1
        total_probes += probes
        total_reachable += reachable
        fallbacks = newest.get("fallbackDownloadURLs") or app.raw.get("fallbackDownloadURLs") or []
        fallbacks = [url for url in fallbacks if isinstance(url, str) and url.startswith(("http://", "https://"))]
        mirror_count += 1 + len(fallbacks)
        consistency = release_consistency(state, app.slug)
        apps.append(
            {
                "slug": app.slug,
                "name": app.name,
                "availability": availability,
                "probes": probes,
                "averageLatencyMs": round(avg_latency, 1) if avg_latency is not None else None,
                "mirrorCount": 1 + len(fallbacks),
                "releaseConsistency": consistency,
                "primaryURL": newest.get("downloadURL") or "",
                "fallbackURLs": fallbacks,
            }
        )
    avg_availability = round((total_reachable / total_probes) * 100, 2) if total_probes else 0.0
    avg_latency = round(total_latency / latency_count, 1) if latency_count else None
    apps.sort(key=lambda item: item["availability"], reverse=True)
    return {
        "schemaVersion": INTEL_SCHEMA_VERSION,
        "generatedAt": today(),
        "windowDays": WINDOW_DAYS,
        "summary": {
            "averageAvailability": avg_availability,
            "averageResponseTimeMs": avg_latency,
            "mirrorCount": mirror_count,
            "probes": total_probes,
        },
        "apps": apps,
    }
