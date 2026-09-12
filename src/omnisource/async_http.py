"""Async batch fetching for internet-scale source counts.

The default pipeline path (:mod:`omnisource.http`, :mod:`omnisource.probes`)
is stdlib-only and thread-based — the right tradeoff up to a few hundred
sources. Past ~1,000 sources / ~10,000 apps the discovery and monitoring
passes switch to this module:

* when ``aiohttp`` is installed: a single shared ``ClientSession`` with a
  bounded ``TCPConnector`` (connection pooling + keep-alive);
* otherwise: :func:`asyncio.to_thread` over :mod:`urllib` with a semaphore
  (still concurrent, zero new dependencies).

The public surface (:func:`fetch_many`, :func:`probe_many`) is identical
either way, so callers never branch on the backend. Responses are capped
(``max_bytes``) and never carry credentials.
"""

from __future__ import annotations

import asyncio
import time
import urllib.error
import urllib.request
from typing import Any

from omnisource.constants import USER_AGENT

try:  # Optional accelerator; the stdlib fallback below is always available.
    import aiohttp  # type: ignore[import-not-found]

    HAS_AIOHTTP = True
except ImportError:  # pragma: no cover - depends on the environment.
    aiohttp = None  # type: ignore[assignment]
    HAS_AIOHTTP = False

DEFAULT_LIMIT = 32
DEFAULT_TIMEOUT = 15
DEFAULT_MAX_BYTES = 2_000_000


def _sync_fetch(url: str, *, timeout: int, max_bytes: int) -> dict[str, Any]:
    started = time.monotonic()
    result: dict[str, Any] = {"url": url, "ok": False, "status": 0, "bytes": 0, "error": ""}
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(max_bytes + 1)
            code = response.status or 200  # Non-HTTP schemes (file://) report no status.
            result["status"] = code
            result["bytes"] = len(body)
            result["ok"] = 200 <= code < 400 and len(body) <= max_bytes
            if len(body) > max_bytes:
                result["error"] = f"payload exceeds {max_bytes} bytes"
    except urllib.error.HTTPError as exc:
        result["status"] = exc.code
        result["error"] = f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        result["error"] = str(exc) or "unreachable"
    result["latency_ms"] = int((time.monotonic() - started) * 1000)
    return result


async def _fallback_fetch_many(
    urls: list[str],
    *,
    timeout: int,
    limit: int,
    max_bytes: int,
) -> list[dict[str, Any]]:
    semaphore = asyncio.Semaphore(max(1, limit))

    async def bounded(url: str) -> dict[str, Any]:
        async with semaphore:
            return await asyncio.to_thread(_sync_fetch, url, timeout=timeout, max_bytes=max_bytes)

    return list(await asyncio.gather(*(bounded(url) for url in urls)))


async def _aiohttp_fetch_many(
    urls: list[str],
    *,
    timeout: int,
    limit: int,
    max_bytes: int,
) -> list[dict[str, Any]]:
    connector = aiohttp.TCPConnector(limit=limit, ttl_dns_cache=300)
    client_timeout = aiohttp.ClientTimeout(total=timeout)
    results: list[dict[str, Any]] = []

    async def one(session: Any, url: str) -> dict[str, Any]:
        started = time.monotonic()
        result: dict[str, Any] = {"url": url, "ok": False, "status": 0, "bytes": 0, "error": ""}
        try:
            async with session.get(url, headers={"User-Agent": USER_AGENT}) as response:
                body = await response.content.read(max_bytes + 1)
                result["status"] = response.status
                result["bytes"] = len(body)
                result["ok"] = 200 <= response.status < 400 and len(body) <= max_bytes
        except TimeoutError:
            result["error"] = "timeout"
        except Exception as exc:
            result["error"] = str(exc) or "unreachable"
        result["latency_ms"] = int((time.monotonic() - started) * 1000)
        return result

    async with aiohttp.ClientSession(connector=connector, timeout=client_timeout) as session:
        for url in urls:
            results.append(await one(session, url))
    return results


async def fetch_many_async(
    urls: list[str],
    *,
    timeout: int = DEFAULT_TIMEOUT,
    limit: int = DEFAULT_LIMIT,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> list[dict[str, Any]]:
    """Concurrently fetch ``urls``; returns one result dict per URL."""
    if HAS_AIOHTTP:
        return await _aiohttp_fetch_many(urls, timeout=timeout, limit=limit, max_bytes=max_bytes)
    return await _fallback_fetch_many(urls, timeout=timeout, limit=limit, max_bytes=max_bytes)


def fetch_many(
    urls: list[str],
    *,
    timeout: int = DEFAULT_TIMEOUT,
    limit: int = DEFAULT_LIMIT,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> list[dict[str, Any]]:
    """Blocking wrapper around :func:`fetch_many_async`."""
    return asyncio.run(fetch_many_async(urls, timeout=timeout, limit=limit, max_bytes=max_bytes))


async def probe_many_async(
    urls: list[str],
    *,
    timeout: int = DEFAULT_TIMEOUT,
    limit: int = DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Fetch ``urls`` and roll the outcomes into a summary document."""
    results = await fetch_many_async(urls, timeout=timeout, limit=limit, max_bytes=4096)
    ok = sum(1 for item in results if item["ok"])
    latencies = sorted(item["latency_ms"] for item in results if item.get("latency_ms") is not None)
    median = latencies[len(latencies) // 2] if latencies else 0
    return {
        "total": len(results),
        "ok": ok,
        "failed": len(results) - ok,
        "medianLatencyMs": median,
        "backend": "aiohttp" if HAS_AIOHTTP else "stdlib",
        "results": results,
    }


def probe_many(
    urls: list[str],
    *,
    timeout: int = DEFAULT_TIMEOUT,
    limit: int = DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Blocking wrapper around :func:`probe_many_async`."""
    return asyncio.run(probe_many_async(urls, timeout=timeout, limit=limit))
