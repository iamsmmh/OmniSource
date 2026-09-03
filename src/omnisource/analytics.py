"""Analytics foundation.

Interfaces only. OmniSource does not implement tracking: there is no
telemetry, no download counter, no phone-home. The :class:`AnalyticsSink`
protocol is the extension point a future OmniStore backend would implement
(Postgres, Prometheus, …). Production uses :class:`NullAnalytics`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AnalyticsSink(Protocol):
    """Record distribution events. Implementations must be side-effect free
    unless the operator has explicitly opted into a real backend."""

    def record_download(self, app_id: str, version: str) -> None:
        """A client fetched an IPA. Not called today."""

    def record_update(self, app_id: str, from_version: str, to_version: str) -> None:
        """An upstream version changed between syncs."""

    def record_repository_seen(self, repository_url: str, app_count: int) -> None:
        """A repository was observed as the upstream of ``app_count`` apps."""

    def record_health(self, app_id: str, reachable: bool) -> None:
        """A download URL probe completed."""


class NullAnalytics:
    """Default sink: discard every event. Safe to use in CI and Pages."""

    def record_download(self, app_id: str, version: str) -> None:
        return None

    def record_update(self, app_id: str, from_version: str, to_version: str) -> None:
        return None

    def record_repository_seen(self, repository_url: str, app_count: int) -> None:
        return None

    def record_health(self, app_id: str, reachable: bool) -> None:
        return None
