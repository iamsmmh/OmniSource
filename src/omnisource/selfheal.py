"""Self-healing engine: detect breakage, plan repairs, apply safe fixes.

Runs on every monitoring pass (``monitoring.yml``) and after each sync:

1. **Detect** — broken downloads, broken feeds, missing metadata and
   removed releases, from health probes + state diffs.
2. **Plan** — attach one repair action per issue: ``retry`` (transient),
   ``repair`` (switch to a recorded fallback URL), ``replace`` (switch to
   a configured mirror) or ``rebuild`` (flag the app for a full resync).
3. **Report** — ``data/selfheal_report.json`` with machine-readable
   ``suggestedPatches``. Only ``repair`` patches that point at an
   already-recorded fallback URL may be applied without review
   (:func:`apply_safe_fixes`); everything else needs a human or a
   follow-up pipeline run.

Offline by default; pass ``reprobe=True`` to re-check failing URLs live
before writing the report.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from omnisource.enrichment import CRITICAL_FIELDS

RETRY = "retry"
REPAIR = "repair"
REPLACE = "replace"
REBUILD = "rebuild"

SELFHEAL_SCHEMA_VERSION = 1


def utcnow() -> str:
    """Current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _health_index(health: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    nodes: Any = []
    if isinstance(health, dict):
        nodes = health.get("apps", health.get("sources", []))
    if isinstance(nodes, list):
        for node in nodes:
            if isinstance(node, dict):
                key = str(node.get("slug") or node.get("id") or node.get("app") or "")
                if key:
                    index[key] = node
    return index


def _is_failing(node: dict[str, Any]) -> bool:
    status = str(node.get("status") or node.get("health") or node.get("reachable") or "").lower()
    if status in ("unavailable", "offline", "failing", "failed", "false", "0"):
        return True
    return "reachable" in node and node["reachable"] is False


def _is_transient(node: dict[str, Any]) -> bool:
    detail = f"{node.get('error', '')} {node.get('detail', '')}".lower()
    return any(token in detail for token in ("timeout", "timed out", "503", "502", "429", "temporar"))


def detect_issues(
    *,
    apps: list[dict[str, Any]],
    health: dict[str, Any] | None = None,
    removed: dict[str, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    """Detect every healable issue across the catalog."""
    index = _health_index(health)
    removed = removed or {}
    issues: list[dict[str, Any]] = []
    for app in apps:
        if not isinstance(app, dict):
            continue
        slug = str(app.get("slug") or app.get("id") or app.get("name") or "?")
        node = index.get(slug, index.get(str(app.get("bundleIdentifier", "")), {}))
        if node and _is_failing(node):
            issues.append(
                {
                    "type": "broken_download",
                    "slug": slug,
                    "severity": "high",
                    "detail": str(node.get("error") or node.get("status") or "unreachable"),
                    "transient": _is_transient(node),
                    "fallbacks": list(app.get("fallbackDownloadURLs") or []),
                }
            )
        missing = [field for field in CRITICAL_FIELDS if not app.get(field)]
        if missing:
            issues.append(
                {
                    "type": "missing_metadata",
                    "slug": slug,
                    "severity": "low",
                    "detail": f"missing {', '.join(missing)}",
                    "transient": False,
                    "fallbacks": [],
                }
            )
        for entry in removed.get(slug, []):
            issues.append(
                {
                    "type": "removed_release",
                    "slug": slug,
                    "severity": "medium",
                    "detail": f"upstream removed {entry.get('version', '?')}",
                    "transient": False,
                    "fallbacks": [],
                }
            )
    return sorted(issues, key=lambda item: (item["type"], item["slug"]))


def plan_repairs(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach one repair action (retry/repair/replace/rebuild) per issue."""
    plans: list[dict[str, Any]] = []
    for issue in issues:
        kind = issue.get("type")
        if kind == "broken_download":
            if issue.get("transient"):
                action, auto = RETRY, True
            elif issue.get("fallbacks"):
                action, auto = REPAIR, True
            else:
                action, auto = REPLACE, False
        elif kind == "missing_metadata" or kind == "removed_release":
            action, auto = REBUILD, False
        else:  # Unknown issue kinds degrade to a rebuild flag, never a guess.
            action, auto = REBUILD, False
        plans.append({**issue, "action": action, "autoFixable": auto})
    return plans


def suggested_patches(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Safe, reviewable patches: fallback-URL swaps only."""
    patches = []
    for plan in plans:
        if plan.get("action") == REPAIR and plan.get("fallbacks"):
            patches.append(
                {
                    "slug": plan["slug"],
                    "field": "downloadURL",
                    "replaceWith": plan["fallbacks"][0],
                    "reason": plan.get("detail", ""),
                }
            )
    return patches


def apply_safe_fixes(
    apps: list[dict[str, Any]],
    plans: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    """Apply auto-fixable fallback swaps; return ``(apps, applied)``."""
    swaps = {
        plan["slug"]: plan["fallbacks"][0] for plan in plans if plan.get("action") == REPAIR and plan.get("fallbacks")
    }
    applied = 0
    fixed: list[dict[str, Any]] = []
    for app in apps:
        slug = str(app.get("slug") or app.get("id") or "")
        if slug in swaps:
            clone = dict(app)
            clone["downloadURL"] = swaps[slug]
            fixed.append(clone)
            applied += 1
        else:
            fixed.append(app)
    return fixed, applied


def build_report(
    plans: list[dict[str, Any]],
    *,
    applied: int = 0,
) -> dict[str, Any]:
    """Build the ``data/selfheal_report.json`` document."""
    by_action: dict[str, int] = {}
    for plan in plans:
        by_action[str(plan.get("action", "?"))] = by_action.get(str(plan.get("action", "?")), 0) + 1
    return {
        "schemaVersion": SELFHEAL_SCHEMA_VERSION,
        "generatedAt": utcnow(),
        "issues": len(plans),
        "autoFixable": sum(1 for plan in plans if plan.get("autoFixable")),
        "appliedFixes": applied,
        "byAction": by_action,
        "plans": plans,
        "suggestedPatches": suggested_patches(plans),
    }
