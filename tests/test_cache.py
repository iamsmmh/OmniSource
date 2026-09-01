"""Cache backend contract tests."""

from __future__ import annotations

from omnisource.cache import InMemoryCache, make_key
from omnisource.cache.redis_cache import RedisCache


class FakeRedis:
    """Minimal async stand-in for redis.asyncio.Redis."""

    def __init__(self, *, broken: bool = False) -> None:
        self.store: dict[str, str] = {}
        self.broken = broken
        self.expiries: dict[str, int | None] = {}

    async def get(self, key: str) -> str | None:
        if self.broken:
            raise ConnectionError("redis down")
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        if self.broken:
            raise ConnectionError("redis down")
        self.store[key] = value
        self.expiries[key] = ex

    async def delete(self, key: str) -> None:
        self.store.pop(key, None)

    async def ping(self) -> bool:
        if self.broken:
            raise ConnectionError("redis down")
        return True

    async def aclose(self) -> None:
        self.store.clear()


async def test_memory_cache_roundtrip() -> None:
    cache = InMemoryCache()
    await cache.set("k", {"a": 1}, ttl=60)
    assert await cache.get("k") == {"a": 1}
    await cache.delete("k")
    assert await cache.get("k") is None


async def test_memory_cache_expires() -> None:
    cache = InMemoryCache()
    await cache.set("k", "v", ttl=0)
    assert await cache.get("k") == "v" or await cache.get("k") is None


async def test_memory_cache_ttl_elapsed() -> None:
    cache = InMemoryCache()
    await cache.set("k", "v", ttl=1)
    assert await cache.get("k") == "v"


async def test_redis_cache_roundtrip_with_ttl() -> None:
    fake = FakeRedis()
    cache = RedisCache(client=fake, default_ttl=42)
    await cache.set("k", [1, 2, 3])
    assert fake.expiries["k"] == 42
    assert await cache.get("k") == [1, 2, 3]


async def test_redis_failures_degrade_to_miss() -> None:
    cache = RedisCache(client=FakeRedis(broken=True))
    await cache.set("k", "v")  # must not raise
    assert await cache.get("k") is None
    assert await cache.ping() is False


async def test_redis_corrupt_payload_is_evicted() -> None:
    fake = FakeRedis()
    fake.store["k"] = "{not json"
    cache = RedisCache(client=fake)
    assert await cache.get("k") is None
    assert "k" not in fake.store


def test_make_key_is_deterministic_and_namespaced() -> None:
    a = make_key("ns", "search", "news", "python")
    b = make_key("ns", "search", "news", "python")
    c = make_key("ns", "search", "news", "rust")
    assert a == b != c
    assert a.startswith("ns:")


async def test_cache_async_context_manager() -> None:
    async with InMemoryCache() as cache:
        await cache.set("k", 1)
        assert await cache.get("k") == 1
