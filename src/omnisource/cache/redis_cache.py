"""Async Redis cache backend built on ``redis.asyncio``."""

from __future__ import annotations

import logging
from typing import Any

from omnisource.cache.base import CacheBackend, dumps, loads

logger = logging.getLogger(__name__)

try:  # pragma: no cover - exercised implicitly by environment
    from redis.asyncio import Redis
except ImportError:  # pragma: no cover
    Redis = None  # type: ignore[assignment, misc]


class RedisCache(CacheBackend):
    """TTL-aware JSON cache over Redis.

    Every operation is failure-tolerant: connection errors are logged and
    reported as a cache miss so the aggregation pipeline keeps flowing.
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        *,
        default_ttl: int = 300,
        client: Any | None = None,
    ) -> None:
        if client is None:
            if Redis is None:  # pragma: no cover
                raise RuntimeError("redis package is required for RedisCache")
            client = Redis.from_url(url, encoding="utf-8", decode_responses=True)
        self._client = client
        self._default_ttl = default_ttl

    async def get(self, key: str) -> Any | None:
        try:
            raw = await self._client.get(key)
        except Exception as exc:
            logger.warning("cache get failed key=%s err=%s", key, exc)
            return None
        if raw is None:
            return None
        try:
            return loads(raw)
        except ValueError:
            logger.warning("cache payload corrupt key=%s; evicting", key)
            await self.delete(key)
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        try:
            await self._client.set(
                key, dumps(value), ex=ttl if ttl is not None else self._default_ttl
            )
        except Exception as exc:
            logger.warning("cache set failed key=%s err=%s", key, exc)

    async def delete(self, key: str) -> None:
        try:
            await self._client.delete(key)
        except Exception as exc:
            logger.warning("cache delete failed key=%s err=%s", key, exc)

    async def ping(self) -> bool:
        try:
            return bool(await self._client.ping())
        except Exception as exc:
            logger.warning("cache ping failed err=%s", exc)
            return False

    async def close(self) -> None:
        try:
            await self._client.aclose()
        except Exception as exc:  # pragma: no cover
            logger.debug("cache close failed err=%s", exc)
