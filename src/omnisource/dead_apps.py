"""Dead-app detection (Phase 8) and release-removal accounting.

Automatically classifies every app from pipeline state:

* no update for **90** days    → ``warning``
* no update for **180** days   → ``stale``
* no update for **365** days   → ``archived``
* a previously published release was **genuinely removed upstream** →
  ``critical`` (the sync stage records this in ``state[slug].removedReleases``)

Only a real takedown counts as a removal: upstream publishing *nothing* for the
app, or rolling **back** to an older version than the one that disappeared.
Two routine events are explicitly *not* removals, because treating them as such
published healthy apps as critical:

* an ordinary version bump — the previous newest release is superseded, which
  is what every release does;
* a same-version asset swap (a provider failover / republished build), where
  the version string did not change but the download URL did. Those are
  recorded separately as ``replaced`` and never flag the app.

Rendered as ``feeds/dead_apps.json``. The classification is a *recommendation
board*, not an automatic delisting: apps keep their feeds unless a maintainer
marks them deprecated in ``catalog.json``.
"""

from __future__ import annotations

from typing import Any

from omnisource.domain import Catalog, today
from omnisource.utils.dates import days_since
from omnisource.utils.versioning import compare_versions

DEAD_APPS_SCHEMA_VERSION = 1

THRESHOLDS = {"warning": 90, "stale": 180, "archived": 365}
CLASSIFICATIONS = ("healthy", "warning", "stale", "archived", "critical")

#: ``release_change`` kinds. ``removed`` is the only one that means "the
#: upstream took a release away"; the others are informational.
REMOVAL_KINDS = ("removed", "replaced", "superseded")


def classify_age(days: int, *, warning: int = 90, stale: int = 180, archived: int = 365) -> str:
    if days >= archived:
        return "archived"
    if days >= stale:
        return "stale"
    if days >= warning:
        return "warning"
    return "healthy"


def newest_version_entry(versions: Any) -> dict[str, Any]:
    """The newest entry of a ``state[slug]["versions"]`` list (``{}`` if none).

    The published order is newest-first; the comparison is still made against
    the maximum version so a mis-ordered list can never invent a rollback.
    """
    if not isinstance(versions, list):
        return {}
    entries = [entry for entry in versions if isinstance(entry, dict)]
    if not entries:
        return {}
    newest = entries[0]
    newest_value = str(newest.get("version") or "")
    for entry in entries[1:]:
        value = str(entry.get("version") or "")
        if value and compare_versions(value, newest_value) > 0:
            newest, newest_value = entry, value
    return newest


def is_genuine_removal(removed_version: str, newest_version: str) -> bool:
    """Is a recorded removal still a takedown, given what upstream offers now?

    True when upstream publishes no version at all, or when the current newest
    version is *older* than the removed one (a rollback). A version that has
    simply been superseded by a newer one is not a removal.
    """
    if not newest_version:
        return True
    if not removed_version:
        return False
    return compare_versions(removed_version, newest_version) > 0


def release_change(
    previous_latest: dict[str, Any] | None,
    versions: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    """Classify how an app's upstream publication changed between two syncs.

    Pure function shared by the sync stage (which persists the result) and the
    tests. Returns ``None`` when the previously newest release is still offered
    under the same URL, otherwise one of:

    ``removed``     upstream no longer offers that release at all — either the
                    app publishes nothing now, or it rolled back to an older
                    version. This is the only kind the dead-app engine treats
                    as critical.
    ``replaced``    same version string, different download URL: a republished
                    build or a provider failover. Informational.
    ``superseded``  a newer version is published. Informational (and identical
                    to the update-history entry the same sync records).
    """
    if not isinstance(previous_latest, dict):
        return None
    previous_version = str(previous_latest.get("version") or "")
    if not previous_version:
        return None
    previous_url = str(previous_latest.get("downloadURL") or "")

    current = [entry for entry in (versions or []) if isinstance(entry, dict)]
    keys = {(str(entry.get("version") or ""), str(entry.get("downloadURL") or "")) for entry in current}
    if (previous_version, previous_url) in keys:
        return None  # still offered unchanged

    newest = newest_version_entry(current)
    newest_version = str(newest.get("version") or "")
    record: dict[str, Any] = {
        "version": previous_version,
        "downloadURL": previous_url,
        "at": today(),
    }
    if is_genuine_removal(previous_version, newest_version):
        return {
            **record,
            "kind": "removed",
            "reason": "upstream no longer publishes this release",
        }
    if previous_version == newest_version:
        return {
            **record,
            "kind": "replaced",
            "reason": f"republished under a new URL (still version {newest_version})",
        }
    return {
        **record,
        "kind": "superseded",
        "reason": f"superseded by {newest_version}",
    }


def _records(app_state: dict[str, Any], key: str) -> list[dict[str, Any]]:
    raw = app_state.get(key)
    return [item for item in raw if isinstance(item, dict)] if isinstance(raw, list) else []


def active_removals(app_state: dict[str, Any]) -> list[dict[str, Any]]:
    """Removal records that still describe a takedown of the *current* state.

    Records written by an older build (before removals were distinguished from
    routine supersession) are filtered here rather than trusted, so a stale
    ``removedReleases`` entry can never publish a healthy app as critical.
    """
    newest_version = str(newest_version_entry(app_state.get("versions")).get("version") or "")
    return [
        record
        for record in _records(app_state, "removedReleases")
        if is_genuine_removal(str(record.get("version") or ""), newest_version)
    ]


def superseded_releases(app_state: dict[str, Any]) -> list[dict[str, Any]]:
    """Informational records: releases republished in place under a new URL."""
    return _records(app_state, "replacedReleases") + _records(app_state, "supersededReleases")


def prune_superseded_removals(state: dict[str, Any]) -> int:
    """Self-heal state: demote removal records that are no longer takedowns.

    Called by the build stage so a state.json written by an older build (or by
    a sync that saw an ordinary version bump) stops carrying false criticals.
    The records are preserved under ``supersededReleases`` for transparency.
    Returns the number of records migrated.
    """
    migrated = 0
    for entry in state.values():
        if not isinstance(entry, dict):
            continue
        removed = _records(entry, "removedReleases")
        if not removed:
            continue
        newest_version = str(newest_version_entry(entry.get("versions")).get("version") or "")
        keep = [record for record in removed if is_genuine_removal(str(record.get("version") or ""), newest_version)]
        demoted = [record for record in removed if record not in keep]
        if not demoted:
            continue
        for record in demoted:
            record.setdefault("kind", "superseded")
            record.setdefault("demotedAt", today())
        entry["supersededReleases"] = (superseded_releases(entry) + demoted)[-10:]
        migrated += len(demoted)
        if keep:
            entry["removedReleases"] = keep
        else:
            entry.pop("removedReleases", None)
    return migrated


def classify_app(
    app: Any,
    app_state: dict[str, Any],
    *,
    today_iso: str | None = None,
) -> dict[str, Any]:
    """Classification record for one app."""
    newest_entry = newest_version_entry(app_state.get("versions"))
    last_update = str(newest_entry.get("date") or "")
    removed = active_removals(app_state)
    replaced = superseded_releases(app_state)

    days = days_since(last_update, today_iso=today_iso or today()) if last_update else 3650

    reasons: list[str] = []
    classification = "healthy"
    if removed:
        classification = "critical"
        versions_removed = ", ".join(str(item.get("version") or "?") for item in removed[:3])
        reasons.append(f"removed upstream release(s): {versions_removed}")
    age = classify_age(days)
    if age != "healthy":
        if classification == "healthy":
            classification = age
        reasons.append(f"no update for {days} days (threshold {THRESHOLDS.get(age, 365)})")
    if replaced:
        reasons.append(f"{len(replaced)} release(s) republished in place (same version, new URL)")

    return {
        "slug": app.slug,
        "name": app.name,
        "lastUpdate": last_update,
        "daysSinceUpdate": days,
        "classification": classification,
        "removedReleases": len(removed),
        "replacedReleases": len(replaced),
        "reasons": reasons,
    }


def build_dead_apps_doc(catalog: Catalog, state: dict[str, Any], *, today_iso: str | None = None) -> dict[str, Any]:
    """Render ``feeds/dead_apps.json``."""
    entries = []
    for app in catalog.apps:
        app_state = state.get(app.slug) if isinstance(state.get(app.slug), dict) else {}
        entries.append(classify_app(app, app_state, today_iso=today_iso))

    summary = dict.fromkeys(("warning", "stale", "archived", "critical"), 0)
    for entry in entries:
        if entry["classification"] in summary:
            summary[entry["classification"]] += 1

    severity_order = {"critical": 0, "archived": 1, "stale": 2, "warning": 3}
    dead = [entry for entry in entries if entry["classification"] != "healthy"]
    dead.sort(key=lambda entry: (severity_order[entry["classification"]], entry["slug"]))
    return {
        "schemaVersion": DEAD_APPS_SCHEMA_VERSION,
        "generatedAt": today_iso or today(),
        "thresholds": dict(THRESHOLDS),
        "count": len(dead),
        "summary": summary,
        "deadApps": dead,
        "apps": entries,
    }
