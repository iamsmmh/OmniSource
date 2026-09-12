"""Source reputation labels for the autonomous pipeline.

:mod:`omnisource.reputation` computes the explainable 0..100 score from six
signals (JSON validity, uptime, update frequency, broken links, release
activity, metadata completeness). This module maps that score onto the
five public trust statuses consumed by the website, the monitoring alerts
and the discovery quarantine:

* ``verified``   — score >= 85
* ``trusted``    — score >= 70
* ``good``       — score >= 50
* ``warning``    — score >= 25
* ``untrusted``  — score < 25 (quarantined: never auto-published)

Output document: ``data/source_reputation.json``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

REPUTATION_SCHEMA_VERSION = 1

STATUS_BANDS = (
    (85, "verified"),
    (70, "trusted"),
    (50, "good"),
    (25, "warning"),
    (0, "untrusted"),
)

QUARANTINE_THRESHOLD = 25


def utcnow() -> str:
    """Current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def label_for_score(score: Any) -> str:
    """Map a 0..100 reputation score onto its public status label."""
    try:
        value = float(score)
    except (TypeError, ValueError):
        return "untrusted"
    for threshold, label in STATUS_BANDS:
        if value >= threshold:
            return label
    return "untrusted"


def summarize_sources(sources: list[dict[str, Any]]) -> dict[str, int]:
    """Count sources per status label."""
    summary = {label: 0 for _, label in STATUS_BANDS}
    for source in sources:
        summary[label_for_score(source.get("score", 0))] += 1
    return summary


def build_labels(
    reputation_doc: dict[str, Any],
    status_doc: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the ``data/source_reputation.json`` document."""
    raw_sources = reputation_doc.get("sources", [])
    if not isinstance(raw_sources, list):
        raw_sources = []
    health_by_id: dict[str, str] = {}
    if isinstance(status_doc, dict):
        for entry in status_doc.get("sources", []) or []:
            if isinstance(entry, dict) and entry.get("id"):
                health_by_id[str(entry["id"])] = str(entry.get("status", "unknown"))
    sources: list[dict[str, Any]] = []
    for entry in raw_sources:
        if not isinstance(entry, dict):
            continue
        score = entry.get("score", 0)
        sources.append(
            {
                "id": entry.get("id", ""),
                "source": entry.get("source", ""),
                "score": score,
                "status": label_for_score(score),
                "legacy_level": entry.get("level", ""),
                "legacy_status": entry.get("status", ""),
                "apps": entry.get("apps", []),
                "lastUpdate": entry.get("lastUpdate", ""),
                "health": health_by_id.get(str(entry.get("id", "")), "unknown"),
                "metrics": entry.get("metrics", {}),
            }
        )
    sources.sort(key=lambda item: (-float(item["score"] or 0), str(item["id"])))
    summary = summarize_sources(sources)
    return {
        "schemaVersion": REPUTATION_SCHEMA_VERSION,
        "generatedAt": utcnow(),
        "count": len(sources),
        "summary": summary,
        "quarantineThreshold": QUARANTINE_THRESHOLD,
        "quarantined": [item["id"] for item in sources if item["status"] == "untrusted"],
        "sources": sources,
    }


def is_quarantined(score: Any) -> bool:
    """True when a score falls below the auto-publish bar."""
    try:
        return float(score) < QUARANTINE_THRESHOLD
    except (TypeError, ValueError):
        return True
