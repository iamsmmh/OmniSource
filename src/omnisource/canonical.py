"""Canonical app database (cross-source deduplication).

The same iOS app often appears in several upstream feeds under slightly
different metadata. This module merges those duplicates into one canonical
record per real-world app.

Matching keys, in priority order:

1. ``bundleIdentifier`` — the iOS identity; strongest signal.
2. ``appID`` / ``id`` — explicit feed-level identifiers.
3. Repository URL — same ``github.com/owner/repo`` upstream.
4. Release / download URL host+path — same published binary.

The merged record keeps the union of sources and versions so provenance is
never lost. Output document: ``data/canonical_apps.json``.
"""

from __future__ import annotations

import urllib.parse
from datetime import UTC, datetime
from typing import Any

CANONICAL_SCHEMA_VERSION = 1


def utcnow() -> str:
    """Current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _repo_key(url: Any) -> str:
    if not isinstance(url, str) or "github.com" not in url.lower():
        return ""
    try:
        parts = [segment for segment in urllib.parse.urlparse(url).path.strip("/").split("/") if segment]
    except ValueError:
        return ""
    if len(parts) >= 2:
        return f"github:{parts[0].lower()}/{parts[1].lower()}"
    return ""


def match_keys(app: dict[str, Any]) -> list[str]:
    """Return the ordered deduplication keys for one app record."""
    keys: list[str] = []
    bundle = str(app.get("bundleIdentifier", "") or "").strip()
    if bundle:
        keys.append(f"bundle:{bundle}")
    for field in ("appID", "appIdentifier", "applicationIdentifier", "identifier", "id", "slug"):
        value = str(app.get(field, "") or "").strip()
        if value:
            keys.append(f"{field}:{value.casefold()}")
    omni = app.get("omnisource")
    candidates: list[Any] = []
    if isinstance(omni, dict):
        candidates.extend((omni.get("upstream"), omni.get("sourceURL"), omni.get("source_url"), omni.get("repository")))
    candidates.extend(
        app.get(field)
        for field in (
            "website",
            "sourceURL",
            "source_url",
            "repositoryURL",
            "repository_url",
            "repositoryUrl",
            "releaseURL",
            "release_url",
            "releaseUrl",
        )
    )
    for candidate in candidates:
        repo = _repo_key(candidate)
        if repo and repo not in keys:
            keys.append(repo)
        if isinstance(candidate, str) and candidate.startswith("https://"):
            try:
                parsed_candidate = urllib.parse.urlparse(candidate)
            except ValueError:
                parsed_candidate = None
            if parsed_candidate and parsed_candidate.hostname:
                url_key = f"url:{parsed_candidate.hostname.casefold()}{parsed_candidate.path.rstrip('/')}"
                if url_key not in keys:
                    keys.append(url_key)
    download = str(app.get("downloadURL", "") or "")
    if download.startswith("https://"):
        try:
            parsed = urllib.parse.urlparse(download)
        except ValueError:
            parsed = None
        if parsed and parsed.hostname:
            keys.append(f"binary:{parsed.hostname.lower()}{parsed.path}")
    return keys


def _prefer(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return values[-1] if values else None


def merge_group(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge duplicate records into one canonical app record."""
    ordered = sorted(records, key=lambda item: str(item.get("versionDate", "")))
    base = dict(ordered[-1]) if ordered else {}
    sources: list[str] = []
    versions: dict[str, dict[str, Any]] = {}
    for record in ordered:
        for field in ("source", "sourceURL", "feedURL"):
            value = record.get(field)
            if isinstance(value, str) and value and value not in sources:
                sources.append(value)
        omni = record.get("omnisource")
        if isinstance(omni, dict):
            for field in ("sourceURL", "upstream"):
                value = omni.get(field)
                if isinstance(value, str) and value and value not in sources:
                    sources.append(value)
        for version in record.get("versions", []) or []:
            if isinstance(version, dict) and version.get("version"):
                versions.setdefault(str(version["version"]), dict(version))
    repository_urls = sorted(
        {
            str(record.get(field) or "")
            for record in ordered
            for field in ("sourceURL", "source_url", "repositoryURL", "repository_url", "releaseURL", "release_url")
            if str(record.get(field) or "").startswith("https://")
        }
    )
    canonical = {
        "id": _prefer(base.get("slug"), base.get("id"), base.get("bundleIdentifier")),
        "name": base.get("name", ""),
        "bundleIdentifier": base.get("bundleIdentifier", ""),
        "developerName": base.get("developerName", ""),
        "category": base.get("category", ""),
        "version": base.get("version", ""),
        "versionDate": base.get("versionDate", ""),
        "downloadURL": base.get("downloadURL", ""),
        "size": base.get("size", 0),
        "iconURL": base.get("iconURL", ""),
        "matchKeys": match_keys(base),
        "repositoryURLs": repository_urls,
        "sources": sources,
        "sourceCount": len(sources),
        "duplicates": len(records),
        "versions": [versions[key] for key in sorted(versions, reverse=True)],
    }
    return canonical


def group_duplicates(apps: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Group app records that describe the same real-world app."""
    groups: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    for app in apps:
        keys = match_keys(app if isinstance(app, dict) else {})
        placed = next((key for key in keys if key in groups), "")
        if not placed:
            placed = keys[0] if keys else f"row:{len(order)}"
            groups[placed] = []
            order.append(placed)
        groups[placed].append(app)
        for key in keys[1:]:
            groups.setdefault(key, groups[placed])
    seen: set[int] = set()
    result: list[list[dict[str, Any]]] = []
    for key in order:
        group = groups[key]
        if id(group) not in seen:
            seen.add(id(group))
            result.append(group)
    return result


def build_canonical(apps: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the canonical app database document from raw app records."""
    records = [app for app in apps if isinstance(app, dict)]
    groups = group_duplicates(records)
    canonical = [merge_group(group) for group in groups]
    canonical.sort(key=lambda item: str(item.get("name", "")).lower())
    return {
        "schemaVersion": CANONICAL_SCHEMA_VERSION,
        "generatedAt": utcnow(),
        "count": len(canonical),
        "inputRecords": len(records),
        "mergedDuplicates": max(0, len(records) - len(canonical)),
        "apps": canonical,
    }


def find_duplicates(apps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return the groups that contain more than one record (audit view)."""
    dupes: list[dict[str, Any]] = []
    for group in group_duplicates([app for app in apps if isinstance(app, dict)]):
        if len(group) > 1:
            names = sorted({str(item.get("name", "?")) for item in group})
            dupes.append({"key": (match_keys(group[0]) or ["?"])[0], "count": len(group), "names": names})
    return sorted(dupes, key=lambda item: (-item["count"], item["key"]))
