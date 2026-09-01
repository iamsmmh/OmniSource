"""Cache abstraction.

The engine depends only on :class:`CacheBackend`, never on Redis directly —
this keeps the domain layer free of infrastructure imports and makes the
cache trivially swappable in tests.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any, Self


class CacheBackend(ABC):
    """Async key/value cache with TTL semantics.

    Implementations MUST be non-fatal: any backend failure should be
    swallowed (and logged) so that a cache outage degrades performance,
    never correctness.
    """

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Return the decoded value for ``key`` or ``None`` when absent."""

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store ``value`` under ``key``, expiring after ``ttl`` seconds."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove ``key`` if present."""

    @abstractmethod
    async def ping(self) -> bool:
        """Return True when the backend is reachable."""

    async def close(self) -> None:  # noqa: B027 - optional hook, intentionally concrete
        """Release any held resources."""

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()


def make_key(namespace: str, *parts: str) -> str:
    """Build a deterministic, collision-resistant cache key."""
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]
    return f"{namespace}:{digest}"


def dumps(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, default=str)


def loads(raw: str | bytes) -> Any:
    return json.loads(raw)
