"""Domain exception hierarchy.

All failures crossing a provider boundary are normalized into
:class:`ProviderError` subclasses so the engine never has to catch
transport-library-specific exceptions.
"""

from __future__ import annotations


class OmniSourceError(Exception):
    """Base class for every error raised by OmniSource."""


class ConfigurationError(OmniSourceError):
    """Raised when the runtime configuration is invalid or incomplete."""


class ProviderError(OmniSourceError):
    """Base class for provider-side failures."""

    def __init__(self, provider: str, message: str) -> None:
        super().__init__(f"[{provider}] {message}")
        self.provider = provider
        self.message = message


class ProviderTimeoutError(ProviderError):
    """The provider exceeded its allotted deadline."""


class ProviderUnavailableError(ProviderError):
    """The provider is reachable but refused or failed to serve the request."""


class CacheError(OmniSourceError):
    """The cache backend misbehaved; always non-fatal for the pipeline."""
