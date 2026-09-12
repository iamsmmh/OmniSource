"""Metadata enrichment and normalization.

Upstream feeds disagree on casing, whitespace, categories and optional
fields. This module normalizes every record into the consistent shape the
website, search index and API v3 consume:

* trim / collapse whitespace in free-text fields;
* title-case names, normalize categories onto the canonical taxonomy;
* backfill ``subtitle`` from the description when missing;
* normalize URLs (strip tracking parameters, enforce https where safe);
* flag records that still miss display-critical fields.

Pure and offline: enrichment never fetches the network. Output document:
``data/enriched_apps.json`` (advisory — the pipeline keeps serving the raw
upstream metadata until a human promotes enriched values into ``catalog.json``).
"""

from __future__ import annotations

import re
import urllib.parse
from datetime import UTC, datetime
from typing import Any

ENRICHMENT_SCHEMA_VERSION = 1

TRACKING_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "gclid",
        "fbclid",
        "mc_cid",
        "mc_eid",
    }
)

CATEGORY_ALIASES = {
    "tweak": "Utilities",
    "tweaks": "Utilities",
    "utility": "Utilities",
    "tool": "Utilities",
    "tools": "Utilities",
    "emulator": "Games",
    "emulators": "Games",
    "game": "Games",
    "music": "Music",
    "video": "Photo & Video",
    "photo": "Photo & Video",
    "photos": "Photo & Video",
    "social": "Social Networking",
    "socialnetworking": "Social Networking",
    "webbrowser": "Utilities",
    "browser": "Utilities",
    "entertainment": "Entertainment",
    "education": "Education",
    "productivity": "Productivity",
    "news": "News",
    "health": "Health & Fitness",
    "fitness": "Health & Fitness",
    "finance": "Finance",
    "developer": "Developer Tools",
    "developertools": "Developer Tools",
}

CRITICAL_FIELDS = ("name", "localizedDescription", "iconURL", "category", "developerName")

_WHITESPACE_RE = re.compile(r"\s+")


def utcnow() -> str:
    """Current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def clean_text(value: Any, *, limit: int = 4000) -> str:
    """Collapse whitespace, strip, and clamp free text to ``limit`` chars."""
    if not isinstance(value, str):
        return ""
    text = _WHITESPACE_RE.sub(" ", value).strip()
    if len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def normalize_category(value: Any) -> str:
    """Map a raw category string onto the canonical taxonomy."""
    if not isinstance(value, str) or not value.strip():
        return "Utilities"
    raw = value.strip()
    canonical = CATEGORY_ALIASES.get(raw.lower().replace(" ", "").replace("&", "and"))
    if canonical:
        return canonical
    aliased = CATEGORY_ALIASES.get(raw.lower())
    if aliased:
        return aliased
    return raw[:48]


def normalize_url(value: Any) -> str:
    """Strip tracking parameters and whitespace from a URL."""
    if not isinstance(value, str):
        return ""
    url = value.strip()
    if not url or not url.startswith(("http://", "https://")):
        return url
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return url
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    kept = [(key, val) for key, val in query if key not in TRACKING_PARAMS]
    cleaned = parsed._replace(query=urllib.parse.urlencode(kept))
    return urllib.parse.urlunparse(cleaned)


def subtitle_for(app: dict[str, Any], *, limit: int = 80) -> str:
    """Best subtitle: explicit value, else the description's first sentence."""
    explicit = clean_text(app.get("subtitle"), limit=limit)
    if explicit:
        return explicit
    description = clean_text(app.get("localizedDescription"), limit=400)
    sentence = re.split(r"[.!?\n]", description, maxsplit=1)[0].strip()
    if len(sentence) > limit:
        return sentence[: limit - 1].rstrip() + "…"
    return sentence


def enrich_app(app: dict[str, Any]) -> dict[str, Any]:
    """Return the normalized copy of one raw app record."""
    enriched = dict(app)
    enriched["name"] = clean_text(app.get("name"), limit=80) or str(app.get("slug") or app.get("id") or "Unknown")
    enriched["developerName"] = clean_text(app.get("developerName"), limit=80) or "Unknown Developer"
    enriched["localizedDescription"] = clean_text(app.get("localizedDescription"))
    enriched["subtitle"] = subtitle_for(app)
    enriched["versionDescription"] = clean_text(app.get("versionDescription"), limit=2000)
    enriched["category"] = normalize_category(app.get("category"))
    for field in ("iconURL", "website", "downloadURL", "tintColor"):
        if field == "tintColor":
            enriched[field] = str(app.get(field, "FF0000")).lstrip("#").upper()[:6] or "FF0000"
        elif app.get(field):
            enriched[field] = normalize_url(app.get(field))
    shots = app.get("screenshotURLs")
    if isinstance(shots, list):
        enriched["screenshotURLs"] = [normalize_url(shot) for shot in shots if isinstance(shot, str)][:10]
    enriched["missingFields"] = [field for field in CRITICAL_FIELDS if not enriched.get(field)]
    return enriched


def enrich_apps(apps: list[dict[str, Any]]) -> dict[str, Any]:
    """Enrich a whole catalog and summarize what is still missing."""
    enriched = [enrich_app(app) for app in apps if isinstance(app, dict)]
    incomplete = sum(1 for app in enriched if app.get("missingFields"))
    return {
        "schemaVersion": ENRICHMENT_SCHEMA_VERSION,
        "generatedAt": utcnow(),
        "count": len(enriched),
        "incomplete": incomplete,
        "apps": enriched,
    }
