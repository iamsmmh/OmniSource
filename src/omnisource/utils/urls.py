"""URL normalization and safety helpers."""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit


def normalise_url(value: str) -> str:
    """Trim whitespace and fragment noise without changing query semantics."""
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if not value:
        return ""
    parsed = urlsplit(value)
    return urlunsplit((parsed.scheme.lower(), parsed.netloc, parsed.path, parsed.query, ""))


def url_host(value: str) -> str:
    try:
        return (urlsplit(value).hostname or "").lower()
    except ValueError:
        return ""


def is_https_url(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = urlsplit(value.strip())
    except ValueError:
        return False
    return parsed.scheme.lower() == "https" and bool(parsed.hostname)


def is_public_http_url(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = urlsplit(value.strip())
    except ValueError:
        return False
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.hostname)
