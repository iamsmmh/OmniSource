"""Provider contract.

A provider is a thin, stateless adapter over one external source. It knows
nothing about caching, concurrency, timeouts or aggregation — those are the
engine's concerns. This keeps providers tiny and independently testable.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Sequence

from omnisource.core.models import HealthReport, HealthState, ProviderMetadata, SearchItem


class BaseProvider(ABC):
    """Abstract adapter for a single external source.

    Subclasses implement three coroutines and are expected to raise
    :class:`~omnisource.core.exceptions.ProviderError` subclasses on failure.
    """

    #: Stable, unique provider identifier used in keys, logs and responses.
    name: str = "base"
    #: Relative weight applied to item scores during aggregation.
    weight: float = 1.0

    def __init__(self, *, name: str | None = None, weight: float | None = None) -> None:
        if name is not None:
            self.name = name
        if weight is not None:
            self.weight = weight

    @abstractmethod
    async def search(self, query: str) -> Sequence[SearchItem]:
        """Return normalized results for ``query``."""

    @abstractmethod
    async def get_metadata(self, id: str) -> ProviderMetadata:
        """Return the detail record for an entity ``id``."""

    @abstractmethod
    async def health_check(self) -> HealthReport:
        """Probe the upstream source and report liveness."""

    async def close(self) -> None:  # noqa: B027 - optional hook, intentionally concrete
        """Release provider-held resources (HTTP sessions, pools, ...)."""

    def _healthy(self, started: float, detail: str | None = None) -> HealthReport:
        """Helper building a HEALTHY report with measured latency."""
        return HealthReport(
            provider=self.name,
            state=HealthState.HEALTHY,
            latency_ms=(time.perf_counter() - started) * 1000,
            detail=detail,
        )

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r} weight={self.weight}>"
