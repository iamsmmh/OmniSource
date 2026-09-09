"""Duplicate detection engine.

Sideloading clients replace an installed app whose ``bundleIdentifier``
matches, so an app appearing in several OmniSource feeds is either a
deliberate alternative (several YouTube tweaks) or a mistake. This module
surfaces both cases with an actionable recommendation.

Signals (in order of strength):

1. ``bundle-id``    — two apps share a bundle identifier.
2. ``similar-name`` — normalized names are highly similar (or one contains the
   other) and the apps are not already covered by signal 1.
3. ``same-developer`` — same developer name *and* same category (weak signal;
   only reported when neither of the stronger signals matched).

Groups that overlap are merged, and the recommended source is the app inside
the group with the newest version (tie-broken by release date), which is the
behaviour a user typically wants when several builds exist for one app.

Rendered as ``feeds/duplicates.json``; the website shows the recommendations
as warnings on the affected app pages.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from omnisource.constants import VALID_STATUSES
from omnisource.discovery import newest_version, source_label
from omnisource.domain import Catalog, today
from omnisource.utils.versioning import compare_versions

DUPLICATES_SCHEMA_VERSION = 1
NAME_SIMILARITY = 0.72
TOKEN_RE = re.compile(r"[^a-z0-9]+")


def _normalize(name: str) -> str:
    return TOKEN_RE.sub("", str(name or "").casefold())


def _similar(left: str, right: str) -> bool:
    a, b = _normalize(left), _normalize(right)
    if len(a) < 3 or len(b) < 3:
        return False
    if a == b:
        return True
    if min(len(a), len(b)) >= 5 and (a in b or b in a):
        return True
    return SequenceMatcher(None, a, b).ratio() >= NAME_SIMILARITY


def _app_record(catalog: Catalog, app: Any, state: dict[str, Any]) -> dict[str, Any]:
    newest = newest_version(state, app.slug)
    return {
        "app": app.slug,
        "name": app.name,
        "version": str(newest.get("version") or ""),
        "releaseDate": str(newest.get("date") or ""),
        "source": source_label(app),
        "developer": app.developer,
        "category": app.category,
        "status": app.status if app.status in VALID_STATUSES else "stable",
        "downloadURL": str(newest.get("downloadURL") or ""),
    }


def _recommend(members: list[dict[str, Any]]) -> dict[str, Any]:
    """Pick the newest version inside a duplicate group."""
    best = members[0]
    for member in members[1:]:
        order = compare_versions(member["version"], best["version"])
        if order > 0 or (order == 0 and member["releaseDate"] > best["releaseDate"]):
            best = member
    reason = (
        f"Newest version available ({best['version'] or 'unversioned'}, "
        f"released {best['releaseDate'] or 'unknown date'})"
    )
    return {
        "app": best["app"],
        "name": best["name"],
        "version": best["version"],
        "reason": reason,
    }


def build_duplicates_doc(catalog: Catalog, state: dict[str, Any]) -> dict[str, Any]:
    """Detect duplicate groups and render ``duplicates.json``."""
    records = [_app_record(catalog, app, state) for app in catalog.apps]

    # Union-find over app indices; every signal merges its group.
    parent = list(range(len(records)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    bundle_groups: dict[str, list[int]] = {}
    for index in range(len(records)):
        bundle = catalog.apps[index].bundle_id
        if bundle:
            bundle_groups.setdefault(bundle, []).append(index)

    reasons: dict[int, set[str]] = {index: set() for index in range(len(records))}
    for bundle, indexes in bundle_groups.items():
        if len(indexes) > 1:
            reason = f"{len(indexes)} apps share bundle identifier '{bundle}'"
            for index in indexes:
                reasons[index].add(reason)
            for index in indexes[1:]:
                union(indexes[0], index)

    # A shared bundle identifier is the only signal strong enough to form a
    # duplicate group on its own: sideloading clients replace an installed app
    # whose bundle matches, so those are genuinely "the same app" published in
    # several feeds. Similar names / same developer only *corroborate* those
    # groups — the iNKillerPlus / TTKillerPlus family is similar by name but
    # is two different apps (Instagram vs TikTok), so a name-only match must
    # never recommend one over the other.
    linked = [find(index) for index in range(len(records))]
    for left in range(len(records)):
        for right in range(left + 1, len(records)):
            if linked[left] != linked[right]:
                continue
            if records[left]["category"] == records[right]["category"] and _similar(
                records[left]["name"], records[right]["name"]
            ):
                reason = f"similar names ({records[left]['name']} / {records[right]['name']})"
                reasons[left].add(reason)
                reasons[right].add(reason)
            same_developer = (
                records[left]["developer"]
                and records[left]["developer"] == records[right]["developer"]
                and records[left]["category"] == records[right]["category"]
            )
            if same_developer:
                reason = f"same developer ({records[left]['developer']}) and category"
                reasons[left].add(reason)
                reasons[right].add(reason)

    groups: dict[int, list[int]] = {}
    for index in range(len(records)):
        groups.setdefault(find(index), []).append(index)

    output_groups: list[dict[str, Any]] = []
    for indexes in groups.values():
        if len(indexes) < 2:
            continue
        members = [records[index] for index in sorted(indexes)]
        shared_bundles = sorted({catalog.apps[index].bundle_id for index in indexes if catalog.apps[index].bundle_id})
        group_reasons: list[str] = []
        for index in sorted(indexes):
            group_reasons.extend(reasons[index])
        reasons_dedup = sorted(set(group_reasons))
        has_bundle_reason = any("bundle identifier" in r for r in reasons_dedup)
        has_name_reason = any("similar names" in r for r in reasons_dedup)
        if has_bundle_reason and has_name_reason:
            group_type = "bundle-id+similar-name"
        elif has_bundle_reason:
            group_type = "bundle-id"
        else:
            group_type = "unknown"
        recommended = _recommend(members)
        output_groups.append(
            {
                "key": " | ".join(shared_bundles)
                if shared_bundles
                else " | ".join(sorted(_normalize(member["name"]) for member in members)),
                "type": group_type,
                "reason": " · ".join(reasons_dedup),
                "apps": members,
                "recommended": recommended,
                "replacementRisk": bool(shared_bundles),
            }
        )

    output_groups.sort(key=lambda group: (-len(group["apps"]), str(group["key"])))
    duplicated = sum(len(group["apps"]) for group in output_groups)
    return {
        "schemaVersion": DUPLICATES_SCHEMA_VERSION,
        "generatedAt": today(),
        "count": len(output_groups),
        "appsAffected": duplicated,
        "groups": output_groups,
        "bySlug": {
            record["app"]: {
                "groupKey": group["key"],
                "type": group["type"],
                "recommended": group["recommended"],
                "reason": group["reason"],
            }
            for group in output_groups
            for record in group["apps"]
        },
    }


def group_for_app(duplicates_doc: dict[str, Any], slug: str) -> dict[str, Any] | None:
    """Return the duplicate-group info attached to ``slug``, if any."""
    by_slug = duplicates_doc.get("bySlug", {})
    item = by_slug.get(slug) if isinstance(by_slug, dict) else None
    return item if isinstance(item, dict) and item.get("groupKey") is not None else None
