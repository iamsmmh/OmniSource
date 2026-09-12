"""Typed domain events and a small in-process event bus.

Events make the pipeline observable without coupling discovery, validation,
publication, and reporting to one another.  The bus is synchronous by default
(which keeps builds deterministic), while :meth:`EventBus.publish_async`
allows async consumers such as metrics exporters.  :class:`JsonlEventStore`
provides an append-only outbox for replay and audit; payloads are scrubbed for
common credential fields before they leave the process.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import re
import threading
import uuid
from collections import defaultdict
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar, Self

SECRET_KEY_RE = re.compile(r"(token|secret|password|authorization|webhook|api[_-]?key)", re.IGNORECASE)


def utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): "[redacted]" if SECRET_KEY_RE.search(str(key)) else _scrub(item) for key, item in value.items()
        }
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, tuple):
        return [_scrub(item) for item in value]
    return value


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base event envelope shared by all pipeline events."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: str = field(default_factory=utcnow)
    correlation_id: str = ""
    event_type: ClassVar[str] = "DomainEvent"

    def to_dict(self) -> dict[str, Any]:
        payload = _scrub(asdict(self))
        payload["eventType"] = self.event_type
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Self:
        values = dict(payload)
        values.pop("eventType", None)
        return cls(**{key: value for key, value in values.items() if key in cls.__dataclass_fields__})


@dataclass(frozen=True, kw_only=True)
class SourceDiscovered(DomainEvent):
    event_type: ClassVar[str] = "SourceDiscovered"
    source_id: str = ""
    source_url: str = ""
    source_type: str = "unknown"


@dataclass(frozen=True, kw_only=True)
class SourceValidated(DomainEvent):
    event_type: ClassVar[str] = "SourceValidated"
    source_id: str = ""
    valid: bool = False
    error_count: int = 0
    warning_count: int = 0


@dataclass(frozen=True, kw_only=True)
class SourcePublished(DomainEvent):
    event_type: ClassVar[str] = "SourcePublished"
    source_id: str = ""
    feed_url: str = ""
    app_count: int = 0


@dataclass(frozen=True, kw_only=True)
class AppUpdated(DomainEvent):
    event_type: ClassVar[str] = "AppUpdated"
    app_id: str = ""
    version: str = ""
    previous_version: str = ""
    release_url: str = ""


@dataclass(frozen=True, kw_only=True)
class FeedGenerated(DomainEvent):
    event_type: ClassVar[str] = "FeedGenerated"
    feed_name: str = ""
    feed_url: str = ""
    app_count: int = 0
    digest: str = ""


@dataclass(frozen=True, kw_only=True)
class WebsitePublished(DomainEvent):
    event_type: ClassVar[str] = "WebsitePublished"
    deployment_url: str = ""
    feed_version: str = ""
    page_count: int = 0


Event = DomainEvent
EventHandler = Callable[[DomainEvent], Any]


class EventBus:
    """Thread-safe in-process pub/sub with explicit subscription cleanup."""

    def __init__(self, *, store: JsonlEventStore | None = None) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._lock = threading.RLock()
        self.store = store

    def subscribe(self, event_type: str | type[DomainEvent], handler: EventHandler) -> Callable[[], None]:
        key = event_type if isinstance(event_type, str) else event_type.event_type
        with self._lock:
            self._handlers[key].append(handler)

        def unsubscribe() -> None:
            with self._lock:
                if handler in self._handlers.get(key, []):
                    self._handlers[key].remove(handler)

        return unsubscribe

    def publish(self, event: DomainEvent) -> int:
        if not isinstance(event, DomainEvent):
            raise TypeError("event bus accepts DomainEvent instances")
        if self.store is not None:
            self.store.append(event)
        with self._lock:
            handlers = [*self._handlers.get(event.event_type, []), *self._handlers.get("*", [])]
        for handler in handlers:
            handler(event)
        return len(handlers)

    async def publish_async(self, event: DomainEvent) -> int:
        """Publish to sync and async handlers without changing the event contract."""
        if not isinstance(event, DomainEvent):
            raise TypeError("event bus accepts DomainEvent instances")
        if self.store is not None:
            self.store.append(event)
        with self._lock:
            handlers = [*self._handlers.get(event.event_type, []), *self._handlers.get("*", [])]
        pending = []
        called = 0
        for handler in handlers:
            result = handler(event)
            called += 1
            if asyncio.iscoroutine(result):
                pending.append(result)
        if pending:
            await asyncio.gather(*pending)
        return called

    @contextlib.contextmanager
    def subscription(self, event_type: str | type[DomainEvent], handler: EventHandler) -> Iterator[None]:
        unsubscribe = self.subscribe(event_type, handler)
        try:
            yield
        finally:
            unsubscribe()


class JsonlEventStore:
    """Append-only, replayable JSONL event store.

    Writes are locked per process and each event is one line.  Rotation is
    explicit so a scheduled job can retain bounded logs without silently
    deleting operational history.
    """

    def __init__(self, path: Path, *, max_bytes: int = 25_000_000) -> None:
        self.path = Path(path)
        self.max_bytes = max(1_000, max_bytes)
        self._lock = threading.RLock()

    def append(self, event: DomainEvent) -> None:
        payload = json.dumps(event.to_dict(), ensure_ascii=False, separators=(",", ":"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            if self.path.exists() and self.path.stat().st_size >= self.max_bytes:
                self.path.replace(self.path.with_suffix(self.path.suffix + ".1"))
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(payload + "\n")

    def read(self, *, limit: int | None = None) -> list[dict[str, Any]]:
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        if limit is not None:
            lines = lines[-max(0, limit) :]
        events: list[dict[str, Any]] = []
        for line in lines:
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                events.append(value)
        return events


EVENT_TYPES: tuple[type[DomainEvent], ...] = (
    SourceDiscovered,
    SourceValidated,
    SourcePublished,
    AppUpdated,
    FeedGenerated,
    WebsitePublished,
)

__all__ = [
    "EVENT_TYPES",
    "AppUpdated",
    "DomainEvent",
    "Event",
    "EventBus",
    "FeedGenerated",
    "JsonlEventStore",
    "SourceDiscovered",
    "SourcePublished",
    "SourceValidated",
    "WebsitePublished",
]
