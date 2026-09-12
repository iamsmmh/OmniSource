"""Release integrity engine (Phase 3).

Two complementary layers:

1. **Metadata verification** (every build, offline).
   For every app's newest asset the report records the contract fields

       {"sha256": str | null, "size": int, "releaseId": str, "source": str}

   and evaluates the reject rules that can be decided without downloading:

   * ``zeroBytes``     — upstream reported size 0 (corrupted / empty asset)
   * ``missingIPA``    — the primary download is not an installable IPA
   * ``badDigest``     — a sha256 is recorded but is not a 64-char hex digest

   A digest *mismatch* can only be proven by downloading, so it is decided by
   layer 2 whenever an expected digest is known.

2. **Full verification** (optional, ``--verify-downloads`` / weekly
   ``verify.yml``). Streams each IPA to disk-free memory (chunked SHA-256),
   checks the byte count and digest, and records the outcome in
   ``state.json`` (``lastFullVerification``) so the next metadata report can
   also reflect real download results.

The document is rendered as ``feeds/integrity_report.json`` and fails the
offline validator when a hard reject rule fires, so a zero-byte or missing
IPA can never reach a published feed unmarked.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

from omnisource.constants import INSTALLABLE_SUFFIXES
from omnisource.discovery import newest_version
from omnisource.domain import Catalog, today
from omnisource.logutil import log
from omnisource.utils.dates import days_since

INTEGRITY_SCHEMA_VERSION = 1

# Reject-rule severities.
HARD = "fail"
SOFT = "warn"
OK = "pass"

# .tipa is a renamed .ipa (TrollStore); both are installable downloads.
SHA256_HEX_LEN = 64


def _digest_ok(value: Any) -> bool:
    return isinstance(value, str) and len(value) == SHA256_HEX_LEN and all(c in "0123456789abcdefABCDEF" for c in value)


def _is_ipa(url: str) -> bool:
    return url.split("?", 1)[0].lower().endswith(INSTALLABLE_SUFFIXES)


def metadata_checks(app: Any, newest: dict[str, Any], health: dict[str, Any] | None) -> dict[str, Any]:
    """Evaluate the offline reject rules for one app's newest asset."""
    url = str(newest.get("downloadURL") or "")
    size = newest.get("size")
    size = int(size) if isinstance(size, (int, float)) and not isinstance(size, bool) else 0
    sha = newest.get("sha256")
    sha = str(sha) if sha else None

    checks = {
        "sizePositive": size > 0,
        "installable": _is_ipa(url),
        "digestFormat": True if sha is None else _digest_ok(sha),
        "reachable": bool((health or {}).get("downloadReachable", True)),
    }
    status = OK
    if not (checks["sizePositive"] and checks["installable"] and checks["digestFormat"]):
        status = HARD
    elif sha is None:
        # Missing digest is not a corruption signal (many upstreams publish
        # none); it keeps the soft "warn" band so reports stay actionable.
        status = SOFT
    return {"checks": checks, "status": status}


def asset_record(app: Any, newest: dict[str, Any]) -> dict[str, Any]:
    """The stored per-asset integrity record (Phase 3 contract)."""
    return {
        "sha256": str(newest["sha256"]) if newest.get("sha256") else None,
        "size": int(newest.get("size") or 0),
        "releaseId": str(newest.get("version") or ""),
        "source": str(newest.get("source") or ""),
        "downloadUrl": str(newest.get("downloadURL") or ""),
    }


def build_integrity_doc(
    catalog: Catalog,
    state: dict[str, Any],
    health_doc: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Render ``feeds/integrity_report.json`` from pipeline state."""
    health_doc = health_doc or {}
    health_by_slug = {item.get("slug"): item for item in health_doc.get("apps", []) if isinstance(item, dict)}

    entries: list[dict[str, Any]] = []
    for app in catalog.apps:
        newest = newest_version(state, app.slug)
        if not newest:
            continue
        result = metadata_checks(app, newest, health_by_slug.get(app.slug))
        full = (state.get(app.slug) or {}).get("lastFullVerification")
        if isinstance(full, dict) and full.get("at"):
            result["fullVerification"] = full
            if full.get("ok") is False:
                result["status"] = HARD
                result["checks"]["corruptedDownload"] = False
        entries.append(
            {
                "slug": app.slug,
                "name": app.name,
                "asset": asset_record(app, newest),
                **result,
            }
        )

    totals = {
        "apps": len(entries),
        "pass": sum(1 for e in entries if e["status"] == OK),
        "warn": sum(1 for e in entries if e["status"] == SOFT),
        "fail": sum(1 for e in entries if e["status"] == HARD),
    }
    totals["rejected"] = totals["fail"]
    rejected = [
        {
            "slug": entry["slug"],
            "reasons": [name for name, ok in entry["checks"].items() if not ok],
        }
        for entry in entries
        if entry["status"] == HARD
    ]
    entries.sort(key=lambda entry: (entry["status"] != HARD, entry["slug"]))
    return {
        "schemaVersion": INTEGRITY_SCHEMA_VERSION,
        "generatedAt": today(),
        "totals": totals,
        "rejected": rejected,
        "apps": entries,
    }


def integrity_errors(doc: dict[str, Any]) -> list[str]:
    """Validator-facing hard failures from an integrity report."""
    problems: list[str] = []
    for item in doc.get("rejected", []):
        if not isinstance(item, dict):
            continue
        problems.append(f"integrity: {item.get('slug')} rejected ({', '.join(item.get('reasons', []))})")
    return problems


# ---------------------------------------------------------------------------
# Full download verification (streaming; memory-safe for large IPAs)
# ---------------------------------------------------------------------------


def stream_sha256(http: Any, url: str, *, timeout: float = 300.0) -> tuple[int, str]:
    """Download ``url`` in chunks; return ``(byte_count, sha256_hex)``.

    Raises ``OSError`` on transport failure or a zero-byte body so callers can
    mark the download corrupted instead of publishing a partial verdict.
    """
    digest = hashlib.sha256()
    total = 0
    with http.open_stream(url, timeout=timeout) as response:
        while True:
            data = response.read(1024 * 1024)
            if not data:
                break
            digest.update(data)
            total += len(data)
    if total == 0:
        raise OSError("downloaded asset is zero bytes")
    return total, digest.hexdigest()


def verification_due(
    app_state: dict[str, Any],
    newest: dict[str, Any],
    *,
    stale_days: int | None,
    today_iso: str | None = None,
) -> tuple[bool, int, str]:
    """Whether an app's newest asset needs a (re-)verification.

    Returns ``(due, priority, reason)`` where the priority orders a bounded
    run: 0 = never verified or last attempt failed, 1 = the asset changed or
    carries no digest, 2 = the recorded verification is older than
    ``stale_days``. ``stale_days=None`` disables the age rule, so every asset
    is due (the historical ``--verify-downloads`` behaviour).

    The rule keeps the weekly job affordable: the catalog is measured in
    gigabytes, so only assets that changed or aged out are streamed again.
    """
    record = app_state.get("lastFullVerification")
    if not isinstance(record, dict) or not record.get("at"):
        return True, 0, "never verified"
    if record.get("ok") is False:
        return True, 0, "last attempt failed"
    version = str(newest.get("version") or "")
    if record.get("version") and str(record["version"]) != version:
        return True, 1, f"asset changed ({record.get('version')} -> {version})"
    recorded_size = record.get("size") or record.get("expectedSize")
    live_size = newest.get("size")
    if (
        isinstance(recorded_size, (int, float))
        and isinstance(live_size, (int, float))
        and int(recorded_size) != int(live_size)
    ):
        return True, 1, "asset size changed"
    if newest.get("sha256") and not record.get("sha256"):
        return True, 1, "no digest recorded"
    if stale_days is None:
        return True, 2, "stale window disabled"
    age = days_since(record.get("at"), today_iso=today_iso or today())
    if age >= int(stale_days):
        return True, 2, f"verified {age} day(s) ago"
    return False, 3, f"verified {age} day(s) ago"


def select_verification_targets(
    catalog: Catalog,
    state: dict[str, Any],
    *,
    only: set[str] | None = None,
    stale_days: int | None = None,
    limit: int = 0,
    today_iso: str | None = None,
) -> list[tuple[str, str]]:
    """App slugs to verify, most urgent first, capped at ``limit``.

    Returns ``(slug, reason)`` pairs. Ordering is deterministic: never/failed
    verifications, then changed assets, then the oldest records — so a bounded
    run always makes progress and eventually covers the whole catalog.
    """
    due: list[tuple[int, str, str]] = []
    for app in catalog.apps:
        if only and app.slug not in only:
            continue
        app_state = state.get(app.slug) if isinstance(state.get(app.slug), dict) else {}
        newest = newest_version(state, app.slug)
        if not newest or not str(newest.get("downloadURL") or ""):
            continue
        needed, priority, reason = verification_due(app_state, newest, stale_days=stale_days, today_iso=today_iso)
        if not needed:
            continue
        record = app_state.get("lastFullVerification")
        recorded_at = str(record.get("at") or "") if isinstance(record, dict) else ""
        due.append((priority, recorded_at, f"{app.slug}\t{reason}"))
    due.sort()
    ordered = [tuple(item.split("\t", 1)) for _priority, _at, item in due]  # type: ignore[misc]
    return ordered[:limit] if limit and limit > 0 else ordered


def verify_downloads(
    container: Any,
    catalog: Catalog,
    state: dict[str, Any],
    *,
    only: set[str] | None = None,
    workers: int = 4,
) -> list[dict[str, Any]]:
    """Stream-download and hash every selected app's newest asset.

    Results are written to ``state[slug]["lastFullVerification"]`` so the next
    metadata report (and the status board) reflects real download outcomes.
    A failing app never mutates its version state — only the verification
    record changes.
    """
    import concurrent.futures

    selected = [app for app in catalog.apps if not only or app.slug in only]
    results: list[dict[str, Any]] = []

    def _verify(app: Any) -> dict[str, Any]:
        newest = newest_version(state, app.slug)
        url = str(newest.get("downloadURL") or "")
        expected_sha = newest.get("sha256")
        expected_size = newest.get("size")
        started = time.monotonic()
        record: dict[str, Any] = {
            "slug": app.slug,
            "url": url,
            "version": str(newest.get("version") or ""),
            "expectedSha256": str(expected_sha) if expected_sha else None,
            "expectedSize": int(expected_size) if isinstance(expected_size, (int, float)) else None,
        }
        try:
            timeout = max(60.0, float(container.settings.health_timeout) * 10)
            size, sha = stream_sha256(container.http, url, timeout=timeout)
            record["size"] = size
            record["sha256"] = sha
            problems = []
            if expected_sha and str(expected_sha).lower() != sha.lower():
                problems.append("hash mismatch")
            if expected_size and int(expected_size) != size:
                problems.append("size mismatch")
            if not _is_ipa(url):
                problems.append("not an IPA")
            record["ok"] = not problems
            record["detail"] = "; ".join(problems) or "ok"
        except Exception as error:  # network/IO failures are per-app results
            record["ok"] = False
            record["detail"] = f"corrupted download: {error}"
        record["at"] = today()
        record["durationMs"] = int((time.monotonic() - started) * 1000)
        return record

    max_workers = max(1, min(workers, len(selected))) if selected else 1
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        for record in pool.map(_verify, selected):
            results.append(record)
            status = "ok" if record["ok"] else "FAIL"
            log.info(
                "%-14s full verify %s: %s (%d ms)",
                record["slug"],
                status,
                record.get("detail"),
                record.get("durationMs", 0),
            )
            entry = state.setdefault(record["slug"], {})
            entry["lastFullVerification"] = {key: value for key, value in record.items() if key not in ("slug", "url")}

    return results
