"""Advanced application search: fuzzy matching, ranking, filters, sorting.

The website's client-side engine (``src/js/search-engine.js``) handles
interactive search. This module is its server-side twin, used by API v3
(``/api/search``), the ``search_apps.py`` CLI and the analytics jobs:

* multi-field matching (name, bundle ID, developer, source, category, tags);
* fuzzy matching via :mod:`difflib` with a configurable threshold;
* weighted relevance ranking with exact/prefix bonuses;
* filters (category, developer, source, verification) and sorting
  (relevance, name, updated, version).

Pure and offline.
"""

from __future__ import annotations

import difflib
import re
from typing import Any

FIELD_WEIGHTS = {
    "name": 5.0,
    "bundleIdentifier": 4.0,
    "developerName": 3.0,
    "source": 2.0,
    "category": 2.0,
    "tags": 2.0,
    "subtitle": 1.5,
    "localizedDescription": 1.0,
}

DEFAULT_THRESHOLD = 0.55
DEFAULT_LIMIT = 25
MAX_LIMIT = 100

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: Any) -> list[str]:
    """Lowercase alphanumeric tokens of ``text``."""
    if not isinstance(text, str):
        return []
    return _TOKEN_RE.findall(text.lower())


def fuzzy_score(query: str, text: str) -> float:
    """Similarity of ``query`` to ``text`` in 0..1 (1 = exact/prefix).

    Short tokens (<= 4 chars) only match exactly / by prefix / substring:
    edit-distance fuzz on tiny strings over-matches (``demo`` ~ ``com``).
    """
    left, right = query.strip().lower(), text.strip().lower()
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    if right.startswith(left):
        return 0.95
    if left in right:
        return 0.85
    if len(left) <= 4:
        return 0.0
    best = max(
        (difflib.SequenceMatcher(None, left, token).ratio() for token in tokenize(right)),
        default=0.0,
    )
    whole = difflib.SequenceMatcher(None, left, right).ratio()
    return max(best, whole)


def _field_text(app: dict[str, Any], field: str) -> str:
    value = app.get(field)
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    omni = app.get("omnisource")
    if field == "source" and isinstance(omni, dict):
        value = value or omni.get("source") or omni.get("upstream") or ""
    return str(value or "")


def score_app(app: dict[str, Any], query: str) -> float:
    """Weighted relevance score of one app for ``query``.

    AND semantics: every query token must clear the threshold in at least
    one field, otherwise the app does not match at all.
    """
    tokens = tokenize(query)
    if not tokens:
        return 0.0
    total = 0.0
    for token in tokens:
        best = 0.0
        for field, weight in FIELD_WEIGHTS.items():
            similarity = fuzzy_score(token, _field_text(app, field))
            if similarity >= DEFAULT_THRESHOLD:
                best = max(best, similarity * weight)
        if not best:
            return 0.0
        total += best
    return round(total / len(tokens), 4)


def matches_filters(app: dict[str, Any], filters: dict[str, Any]) -> bool:
    """True when ``app`` satisfies every active filter."""
    for key, want in filters.items():
        if want in (None, "", []):
            continue
        if key == "category":
            if str(app.get("category", "")).lower() != str(want).lower():
                return False
        elif key == "developer":
            if str(want).lower() not in str(app.get("developerName", "")).lower():
                return False
        elif key == "source":
            blob = f"{app.get('source', '')} {(_field_text(app, 'source'))}".lower()
            if str(want).lower() not in blob:
                return False
        elif key == "tag":
            tags = app.get("tags", [])
            haystack = " ".join(str(item) for item in tags).lower() if isinstance(tags, list) else ""
            if str(want).lower() not in haystack:
                return False
        elif key == "verified":
            verification = app.get("verification")
            status = verification.get("status", "") if isinstance(verification, dict) else ""
            is_verified = status in ("verified", "official") or bool(app.get("verified"))
            if bool(want) != is_verified:
                return False
    return True


def _sort_key(app: dict[str, Any], sort: str) -> Any:
    if sort == "name":
        return str(app.get("name", "")).lower()
    if sort == "updated":
        return str(app.get("versionDate", ""))
    if sort == "version":
        return str(app.get("version", ""))
    return -(app.get("_score", 0.0))


def search(
    apps: list[dict[str, Any]],
    query: str,
    *,
    filters: dict[str, Any] | None = None,
    sort: str = "relevance",
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> dict[str, Any]:
    """Full search: filter → score → sort → paginate."""
    active = {key: value for key, value in (filters or {}).items() if value not in (None, "", [])}
    candidates = [app for app in apps if isinstance(app, dict) and matches_filters(app, active)]
    threshold = DEFAULT_THRESHOLD if tokenize(query) else 0.0
    scored: list[dict[str, Any]] = []
    for app in candidates:
        score = score_app(app, query) if tokenize(query) else 1.0
        if score >= threshold:
            hit = dict(app)
            hit["_score"] = score
            scored.append(hit)
    reverse = sort in ("relevance", "updated", "version")
    scored.sort(key=lambda item: _sort_key(item, sort), reverse=(sort != "name" and reverse))
    if sort == "relevance":
        scored.sort(key=lambda item: -item["_score"])
    limit = max(1, min(MAX_LIMIT, int(limit or DEFAULT_LIMIT)))
    offset = max(0, int(offset or 0))
    page = scored[offset : offset + limit]
    return {
        "query": query,
        "filters": active,
        "sort": sort,
        "total": len(scored),
        "limit": limit,
        "offset": offset,
        "results": page,
    }
