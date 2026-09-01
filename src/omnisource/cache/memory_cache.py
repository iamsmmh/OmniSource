"""In-process cache backend: default for tests and single-node deployments."""

from __future__ import annotations

import time
from typing import Any

from omnisource.cache.base import CacheBackend


class InMemoryCache(CacheBackend):
    """Dict-backed TTL cache. Not shared across processes."""

    def __init__(self, *, default_ttl: int = 300) -> None:
        self._store: dict[str, tuple[float | None, Any]] = {}
        self._default_ttl = default_ttl

    async def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at is not None and expires_at <= time.monotonic():
            self._store.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        effective = self._default_ttl if ttl is None else ttl
        expires_at = time.monotonic() + effective if effective > 0 else None
        self._store[key] = (expires_at, value)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        self._store.clear()
