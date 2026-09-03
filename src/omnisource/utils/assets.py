"""Deterministic release-asset classification."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

_FILE_TYPES = {
    ".ipa": "IPA",
    ".apk": "APK",
    ".aab": "AAB",
    ".zip": "ZIP",
    ".dmg": "DMG",
    ".exe": "EXE",
    ".appimage": "AppImage",
    ".deb": "DEB",
}


def _filename(value: str) -> str:
    path = urlsplit(value).path if "://" in value else value
    return Path(path).name.lower()


def detect_file_type(filename_or_url: str) -> str:
    """Return a stable package type, or ``other`` for unknown extensions."""
    name = _filename(filename_or_url)
    for suffix, file_type in _FILE_TYPES.items():
        if name.endswith(suffix):
            return file_type
    return "other"


def detect_platform(filename_or_url: str, file_type: str | None = None) -> str:
    """Infer platform only from an unambiguous package extension/name."""
    name = _filename(filename_or_url)
    kind = file_type or detect_file_type(name)
    if kind == "IPA":
        return "ios"
    if kind in {"APK", "AAB"}:
        return "android"
    if kind == "DMG":
        return "macos"
    if kind == "EXE":
        return "windows"
    if kind == "AppImage" or kind == "DEB":
        return "linux"
    if any(token in name for token in ("ios", "ipados", "iphone", "ipad")):
        return "ios"
    if any(token in name for token in ("android", "apk")):
        return "android"
    if "mac" in name or "darwin" in name:
        return "macos"
    if "windows" in name or name.endswith(".msi"):
        return "windows"
    if "linux" in name:
        return "linux"
    return "unknown"


def detect_architecture(filename_or_url: str) -> str | None:
    """Infer common CPU labels from a filename; return ``None`` if absent."""
    name = _filename(filename_or_url)
    labels = (
        (("arm64", "aarch64", "armv8"), "arm64"),
        (("armv7", "armeabi-v7a", "arm32", "armv7l"), "armv7"),
        (("x86_64", "x86-64", "amd64"), "x86_64"),
        (("x86", "i386", "i686"), "x86"),
        (("universal", "fat", "all"), "universal"),
        (("riscv64", "risc-v64"), "riscv64"),
    )
    for needles, value in labels:
        if any(needle in name for needle in needles):
            return value
    return None


def detect_asset_metadata(filename: str, download_url: str, *, mime_type: str = "") -> dict[str, object]:
    """Return the canonical asset classification without network access."""
    file_type = detect_file_type(filename or download_url)
    return {
        "filename": filename,
        "downloadUrl": download_url,
        "platform": detect_platform(filename or download_url, file_type),
        "architecture": detect_architecture(filename or download_url),
        "fileType": file_type,
        "mimeType": mime_type or None,
        "installable": file_type in {"IPA", "APK", "AAB", "DMG", "EXE", "AppImage", "DEB"},
    }
