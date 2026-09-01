"""Provider adapters and the registry that composes them."""

from omnisource.providers.base import BaseProvider
from omnisource.providers.registry import ProviderRegistry
from omnisource.providers.samples import (
    ArchiveProvider,
    CatalogProvider,
    NewsProvider,
    SimulatedProvider,
)

__all__ = [
    "ArchiveProvider",
    "BaseProvider",
    "CatalogProvider",
    "NewsProvider",
    "ProviderRegistry",
    "SimulatedProvider",
]
