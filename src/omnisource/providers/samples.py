"""Reference providers.

These simulate real network-bound sources with configurable latency and
failure behaviour, so the engine's concurrency, timeout and fallback paths
can be demonstrated and tested without external dependencies.

Replace the ``_fetch`` bodies with real HTTP calls (e.g. ``httpx.AsyncClient``)
to turn any of these into a production adapter.
"""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Sequence

from omnisource.core.exceptions import ProviderUnavailableError
from omnisource.core.models import HealthReport, HealthState, ProviderMetadata, SearchItem
from omnisource.providers.base import BaseProvider


class SimulatedProvider(BaseProvider):
    """Base for the bundled demo providers.

    Args:
        latency: Simulated round-trip time in seconds.
        failure_rate: Probability in ``[0, 1]`` that a call raises.
        result_count: Number of synthetic items to emit per search.
        seed: Seed for deterministic behaviour in tests.
    """

    def __init__(
        self,
        *,
        name: str | None = None,
        weight: float | None = None,
        latency: float = 0.1,
        failure_rate: float = 0.0,
        result_count: int = 5,
        seed: int | None = None,
    ) -> None:
        super().__init__(name=name, weight=weight)
        self.latency = latency
        self.failure_rate = failure_rate
        self.result_count = result_count
        self._rng = random.Random(seed)

    async def _fetch(self) -> None:
        """Simulate the network hop and upstream error behaviour."""
        await asyncio.sleep(self.latency)
        if self.failure_rate and self._rng.random() < self.failure_rate:
            raise ProviderUnavailableError(self.name, "upstream returned HTTP 503")

    async def search(self, query: str) -> Sequence[SearchItem]:
        await self._fetch()
        return [
            SearchItem(
                id=f"{self.name}-{index}",
                title=f"{query} result #{index + 1} from {self.name}",
                url=f"https://{self.name}.example.com/items/{index}",
                score=round(1.0 - index / max(self.result_count, 1), 4),
                provider=self.name,
                extra={"rank": index + 1},
            )
            for index in range(self.result_count)
        ]

    async def get_metadata(self, id: str) -> ProviderMetadata:
        await self._fetch()
        return ProviderMetadata(
            id=id,
            provider=self.name,
            title=f"{self.name} entity {id}",
            fields={"source": self.name, "latency": self.latency},
        )

    async def health_check(self) -> HealthReport:
        started = time.perf_counter()
        try:
            await self._fetch()
        except ProviderUnavailableError as exc:
            return HealthReport(
                provider=self.name,
                state=HealthState.UNHEALTHY,
                latency_ms=(time.perf_counter() - started) * 1000,
                detail=exc.message,
            )
        return self._healthy(started, detail="simulated upstream reachable")


class NewsProvider(SimulatedProvider):
    """Fast, high-trust news source."""

    name = "news"
    weight = 1.2

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("latency", 0.05)
        super().__init__(**kwargs)  # type: ignore[arg-type]


class CatalogProvider(SimulatedProvider):
    """Medium-latency product catalog."""

    name = "catalog"
    weight = 1.0

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("latency", 0.15)
        super().__init__(**kwargs)  # type: ignore[arg-type]


class ArchiveProvider(SimulatedProvider):
    """Slow, flaky long-tail archive — the classic timeout/fallback case."""

    name = "archive"
    weight = 0.7

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("latency", 0.4)
        kwargs.setdefault("failure_rate", 0.25)
        super().__init__(**kwargs)  # type: ignore[arg-type]
