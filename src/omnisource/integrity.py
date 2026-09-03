"""Optional asset hashing and integrity verification.

Normal metadata synchronization uses upstream-provided digests when available.
Downloading and hashing a package is opt-in because IPA/APK files can be large.
Cached package bytes are kept outside Git (under ``.cache``) and bounded by
caller policy.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from omnisource.constants import USER_AGENT
from omnisource.errors import ProviderError
from omnisource.utils.hashing import CHUNK_SIZE, hash_file
from omnisource.utils.urls import is_public_http_url


@dataclass(frozen=True)
class IntegrityResult:
    url: str
    sha256: str | None
    size: int
    cached: bool = False
    verified: bool | None = None
    detail: str = ""


def _cache_path(cache_dir: Path, url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return cache_dir / "assets" / digest[:2] / digest


def download_and_hash(
    url: str,
    *,
    cache_dir: Path | None = None,
    expected_sha256: str | None = None,
    max_bytes: int = 512 * 1024 * 1024,
    timeout: float = 60.0,
) -> IntegrityResult:
    """Stream an asset to a bounded cache/temp file and calculate SHA-256.

    The request has no API credentials. A declared ``Content-Length`` larger
    than ``max_bytes`` is rejected before the body is read. The temporary file
    is atomically moved into the cache only after the complete hash succeeds.
    """
    if not is_public_http_url(url):
        raise ProviderError(f"cannot hash invalid asset URL: {url}")
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")
    target = _cache_path(cache_dir, url) if cache_dir else None
    if target and target.is_file():
        size = target.stat().st_size
        if size <= max_bytes:
            digest = hash_file(target)
            verified = expected_sha256.casefold() == digest if expected_sha256 else None
            return IntegrityResult(url, digest, size, cached=True, verified=verified, detail="cache hit")

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
    try:
        response = urllib.request.urlopen(request, timeout=timeout)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ProviderError(f"asset download failed: {url} ({error})") from error

    temp_parent = target.parent if target else Path(tempfile.gettempdir())
    temp_parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="omnisource-asset-", dir=temp_parent)
    os.close(fd)
    temp_path = Path(temp_name)
    total = 0
    digest = hashlib.sha256()
    try:
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > max_bytes:
            raise ProviderError(f"asset exceeds max_bytes ({content_length} > {max_bytes}): {url}")
        with temp_path.open("wb") as output:
            while chunk := response.read(CHUNK_SIZE):
                total += len(chunk)
                if total > max_bytes:
                    raise ProviderError(f"asset exceeds max_bytes ({max_bytes}): {url}")
                digest.update(chunk)
                output.write(chunk)
        actual = digest.hexdigest()
        verified = expected_sha256.casefold() == actual if expected_sha256 else None
        if expected_sha256 and not verified:
            raise ProviderError(f"SHA-256 mismatch for {url}: expected {expected_sha256}, got {actual}")
        if target:
            target.parent.mkdir(parents=True, exist_ok=True)
            temp_path.replace(target)
            temp_path = target
        return IntegrityResult(url, actual, total, cached=False, verified=verified, detail="downloaded")
    finally:
        if temp_path != target:
            temp_path.unlink(missing_ok=True)
        response.close()
