"""Storage ports and adapters for OmniSource domain data.

Business logic should not know whether the catalog is stored as committed JSON,
SQLite, PostgreSQL, or MySQL.  This module provides the deliberately small
repository contract used by orchestration code and two production adapters:

* :class:`JsonRepository` is the default Git-friendly adapter.  It writes one
  collection per JSON file and uses atomic replacement, so a failed build
  cannot leave a half-written document in ``data/``.
* :class:`DBAPIRepository` speaks the Python DB-API 2.0 protocol.  Passing a
  SQLite, psycopg, or mysqlclient connection changes storage without changing
  validators, enrichers, or feed generators.  SQL is parameterized throughout.

The adapters store JSON-compatible dictionaries only.  Keeping this boundary
narrow makes migration and backup straightforward and prevents persistence
concerns from leaking into the feed pipeline.
"""

from __future__ import annotations

import contextlib
import json
import re
import sqlite3
import threading
from collections.abc import Iterator, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, Self

from omnisource.io import atomic_write_many, atomic_write_text, dumps_pretty, read_json

Document = dict[str, Any]
_COLLECTION_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
_KEY_RE = re.compile(r"^[^/\\\x00]{1,255}$")


def _validate_collection(collection: str) -> str:
    if not isinstance(collection, str) or not _COLLECTION_RE.fullmatch(collection):
        raise ValueError(f"invalid repository collection: {collection!r}")
    return collection


def _validate_key(key: str) -> str:
    if not isinstance(key, str) or not _KEY_RE.fullmatch(key) or key in {".", ".."}:
        raise ValueError("repository keys must be non-empty and path-safe")
    return key


def _copy_document(document: Mapping[str, Any]) -> Document:
    # JSON round-tripping gives adapters consistent copy-on-read/write
    # semantics and rejects non-serializable values at the boundary.
    return json.loads(json.dumps(dict(document), ensure_ascii=False))


def utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


class Repository(Protocol):
    """Minimal persistence port consumed by the application services."""

    def get(self, collection: str, key: str) -> Document | None: ...

    def put(self, collection: str, key: str, document: Mapping[str, Any]) -> None: ...

    def delete(self, collection: str, key: str) -> bool: ...

    def list(self, collection: str) -> list[Document]: ...

    def count(self, collection: str) -> int: ...

    def transaction(self) -> Any: ...


class MemoryRepository:
    """Fast repository useful for tests, dry-runs, and plugin development."""

    def __init__(self, initial: Mapping[str, Mapping[str, Mapping[str, Any]]] | None = None) -> None:
        self._data: dict[str, dict[str, Document]] = {}
        self._lock = threading.RLock()
        for collection, records in (initial or {}).items():
            for key, document in records.items():
                self.put(collection, key, document)

    def get(self, collection: str, key: str) -> Document | None:
        _validate_collection(collection)
        _validate_key(key)
        with self._lock:
            document = self._data.get(collection, {}).get(key)
            return _copy_document(document) if document is not None else None

    def put(self, collection: str, key: str, document: Mapping[str, Any]) -> None:
        _validate_collection(collection)
        _validate_key(key)
        value = _copy_document(document)
        with self._lock:
            self._data.setdefault(collection, {})[key] = value

    def delete(self, collection: str, key: str) -> bool:
        _validate_collection(collection)
        _validate_key(key)
        with self._lock:
            return self._data.get(collection, {}).pop(key, None) is not None

    def list(self, collection: str) -> list[Document]:
        _validate_collection(collection)
        with self._lock:
            return [_copy_document(item) for item in self._data.get(collection, {}).values()]

    def count(self, collection: str) -> int:
        _validate_collection(collection)
        with self._lock:
            return len(self._data.get(collection, {}))

    @contextlib.contextmanager
    def transaction(self) -> Iterator[Self]:
        with self._lock:
            snapshot = {
                collection: {key: _copy_document(value) for key, value in records.items()}
                for collection, records in self._data.items()
            }
            try:
                yield self
            except BaseException:
                self._data = snapshot
                raise


class JsonRepository(MemoryRepository):
    """Atomic JSON-file adapter with optional in-memory write-through cache.

    A collection file has the shape ``{"schemaVersion": 1, "records": {}}``.
    Existing flat dictionaries are read as a compatibility format.  The
    adapter never follows a user-provided path outside ``root``.
    """

    def __init__(self, root: Path, *, cache: bool = True) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._cache_enabled = cache
        self._loaded: set[str] = set()
        self._transaction_depth = 0
        super().__init__()

    def _path(self, collection: str) -> Path:
        _validate_collection(collection)
        path = (self.root / f"{collection}.json").resolve()
        if self.root not in path.parents:
            raise ValueError("repository path escaped root")
        return path

    def _load(self, collection: str) -> None:
        if collection in self._loaded:
            return
        raw = read_json(self._path(collection))
        records: Any = raw.get("records", raw) if isinstance(raw, dict) else {}
        if isinstance(records, dict):
            for key, value in records.items():
                if isinstance(key, str) and _KEY_RE.fullmatch(key) and isinstance(value, dict):
                    self._data.setdefault(collection, {})[key] = _copy_document(value)
        self._loaded.add(collection)

    def _flush(self, collection: str) -> None:
        payload = {"schemaVersion": 1, "updatedAt": utcnow(), "records": self._data.get(collection, {})}
        atomic_write_text(self._path(collection), dumps_pretty(payload))

    def get(self, collection: str, key: str) -> Document | None:
        with self._lock:
            self._load(collection)
            return super().get(collection, key)

    def put(self, collection: str, key: str, document: Mapping[str, Any]) -> None:
        with self._lock:
            self._load(collection)
            super().put(collection, key, document)
            # A transaction stages all mutations in memory. Flushing here
            # would make a later rollback observable on disk.
            if self._transaction_depth == 0:
                self._flush(collection)

    def delete(self, collection: str, key: str) -> bool:
        with self._lock:
            self._load(collection)
            removed = super().delete(collection, key)
            if removed and self._transaction_depth == 0:
                self._flush(collection)
            return removed

    def list(self, collection: str) -> list[Document]:
        with self._lock:
            self._load(collection)
            return super().list(collection)

    def count(self, collection: str) -> int:
        with self._lock:
            self._load(collection)
            return super().count(collection)

    @contextlib.contextmanager
    def transaction(self) -> Iterator[Self]:
        """Stage a batch and persist it only after the outer block succeeds.

        Nested transactions are savepoints in memory. The outer transaction is
        the only one allowed to touch disk, so an exception raised after a
        ``put`` or ``delete`` cannot leak a partial mutation to a JSON file.
        """
        with self._lock:
            outer = self._transaction_depth == 0
            before = {
                collection: {key: _copy_document(value) for key, value in records.items()}
                for collection, records in self._data.items()
            }
            loaded_before = set(self._loaded)
            self._transaction_depth += 1
            try:
                yield self
            except BaseException:
                self._transaction_depth -= 1
                if outer:
                    self._data = before or {}
                    self._loaded = loaded_before or set()
                raise
            else:
                self._transaction_depth -= 1
                if outer:
                    changed = [
                        collection
                        for collection in self._loaded
                        if before is not None and before.get(collection) != self._data.get(collection)
                    ]
                    try:
                        documents = {
                            self._path(collection): {
                                "schemaVersion": 1,
                                "updatedAt": utcnow(),
                                "records": self._data.get(collection, {}),
                            }
                            for collection in changed
                        }
                        atomic_write_many(documents, pretty=lambda _path: True)
                    except BaseException:
                        # atomic_write_many restores every replaced target on
                        # filesystem failure. Keep the in-memory view aligned
                        # with that last-known-good disk state as well.
                        self._data = before
                        self._loaded = loaded_before
                        raise


class DBAPIRepository:
    """Repository backed by any DB-API 2.0 connection.

    ``placeholder`` is ``?`` for SQLite and usually ``%s`` for PostgreSQL and
    MySQL drivers.  The table is intentionally generic; domain-specific
    indexes can be added by a deployment migration without changing callers.
    """

    def __init__(self, connection: Any, *, placeholder: str = "?") -> None:
        if placeholder not in {"?", "%s"}:
            raise ValueError("placeholder must be '?' or '%s'")
        self.connection = connection
        self.placeholder = placeholder
        self._lock = threading.RLock()
        self._transaction_depth = 0
        self._ensure_schema()

    def _sql(self, statement: str) -> str:
        return statement.replace("?", self.placeholder)

    def _ensure_schema(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            self._sql(
                "CREATE TABLE IF NOT EXISTS omnisource_documents ("
                "collection VARCHAR(64) NOT NULL, "
                "document_key VARCHAR(255) NOT NULL, "
                "payload TEXT NOT NULL, updated_at VARCHAR(40) NOT NULL, "
                "PRIMARY KEY (collection, document_key))"
            )
        )
        self.connection.commit()
        cursor.close()

    def get(self, collection: str, key: str) -> Document | None:
        _validate_collection(collection)
        _validate_key(key)
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute(
                self._sql("SELECT payload FROM omnisource_documents WHERE collection = ? AND document_key = ?"),
                (collection, key),
            )
            row = cursor.fetchone()
            cursor.close()
        if not row:
            return None
        value = json.loads(row[0])
        return value if isinstance(value, dict) else None

    def put(self, collection: str, key: str, document: Mapping[str, Any]) -> None:
        _validate_collection(collection)
        _validate_key(key)
        payload = json.dumps(_copy_document(document), ensure_ascii=False, separators=(",", ":"))
        with self._lock:
            cursor = self.connection.cursor()
            # SQLite supports INSERT OR REPLACE; PostgreSQL/MySQL do not share
            # that syntax, so use an update followed by an insert. Both are
            # parameterized and remain portable across DB-API drivers.
            cursor.execute(
                self._sql(
                    "UPDATE omnisource_documents SET payload = ?, updated_at = ? "
                    "WHERE collection = ? AND document_key = ?"
                ),
                (payload, utcnow(), collection, key),
            )
            if getattr(cursor, "rowcount", 0) == 0:
                try:
                    cursor.execute(
                        self._sql(
                            "INSERT INTO omnisource_documents "
                            "(collection, document_key, payload, updated_at) VALUES (?, ?, ?, ?)"
                        ),
                        (collection, key, payload, utcnow()),
                    )
                except Exception:
                    # A concurrent writer may have inserted it between the
                    # update and insert; retry as an update within this tx.
                    cursor.execute(
                        self._sql(
                            "UPDATE omnisource_documents SET payload = ?, updated_at = ? "
                            "WHERE collection = ? AND document_key = ?"
                        ),
                        (payload, utcnow(), collection, key),
                    )
            if self._transaction_depth == 0:
                self.connection.commit()
            cursor.close()

    def delete(self, collection: str, key: str) -> bool:
        _validate_collection(collection)
        _validate_key(key)
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute(
                self._sql("DELETE FROM omnisource_documents WHERE collection = ? AND document_key = ?"),
                (collection, key),
            )
            changed = bool(getattr(cursor, "rowcount", 0))
            if self._transaction_depth == 0:
                self.connection.commit()
            cursor.close()
            return changed

    def list(self, collection: str) -> list[Document]:
        _validate_collection(collection)
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute(
                self._sql("SELECT payload FROM omnisource_documents WHERE collection = ? ORDER BY document_key"),
                (collection,),
            )
            rows = cursor.fetchall()
            cursor.close()
        return [value for row in rows if isinstance((value := json.loads(row[0])), dict)]

    def count(self, collection: str) -> int:
        _validate_collection(collection)
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute(
                self._sql("SELECT COUNT(*) FROM omnisource_documents WHERE collection = ?"),
                (collection,),
            )
            row = cursor.fetchone()
            cursor.close()
        return int(row[0]) if row else 0

    @contextlib.contextmanager
    def transaction(self) -> Iterator[Self]:
        """Group all writes in one DB-API transaction.

        ``put`` and ``delete`` intentionally do not commit while this context
        is active. Nested contexts use the driver's current transaction and
        only the outer context commits or rolls back it.
        """
        with self._lock:
            outer = self._transaction_depth == 0
            self._transaction_depth += 1
            try:
                yield self
            except BaseException:
                self._transaction_depth -= 1
                if outer:
                    self.connection.rollback()
                raise
            else:
                self._transaction_depth -= 1
                if outer:
                    self.connection.commit()


class SQLiteRepository(DBAPIRepository):
    """Convenience adapter for the future single-node SQLite deployment."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(sqlite3.connect(self.path, check_same_thread=False), placeholder="?")

    def close(self) -> None:
        self.connection.close()


RepositoryFactory = JsonRepository

__all__ = [
    "DBAPIRepository",
    "Document",
    "JsonRepository",
    "MemoryRepository",
    "Repository",
    "RepositoryFactory",
    "SQLiteRepository",
]
