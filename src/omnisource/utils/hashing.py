"""Streaming SHA-256 helpers.

Hashing is deliberately independent of trust. A matching digest says that the
bytes match an expected value; it does not prove provenance or safety.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO

CHUNK_SIZE = 1024 * 1024


def calculate_sha256(stream: BinaryIO, *, chunk_size: int = CHUNK_SIZE) -> str:
    """Hash a binary stream without loading it into memory."""
    digest = hashlib.sha256()
    while chunk := stream.read(chunk_size):
        digest.update(chunk)
    return digest.hexdigest()


def hash_file(path: Path, *, chunk_size: int = CHUNK_SIZE) -> str:
    with path.open("rb") as stream:
        return calculate_sha256(stream, chunk_size=chunk_size)


# Friendly alias for callers using the wording in the public contract.
def sha256_file(path: Path, *, chunk_size: int = CHUNK_SIZE) -> str:
    return hash_file(path, chunk_size=chunk_size)


def verify_sha256(stream: BinaryIO, expected: str, *, chunk_size: int = CHUNK_SIZE) -> bool:
    if not isinstance(expected, str) or len(expected) != 64:
        return False
    try:
        int(expected, 16)
    except ValueError:
        return False
    actual = calculate_sha256(stream, chunk_size=chunk_size)
    return actual.casefold() == expected.casefold()


def verify_file_sha256(path: Path, expected: str, *, chunk_size: int = CHUNK_SIZE) -> bool:
    with path.open("rb") as stream:
        return verify_sha256(stream, expected, chunk_size=chunk_size)
