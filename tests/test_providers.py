"""Provider contract tests."""

from __future__ import annotations

import pytest

from omnisource.core.exceptions import ProviderUnavailableError
from omnisource.core.models import HealthState
from omnisource.providers import (
    ArchiveProvider,
    BaseProvider,
    CatalogProvider,
    NewsProvider,
    SimulatedProvider,
)


def test_base_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        BaseProvider()  # type: ignore[abstract]


@pytest.mark.parametrize("factory", [NewsProvider, CatalogProvider, ArchiveProvider])
async def test_providers_implement_contract(factory: type[SimulatedProvider]) -> None:
    provider = factory(failure_rate=0.0, result_count=3, latency=0.0)
    items = await provider.search("query")
    assert len(items) == 3
    assert all(item.provider == provider.name for item in items)

    metadata = await provider.get_metadata("42")
    assert metadata.id == "42" and metadata.provider == provider.name

    assert (await provider.health_check()).state is HealthState.HEALTHY


async def test_failing_provider_raises_and_reports_unhealthy() -> None:
    provider = SimulatedProvider(name="broken", latency=0.0, failure_rate=1.0)
    with pytest.raises(ProviderUnavailableError):
        await provider.search("q")
    assert (await provider.health_check()).state is HealthState.UNHEALTHY


def test_repr_is_informative() -> None:
    assert "news" in repr(NewsProvider())
