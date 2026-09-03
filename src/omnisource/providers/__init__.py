"""Source providers.

Every provider implements :class:`omnisource.providers.base.SourceProvider`:

* ``discover_apps()``     — list apps at a repository / organisation / feed
* ``fetch_metadata()``    — identity, description, topics
* ``fetch_releases()``    — normalised :class:`RemoteRelease` values
* ``validate_repository()`` — existence + basic sanity

CamelCase aliases matching the platform contract (``discoverApps``, …) are
exposed on the ABC so both naming conventions work.
"""

from __future__ import annotations

from omnisource.providers.base import INCREMENTAL_UNCHANGED, SourceProvider
from omnisource.providers.registry import ProviderRegistry, build_default_registry

__all__ = [
    "INCREMENTAL_UNCHANGED",
    "ProviderRegistry",
    "SourceProvider",
    "build_default_registry",
]
