"""Engine behaviour: concurrency, timeouts, fallback and merging."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Sequence

import pytest

from omnisource.cache import InMemoryCache
from omnisource.core.config import Settings
from omnisource.core.engine import OmniSourceEngine
from omnisource.core.exceptions import ConfigurationError, ProviderUnavailableError
from omnisource.core.models import (
    HealthReport,
    HealthState,
    ProviderMetadata,
    ProviderStatus,
    SearchItem,
)
from omnisource.providers import BaseProvider, NewsProvider, ProviderRegistry, SimulatedProvider


class FlakyProvider(BaseProvider):
    """Provider that succeeds until ``fail`` is flipped on."""

    name = "flaky"

    def __init__(self, *, delay: float = 0.0) -> None:
        super().__init__()
        self.fail = False
        self.delay = delay
        self.calls = 0

    async def search(self, query: str) -> Sequence[SearchItem]:
        self.calls += 1
        await asyncio.sleep(self.delay)
        if self.fail:
            raise ProviderUnavailableError(self.name, "boom")
        return [
            SearchItem(
                id="1", title=f"{query} ok", url="https://flaky/1", score=1.0, provider=self.name
            )
        ]

    async def get_metadata(self, id: str) -> ProviderMetadata:
        return ProviderMetadata(id=id, provider=self.name, title="meta")

    async def health_check(self) -> HealthReport:
        return HealthReport(provider=self.name, state=HealthState.HEALTHY)


def make_engine(providers: list[BaseProvider], **overrides: object) -> OmniSourceEngine:
    settings = Settings(cache_enabled=True, cache_ttl=60, provider_timeout=1.0, **overrides)  # type: ignore[arg-type]
    return OmniSourceEngine(ProviderRegistry(providers), cache=InMemoryCache(), settings=settings)


async def test_search_aggregates_all_providers() -> None:
    engine = make_engine(
        [NewsProvider(result_count=3), SimulatedProvider(name="alt", result_count=2)]
    )
    response = await engine.search("python")

    assert response.total == 5
    assert {r.provider for r in response.results} == {"news", "alt"}
    assert all(r.status is ProviderStatus.OK for r in response.results)
    assert not response.degraded


async def test_providers_run_in_parallel() -> None:
    providers = [SimulatedProvider(name=f"p{i}", latency=0.2, result_count=1) for i in range(5)]
    engine = make_engine(providers)

    started = time.perf_counter()
    await engine.search("q")
    elapsed = time.perf_counter() - started

    assert elapsed < 0.6, "providers should overlap, not run serially"


async def test_slow_provider_times_out_without_failing_request() -> None:
    engine = make_engine(
        [NewsProvider(result_count=1), SimulatedProvider(name="slow", latency=1.0)]
    )
    response = await engine.search("q", timeout=0.1)

    by_name = {r.provider: r for r in response.results}
    assert by_name["slow"].status is ProviderStatus.TIMEOUT
    assert by_name["news"].status is ProviderStatus.OK
    assert response.degraded and response.total == 1


async def test_failure_falls_back_to_cached_payload() -> None:
    flaky = FlakyProvider()
    engine = make_engine([flaky])

    warm = await engine.search("q")
    assert warm.results[0].status is ProviderStatus.OK

    flaky.fail = True
    stale = await engine.search("q", use_cache=True)
    assert stale.results[0].status is ProviderStatus.CACHED
    assert stale.results[0].from_cache
    assert stale.total == 1


async def test_failure_without_cache_is_skipped_gracefully() -> None:
    flaky = FlakyProvider()
    flaky.fail = True
    engine = make_engine([flaky, NewsProvider(result_count=2)])

    response = await engine.search("q")
    by_name = {r.provider: r for r in response.results}
    assert by_name["flaky"].status is ProviderStatus.ERROR
    assert by_name["flaky"].error
    assert response.total == 2


async def test_cache_hit_avoids_second_provider_call() -> None:
    flaky = FlakyProvider()
    engine = make_engine([flaky])

    await engine.search("cached")
    await engine.search("cached")

    assert flaky.calls == 1


async def test_use_cache_false_bypasses_cache() -> None:
    flaky = FlakyProvider()
    engine = make_engine([flaky])

    await engine.search("q", use_cache=False)
    await engine.search("q", use_cache=False)

    assert flaky.calls == 2


async def test_merge_dedupes_and_applies_weights() -> None:
    engine = make_engine([FlakyProvider()])
    engine.register(SimulatedProvider(name="heavy", weight=2.0, result_count=1))

    response = await engine.search("q", limit=10)
    scores = [i.score for i in response.items]
    assert scores == sorted(scores, reverse=True)
    assert len({i.url for i in response.items}) == len(response.items)


async def test_limit_is_respected() -> None:
    engine = make_engine([SimulatedProvider(name="many", result_count=50)])
    response = await engine.search("q", limit=5)
    assert response.total == 5


async def test_unknown_provider_selection_raises() -> None:
    engine = make_engine([NewsProvider()])
    with pytest.raises(ConfigurationError):
        await engine.search("q", providers=["nope"])


async def test_health_check_reports_every_provider() -> None:
    engine = make_engine([NewsProvider(), SimulatedProvider(name="slow", latency=1.0)])
    reports = await engine.health_check(timeout=0.1)

    by_name = {r.provider: r for r in reports}
    assert by_name["news"].state is HealthState.HEALTHY
    assert by_name["slow"].state is HealthState.UNHEALTHY


async def test_duplicate_registration_rejected() -> None:
    engine = make_engine([NewsProvider()])
    with pytest.raises(ConfigurationError):
        engine.register(NewsProvider())


async def test_engine_context_manager_closes_cleanly() -> None:
    async with make_engine([NewsProvider(result_count=1)]) as engine:
        assert (await engine.search("q")).total == 1
