"""Build monitoring reports (``reports/latest.json`` + ``reports/history.json``).

Every pipeline run records a deterministic snapshot of what it built: app
totals, download reachability, sync/update counts, per-build errors and the
translation coverage that shipped. ``latest.json`` is overwritten in place;
``history.json`` keeps the last :data:`HISTORY_LIMIT` distinct builds as a
rolling ledger for trend monitoring (reachability dips, repeated sync
failures). A rebuild that changes nothing appends no row — ``generatedAt``
is derived from the data (not wall-clock), so a consecutive identical row
would carry zero information and only churn the file.

Determinism contract: both documents must be byte-identical when the same
committed state is rebuilt, because ``scripts/check_reproducible.py`` treats
them as generated artifacts. The only volatile field is ``generatedAt``,
which the checker already normalizes, and the ``history`` array, which it
normalizes wholesale (same as the analytics history). In particular the
report embeds no wall-clock durations and no ``files_changed`` counts —
a rebuild from committed state reports 0 changed files while the original
run reported N, so either value would fail the gate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from omnisource.io import write_json

HISTORY_LIMIT = 30


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def build_report(
    *,
    health_doc: dict[str, Any],
    analytics_doc: dict[str, Any],
    sync_report: Any,
    feeds_dir: Path,
) -> dict[str, Any]:
    """Assemble the deterministic per-build report document."""
    totals = health_doc.get("totals", {})
    analytics_totals = analytics_doc.get("totals", {})
    unreachable = sorted(
        str(item.get("slug", item.get("name", "?")))
        for item in health_doc.get("apps", [])
        if isinstance(item, dict) and not item.get("downloadReachable")
    )
    updates = []
    for event in getattr(sync_report, "updates", []) or []:
        updates.append(
            {
                "slug": getattr(event, "slug", None) or getattr(event, "app_id", None),
                "name": getattr(event, "name", None),
                "previousVersion": getattr(event, "previous_version", None),
                "version": getattr(event, "version", None),
                "kind": getattr(event, "kind", None),
            }
        )
    manifest = _read_json(feeds_dir / "api" / "v2" / "manifest.json") or {}
    translations = _read_json(feeds_dir / "translation-status.json") or {}
    return {
        "generatedAt": health_doc.get("generatedAt"),
        "feedVersion": manifest.get("feedVersion"),
        "apps": {
            "total": totals.get("apps", 0),
            "reachable": totals.get("reachable", 0),
            "unreachable": totals.get("unreachable", 0),
            "verified": analytics_totals.get("verifiedApps", 0),
        },
        "sync": {
            "synced": getattr(sync_report, "apps_synced", 0),
            "incrementalHits": getattr(sync_report, "apps_incremental_hit", 0),
            "updated": getattr(sync_report, "apps_updated", 0),
            "failed": getattr(sync_report, "apps_failed", 0),
            "apiRequests": getattr(sync_report, "api_requests", 0),
        },
        "unreachable": unreachable,
        "updates": updates,
        "errors": list(getattr(sync_report, "errors", []) or []),
        "translations": translations,
    }


def history_row(report: dict[str, Any]) -> dict[str, Any]:
    """Compress one build report into a single trend row."""
    return {
        "generatedAt": report.get("generatedAt"),
        "apps": report["apps"]["total"],
        "reachable": report["apps"]["reachable"],
        "verified": report["apps"]["verified"],
        "updated": report["sync"]["updated"],
        "failed": report["sync"]["failed"],
        "errors": len(report["errors"]),
    }


def append_history(history_path: Path, report: dict[str, Any]) -> dict[str, Any]:
    """Return the trimmed history document with this build's row appended.

    A row identical to the current tail is skipped: rebuilding committed
    state is then a byte-level no-op, which is what the reproducibility
    checker asserts.
    """
    doc = _read_json(history_path) or {}
    rows = doc.get("history")
    rows = list(rows) if isinstance(rows, list) else []
    row = history_row(report)
    if not rows or rows[-1] != row:
        rows.append(row)
    return {"generatedAt": report.get("generatedAt"), "history": rows[-HISTORY_LIMIT:]}


def write_reports(
    *,
    root: Path,
    feeds_dir: Path,
    health_doc: dict[str, Any],
    analytics_doc: dict[str, Any],
    sync_report: Any,
) -> list[Path]:
    """Write ``reports/latest.json`` + ``reports/history.json``.

    Returns the paths that changed on disk.
    """
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(
        health_doc=health_doc,
        analytics_doc=analytics_doc,
        sync_report=sync_report,
        feeds_dir=feeds_dir,
    )
    changed: list[Path] = []
    latest_path = reports_dir / "latest.json"
    if write_json(latest_path, report):
        changed.append(latest_path)
    history_path = reports_dir / "history.json"
    if write_json(history_path, append_history(history_path, report)):
        changed.append(history_path)
    return changed
