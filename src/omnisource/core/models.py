"""Standardized, immutable response schemas shared across the whole system.

Every provider must speak this vocabulary; the engine never leaks
provider-specific payload shapes to callers.
"""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field


class ProviderStatus(StrEnum):
    """Outcome of a single provider invocation."""

    OK = "ok"
    TIMEOUT = "timeout"
    ERROR = "error"
    CACHED = "cached"
    SKIPPED = "skipped"


class HealthState(StrEnum):
    """Coarse-grained provider liveness."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SearchItem(_Frozen):
    """A single normalized result row."""

    id: str
    title: str
    url: str | None = None
    score: float = 0.0
    provider: str = ""
    extra: Mapping[str, Any] = Field(default_factory=dict)


class ProviderResult(_Frozen):
    """Envelope describing what one provider returned for one request."""

    provider: str
    status: ProviderStatus
    items: Sequence[SearchItem] = ()
    latency_ms: float = 0.0
    error: str | None = None
    from_cache: bool = False

    @property
    def succeeded(self) -> bool:
        return self.status in (ProviderStatus.OK, ProviderStatus.CACHED)


class AggregatedResponse(_Frozen):
    """The single standardized shape returned by :class:`OmniSourceEngine`."""

    query: str
    items: Sequence[SearchItem] = ()
    results: Sequence[ProviderResult] = ()
    total: int = 0
    elapsed_ms: float = 0.0
    generated_at: float = Field(default_factory=time.time)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def degraded(self) -> bool:
        """True when at least one provider failed to contribute fresh data."""
        return any(not r.succeeded for r in self.results)


class ProviderMetadata(_Frozen):
    """Detail record for a single entity fetched from a provider."""

    id: str
    provider: str
    title: str
    fields: Mapping[str, Any] = Field(default_factory=dict)


class HealthReport(_Frozen):
    """Result of a provider health probe."""

    provider: str
    state: HealthState
    latency_ms: float = 0.0
    detail: str | None = None
