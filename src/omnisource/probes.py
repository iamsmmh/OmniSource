"""Active health probing for sources, feeds and downloads.

:mod:`omnisource.monitor` renders the pipeline's probe history. This module
performs the probing itself as a standalone, schedule-friendly operation
(run every 30 minutes from ``monitoring.yml``):

* :func:`probe_url` — one HEAD/GET round-trip with latency measurement.
* :func:`check_sources` — probe every upstream feed / homepage concurrently.
* :func:`check_downloads` — probe every app's newest download URL.
* :func:`build_status` — roll results into ``data/status.json`` with the
  ``online`` / ``degraded`` / ``offline`` state machine.

Stdlib only; concurrency via :class:`concurrent.futures.ThreadPoolExecutor`.
Credentials are never attached: probes are anonymous by design.
"""

from __future__ import annotations

import concurrent.futures
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from typing import Any

from omnisource.constants import USER_AGENT
from omnisource.http import is_http_url

ONLINE = "online"
DEGRADED = "degraded"
OFFLINE = "offline"

STATUS_SCHEMA_VERSION = 1


def utcnow() -> str:
    """Current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def probe_url(url: str, *, timeout: int = 12) -> dict[str, Any]:
    """Probe one URL; never raises. A 2xx/3xx is reachable."""
    result: dict[str, Any] = {"url": url, "ok": False, "status": 0, "latency_ms": None, "error": ""}
    if not is_http_url(url):
        result["error"] = "not an http(s) URL"
        return result
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                code = response.status
                if method == "GET":
                    response.read(1024)  # Confirm the body actually starts flowing.
        except urllib.error.HTTPError as exc:
            result["latency_ms"] = int((time.monotonic() - started) * 1000)
            if exc.code in (403, 405) and method == "HEAD":
                continue
            result["status"] = exc.code
            result["error"] = f"HTTP {exc.code}"
            return result
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            result["latency_ms"] = int((time.monotonic() - started) * 1000)
            result["error"] = str(exc) or "unreachable"
            return result
        result["latency_ms"] = int((time.monotonic() - started) * 1000)
        result["status"] = code
        if 200 <= code < 400:
            result["ok"] = True
            return result
        result["error"] = f"HTTP {code}"
        return result
    return result


def _run(urls: list[str], *, timeout: int, workers: int) -> list[dict[str, Any]]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(probe_url, url, timeout=timeout): url for url in urls}
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    return sorted(results, key=lambda item: item["url"])


def check_sources(
    sources: list[dict[str, Any]],
    *,
    timeout: int = 12,
    workers: int = 16,
) -> list[dict[str, Any]]:
    """Probe each source's feed URL (falling back to its homepage)."""
    targets = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        url = source.get("sourceURL") or source.get("url") or source.get("homepage") or ""
        if is_http_url(url):
            targets.append((str(source.get("id") or url), url))
    probed = {item["url"]: item for item in _run([url for _, url in targets], timeout=timeout, workers=workers)}
    results = []
    for source_id, url in targets:
        probe = probed.get(url, {})
        results.append({"id": source_id, "url": url, **{k: v for k, v in probe.items() if k != "url"}})
    return sorted(results, key=lambda item: item["id"])


def check_downloads(
    apps: list[dict[str, Any]],
    *,
    timeout: int = 12,
    workers: int = 16,
) -> list[dict[str, Any]]:
    """Probe each app's newest download URL concurrently."""
    targets = []
    for app in apps:
        if not isinstance(app, dict):
            continue
        url = app.get("downloadURL") or ""
        if is_http_url(url):
            targets.append((str(app.get("slug") or app.get("id") or app.get("name") or url), url))
    probed = {item["url"]: item for item in _run([url for _, url in targets], timeout=timeout, workers=workers)}
    results = []
    for app_id, url in targets:
        probe = probed.get(url, {})
        results.append({"id": app_id, "url": url, **{k: v for k, v in probe.items() if k != "url"}})
    return sorted(results, key=lambda item: item["id"])


def state_for(ok: int, total: int) -> str:
    """Roll individual probe outcomes into one state."""
    if total == 0:
        return OFFLINE
    if ok == total:
        return ONLINE
    if ok == 0:
        return OFFLINE
    return DEGRADED


def build_status(
    source_results: list[dict[str, Any]],
    download_results: list[dict[str, Any]],
    *,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the ``data/status.json`` monitoring document."""
    sources_ok = sum(1 for item in source_results if item.get("ok"))
    downloads_ok = sum(1 for item in download_results if item.get("ok"))
    sources_state = state_for(sources_ok, len(source_results))
    downloads_state = state_for(downloads_ok, len(download_results))
    overall = (
        ONLINE
        if sources_state == ONLINE and downloads_state == ONLINE
        else (OFFLINE if sources_state == OFFLINE and downloads_state == OFFLINE else DEGRADED)
    )
    history: list[dict[str, Any]] = []
    if isinstance(previous, dict) and isinstance(previous.get("history"), list):
        history = [entry for entry in previous["history"] if isinstance(entry, dict)][-29:]
    history.append(
        {"at": utcnow(), "overall": overall, "sourcesOk": sources_ok, "downloadsOk": downloads_ok},
    )
    return {
        "schemaVersion": STATUS_SCHEMA_VERSION,
        "generatedAt": utcnow(),
        "overall": overall,
        "summary": {
            "sources": len(source_results),
            "sourcesOk": sources_ok,
            "sourcesState": sources_state,
            "downloads": len(download_results),
            "downloadsOk": downloads_ok,
            "downloadsState": downloads_state,
        },
        "sources": source_results,
        "downloads": download_results,
        "failing": sorted(
            {item["id"] for item in (*source_results, *download_results) if not item.get("ok")},
        ),
        "history": history,
    }
