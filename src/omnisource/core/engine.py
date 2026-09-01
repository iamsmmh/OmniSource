"""OmniSourceEngine — parallel fan-out, deadline enforcement, graceful fallback.

Request lifecycle
-----------------
1. Fan out to every selected provider concurrently (bounded by a semaphore).
2. Each call runs under a hard per-provider deadline.
3. On success the normalized payload is written to cache with a TTL.
4. On timeout/error the engine serves the last known-good cached payload if
   one exists, otherwise records the failure and moves on. A single bad
   provider can never fail the request.
5. Surviving items are weighted, merged, de-duplicated and ranked into one
   :class:`AggregatedResponse`.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Iterable, Sequence
from types import TracebackType
from typing import Self

from omnisource.cache.base import CacheBackend, make_key
from omnisource.cache.memory_cache import InMemoryCache
from omnisource.core.config import Settings, get_settings
from omnisource.core.models import (
    AggregatedResponse,
    HealthReport,
    HealthState,
    ProviderMetadata,
    ProviderResult,
    ProviderStatus,
    SearchItem,
)
from omnisource.providers.base import BaseProvider
from omnisource.providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)


class OmniSourceEngine:
    """Aggregates many providers behind one resilient, cached interface."""

    def __init__(
        self,
        registry: ProviderRegistry | Iterable[BaseProvider] | None = None,
        *,
        cache: CacheBackend | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        if registry is None:
            registry = ProviderRegistry()
        elif not isinstance(registry, ProviderRegistry):
            registry = ProviderRegistry(registry)
        self.registry = registry
        self.cache: CacheBackend = cache or InMemoryCache(default_ttl=self.settings.cache_ttl)
        self._semaphore = asyncio.Semaphore(self.settings.max_concurrency)

    # ------------------------------------------------------------------ API

    def register(self, provider: BaseProvider) -> None:
        """Register an additional provider at runtime."""
        self.registry.register(provider)

    async def search(
        self,
        query: str,
        *,
        providers: Sequence[str] | None = None,
        timeout: float | None = None,
        limit: int | None = None,
        use_cache: bool | None = None,
    ) -> AggregatedResponse:
        """Fan out ``query`` to providers and merge the outcome."""
        started = time.perf_counter()
        selected = self.registry.select(providers)
        deadline = timeout if timeout is not None else self.settings.provider_timeout
        cached = self.settings.cache_enabled if use_cache is None else use_cache

        results = await asyncio.gather(
            *(self._search_one(p, query, deadline, cached) for p in selected)
        )

        merged = self._merge(results, limit or self.settings.max_items)
        return AggregatedResponse(
            query=query,
            items=merged,
            results=results,
            total=len(merged),
            elapsed_ms=(time.perf_counter() - started) * 1000,
        )

    async def get_metadata(self, provider: str, id: str) -> ProviderMetadata:
        """Fetch a detail record from a single named provider."""
        return await self.registry.get(provider).get_metadata(id)

    async def health_check(self, *, timeout: float | None = None) -> list[HealthReport]:
        """Probe every registered provider concurrently."""
        deadline = timeout if timeout is not None else self.settings.provider_timeout
        return list(await asyncio.gather(*(self._health_one(p, deadline) for p in self.registry)))

    async def close(self) -> None:
        """Release provider and cache resources."""
        await asyncio.gather(
            *(p.close() for p in self.registry), self.cache.close(), return_exceptions=True
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    # ------------------------------------------------------------- internals

    def _key(self, provider: BaseProvider, query: str) -> str:
        return make_key(
            self.settings.cache_namespace, "search", provider.name, query.strip().lower()
        )

    async def _search_one(
        self, provider: BaseProvider, query: str, timeout: float, use_cache: bool
    ) -> ProviderResult:
        """Run one provider under a deadline, falling back to cache on failure."""
        key = self._key(provider, query)
        started = time.perf_counter()

        if use_cache:
            hit = await self.cache.get(key)
            if hit is not None:
                return ProviderResult(
                    provider=provider.name,
                    status=ProviderStatus.CACHED,
                    items=[SearchItem(**item) for item in hit],
                    latency_ms=(time.perf_counter() - started) * 1000,
                    from_cache=True,
                )

        status = ProviderStatus.OK
        error: str | None = None
        items: list[SearchItem] = []
        try:
            async with self._semaphore:
                raw = await asyncio.wait_for(provider.search(query), timeout=timeout)
            items = list(raw)
            if use_cache:
                await self.cache.set(
                    key, [i.model_dump(mode="json") for i in items], ttl=self.settings.cache_ttl
                )
        except TimeoutError:
            status, error = ProviderStatus.TIMEOUT, f"exceeded {timeout}s deadline"
            logger.warning("provider timeout provider=%s query=%r", provider.name, query)
        except asyncio.CancelledError:  # pragma: no cover - propagate cooperative cancellation
            raise
        except Exception as exc:
            status, error = ProviderStatus.ERROR, str(exc)
            logger.exception("provider failed provider=%s query=%r", provider.name, query)

        if status is not ProviderStatus.OK:
            stale = await self.cache.get(key) if use_cache else None
            if stale is not None:
                logger.info("serving stale cache provider=%s", provider.name)
                return ProviderResult(
                    provider=provider.name,
                    status=ProviderStatus.CACHED,
                    items=[SearchItem(**item) for item in stale],
                    latency_ms=(time.perf_counter() - started) * 1000,
                    error=error,
                    from_cache=True,
                )

        return ProviderResult(
            provider=provider.name,
            status=status,
            items=items,
            latency_ms=(time.perf_counter() - started) * 1000,
            error=error,
        )

    async def _health_one(self, provider: BaseProvider, timeout: float) -> HealthReport:
        started = time.perf_counter()
        try:
            return await asyncio.wait_for(provider.health_check(), timeout=timeout)
        except TimeoutError:
            detail = f"health probe exceeded {timeout}s"
            state = HealthState.UNHEALTHY
        except Exception as exc:
            detail, state = str(exc), HealthState.UNHEALTHY
        return HealthReport(
            provider=provider.name,
            state=state,
            latency_ms=(time.perf_counter() - started) * 1000,
            detail=detail,
        )

    def _merge(self, results: Sequence[ProviderResult], limit: int) -> list[SearchItem]:
        """Weight, de-duplicate and rank items from all successful providers."""
        best: dict[str, SearchItem] = {}
        for result in results:
            if not result.succeeded:
                continue
            weight = self._weight_of(result.provider)
            for item in result.items:
                scored = item.model_copy(update={"score": round(item.score * weight, 6)})
                dedupe_key = (scored.url or f"{scored.provider}:{scored.id}").lower()
                incumbent = best.get(dedupe_key)
                if incumbent is None or scored.score > incumbent.score:
                    best[dedupe_key] = scored
        ranked = sorted(best.values(), key=lambda i: (-i.score, i.provider, i.id))
        return ranked[:limit]

    def _weight_of(self, name: str) -> float:
        return self.registry.get(name).weight if name in self.registry else 1.0
