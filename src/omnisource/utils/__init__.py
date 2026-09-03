"""Small dependency-free utilities used by the sync and validation layers."""

from .assets import detect_architecture, detect_asset_metadata, detect_file_type, detect_platform
from .hashing import calculate_sha256, hash_file, verify_sha256
from .urls import is_https_url, normalise_url, url_host
from .versioning import Version, compare_versions, is_newer, parse_version

__all__ = [
    "Version",
    "calculate_sha256",
    "compare_versions",
    "detect_architecture",
    "detect_asset_metadata",
    "detect_file_type",
    "detect_platform",
    "hash_file",
    "is_https_url",
    "is_newer",
    "normalise_url",
    "parse_version",
    "url_host",
    "verify_sha256",
]
