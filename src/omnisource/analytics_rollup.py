"""Analytics rollups: daily / weekly / monthly aggregates.

``feeds/analytics.json`` carries the live totals plus a growing ``history``
series. This module rolls that series (and the ``reports/history.json``
monitoring ledger when present) into the bounded windows the website's
Statistics page and API v3 serve:

* ``daily`` — the most recent 30 days;
* ``weekly`` — the most recent 12 ISO weeks;
* ``monthly`` — the most recent 12 calendar months.

Pure and offline. Output document: ``data/analytics_rollup.json``.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

ROLLUP_SCHEMA_VERSION = 1

DAILY_DAYS = 30
WEEKLY_WEEKS = 12
MONTHLY_MONTHS = 12


def _as_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(value[:19], fmt).date()
        except ValueError:
            continue
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _entry_date(entry: dict[str, Any]) -> date | None:
    for field in ("date", "day", "at", "generatedAt", "syncedAt"):
        parsed = _as_date(entry.get(field))
        if parsed is not None:
            return parsed
    return None


def _metrics(entry: dict[str, Any]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    candidates = [entry, entry.get("totals", {}), entry.get("summary", {})]
    for node in candidates:
        if not isinstance(node, dict):
            continue
        for key, value in node.items():
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)) and key not in metrics:
                metrics[str(key)] = float(value)
    return metrics


def normalize_history(*series: Any) -> list[dict[str, Any]]:
    """Flatten history series into ``[{date, metrics}]`` sorted by date."""
    rows: dict[str, dict[str, Any]] = {}
    for sequence in series:
        if not isinstance(sequence, list):
            continue
        for entry in sequence:
            if not isinstance(entry, dict):
                continue
            day = _entry_date(entry)
            if day is None:
                continue
            key = day.isoformat()
            merged = rows.setdefault(key, {"date": key, "metrics": {}})
            for name, value in _metrics(entry).items():
                merged["metrics"][name] = value
    return [rows[key] for key in sorted(rows)]


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for row in rows:
        for name, value in row.get("metrics", {}).items():
            totals[name] = totals.get(name, 0.0) + value
    days = max(1, len(rows))
    return {name: round(value / days, 2) for name, value in sorted(totals.items())}


def rollup_daily(rows: list[dict[str, Any]], *, days: int = DAILY_DAYS) -> list[dict[str, Any]]:
    """Most recent ``days`` of daily rows."""
    return rows[-days:]


def rollup_weekly(rows: list[dict[str, Any]], *, weeks: int = WEEKLY_WEEKS) -> list[dict[str, Any]]:
    """Group daily rows into ISO weeks (most recent ``weeks`` first)."""
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        day = _as_date(row["date"])
        if day is None:  # pragma: no cover - normalized rows always parse.
            continue
        iso_year, iso_week, _ = day.isocalendar()
        buckets.setdefault(f"{iso_year}-W{iso_week:02d}", []).append(row)
    ordered = sorted(buckets)[-weeks:]
    return [{"week": key, "days": len(buckets[key]), "averages": _aggregate(buckets[key])} for key in ordered]


def rollup_monthly(rows: list[dict[str, Any]], *, months: int = MONTHLY_MONTHS) -> list[dict[str, Any]]:
    """Group daily rows into calendar months (most recent ``months``)."""
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        buckets.setdefault(row["date"][:7], []).append(row)
    ordered = sorted(buckets)[-months:]
    return [{"month": key, "days": len(buckets[key]), "averages": _aggregate(buckets[key])} for key in ordered]


def build_rollup(
    analytics_doc: dict[str, Any] | None,
    monitoring_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the ``data/analytics_rollup.json`` document."""
    analytics_doc = analytics_doc if isinstance(analytics_doc, dict) else {}
    rows = normalize_history(analytics_doc.get("history"), monitoring_history)
    return {
        "schemaVersion": ROLLUP_SCHEMA_VERSION,
        "generatedAt": analytics_doc.get("generatedAt", ""),
        "totals": analytics_doc.get("totals", {}),
        "coverageDays": len(rows),
        "daily": rollup_daily(rows),
        "weekly": rollup_weekly(rows),
        "monthly": rollup_monthly(rows),
    }
