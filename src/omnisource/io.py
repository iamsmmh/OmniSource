"""Atomic JSON I/O.

Writes go through a temp file, are re-parsed to prove they are valid JSON,
then ``Path.replace``d. Unchanged payloads are not touched so the pipeline
stays idempotent (no empty commits).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_json(path: Path, data: Any) -> bool:
    """Atomically write ``data``; return True when the file actually changed."""
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == payload:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(payload, encoding="utf-8")
        json.loads(tmp.read_text(encoding="utf-8"))  # never publish invalid JSON
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)
    return True


def dumps(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
