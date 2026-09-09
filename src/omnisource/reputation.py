"""Source reputation engine.

A "source" in OmniSource is the upstream identity that publishes a given
app. Reputation combines four rolling signals:

* **Uptime** — fraction of health probes that found the download reachable.
* **Update frequency** — average gap (in days) between consecutive releases.
* **Broken releases** — count of releases that were later removed /
  re-published (rolled back, yanked, or replaced within 24 hours).
* **Health history** — length of the available probe window; older sources
  are more trustworthy.

The result is a 0..100 score with explicit levels:

* **TRUSTED**    85..100
* **RELIABLE**   70..84
* **AVERAGE**    50..69
* **EXPERIMENTAL**  0..49

The document is consumed by the website (badges throughout), the
``feeds/reputation.json`` endpoint, and the ``api/reputation.json`` mirror.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from omnisource.discovery import source_label
from omnisource.domain import Catalog, today

REPUTATION_SCHEMA_VERSION = 1
WINDOW_DAYS = 30
LEVELS = ("TRUSTED", "RELIABLE", "AVERAGE", "EXPERIMENTAL")


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _level_for(score: float) -> str:
    if score >= 85:
        return "TRUSTED"
    if score >= 70:
        return "RELIABLE"
    if score >= 50:
        return "AVERAGE"
    return "EXPERIMENTAL"


def _health_window(state: dict[str, Any]) -> tuple[int, int, float | None]:
    """Return (total, reachable, average_latency_ms) over the rolling window."""
    history = state.get("healthHistory") or []
    if not isinstance(history, list):
        return 0, 0, None
    cutoff = date.today() - timedelta(days=WINDOW_DAYS)
    total = 0
    reachable = 0
    latencies: list[int] = []
    for item in history:
        if not isinstance(item, dict):
            continue
        when = _parse_date(item.get("date"))
        if when is None or when < cutoff:
            continue
        total += 1
        if item.get("reachable") is True:
            reachable += 1
        latency = item.get("latencyMs")
        if isinstance(latency, (int, float)):
            latencies.append(int(latency))
    avg = sum(latencies) / len(latencies) if latencies else None
    return total, reachable, avg


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
    if len(dates) < 2:
        return 0.0
    deltas = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates)) if (dates[i] - dates[i - 1]).days > 0]
    if not deltas:
        return 0.0
    return sum(deltas) / len(deltas)


def _broken_releases(state: dict[str, Any], slug: str) -> int:
    broken = (state.get(slug) or {}).get("brokenReleases")
    if isinstance(broken, int):
        return max(0, broken)
    # Fall back to a heuristic: count the number of times a release was
    # published and then superseded within 48 hours. This is rare but
    # usually indicates a bad release.
    versions = (state.get(slug) or {}).get("versions") or []
    if not isinstance(versions, list) or len(versions) < 2:
        return 0
    rolled = 0
    dates: list[date] = []
    for v in versions:
        if isinstance(v, dict):
            parsed = _parse_date(v.get("date"))
            if parsed is not None:
                dates.append(parsed)
    dates.sort(reverse=True)
    for i in range(1, len(dates)):
        delta = (dates[i - 1] - dates[i]).days
        if 0 <= delta <= 2:
            rolled += 1
    return rolled


def _score_source(*, uptime: float, avg_delta: float, broken: int, sample_size: int) -> float:
    """Combine the four signals into a 0..100 score."""
    # Uptime is the dominant signal (0..100 weighted at 0.5).
    score = uptime * 100 * 0.5
    # Update frequency: every 30 days is "neutral", 7 days is great, 180+ is
    # cold. We clamp the contribution to 0..25.
    if avg_delta <= 0:
        frequency_component = 0.0
    else:
        # Smooth curve: peak at 7 days, decays to 0 at 180 days.
        peak = 25.0
        frequency_component = max(0.0, peak * (1 - abs(avg_delta - 7) / 180))
        frequency_component = min(peak, frequency_component)
    score += frequency_component
    # Broken releases: each is a -3 penalty, capped at -15.
    score -= min(15.0, broken * 3.0)
    # Sample size bonus: a window of 30+ probes earns 10, 10..29 earns 5.
    if sample_size >= 30:
        score += 10
    elif sample_size >= 10:
        score += 5
    # Clamp.
    return round(max(0.0, min(100.0, score)), 2)


def build_reputation_doc(
    catalog: Catalog,
    state: dict[str, Any],
    health_doc: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``feeds/reputation.json``."""
    health_doc = health_doc or {}
    health_by_slug = {item.get("slug"): item for item in health_doc.get("apps", []) if isinstance(item, dict)}

    grouped: dict[str, dict[str, Any]] = {}
    for app in catalog.apps:
        verification = app.raw.get("verification", {}) if isinstance(app.raw.get("verification"), dict) else {}
        upstream = app.upstream
        identity = (upstream.identity if upstream is not None else None) or f"manual:{app.slug}"
        entry = grouped.setdefault(
            identity,
            {
                "id": identity,
                "source": source_label(app),
                "publisher": verification.get("publisher", ""),
                "homepage": app.repository_url or app.homepage,
                "apps": [],
            },
        )
        entry["apps"].append(app.slug)

    sources: list[dict[str, Any]] = []
    for identity, info in sorted(grouped.items(), key=lambda item: item[1]["source"].casefold()):
        # Aggregate health across all of the source's apps.
        total = 0
        reachable = 0
        latencies: list[int] = []
        sample_size = 0
        for slug in info["apps"]:
            app_state = state.get(slug) if isinstance(state.get(slug), dict) else state
            history_total, history_reachable, avg_latency = _health_window(app_state)
            sample_size += history_total
            total += history_total
            reachable += history_reachable
            if avg_latency is not None:
                latencies.append(int(avg_latency))
        # Use the most recent health document for current reachability.
        currently_reachable = 0
        currently_total = 0
        for slug in info["apps"]:
            item = health_by_slug.get(slug) or {}
            currently_total += 1
            if item.get("downloadReachable") is True:
                currently_reachable += 1
        uptime = reachable / total if total else (currently_reachable / currently_total if currently_total else 0.0)
        avg_latency = sum(latencies) / len(latencies) if latencies else None
        # Update frequency: average over the source's apps.
        deltas = [_update_frequency(state, slug) for slug in info["apps"]]
        avg_delta = sum(d for d in deltas if d > 0) / max(1, sum(1 for d in deltas if d > 0))
        broken = sum(_broken_releases(state, slug) for slug in info["apps"])
        score = _score_source(
            uptime=uptime,
            avg_delta=avg_delta,
            broken=broken,
            sample_size=sample_size,
        )
        sources.append(
            {
                "id": identity,
                "source": info["source"],
                "publisher": info["publisher"],
                "homepage": info["homepage"],
                "apps": info["apps"],
                "score": score,
                "level": _level_for(score),
                "metrics": {
                    "uptime": round(uptime * 100, 2),
                    "probes": total,
                    "averageLatencyMs": round(avg_latency, 1) if avg_latency is not None else None,
                    "averageUpdateGapDays": round(avg_delta, 1) if avg_delta else None,
                    "brokenReleases": broken,
                    "currentlyReachable": f"{currently_reachable}/{currently_total}",
                },
            }
        )
    sources.sort(key=lambda item: (item["score"], item["source"].casefold()), reverse=True)

    return {
        "schemaVersion": REPUTATION_SCHEMA_VERSION,
        "generatedAt": today(),
        "count": len(sources),
        "levels": list(LEVELS),
        "windowDays": WINDOW_DAYS,
        "sources": sources,
    }
