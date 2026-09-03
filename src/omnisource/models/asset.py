"""Canonical release asset model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .enums import AssetFileType, Platform


@dataclass(frozen=True)
class Asset:
    """A release file, installable or otherwise.

    ``sha256`` is an integrity value only. It must never be interpreted as a
    statement that a package is safe, trusted, or code-signed.
    """

    filename: str
    download_url: str
    platform: str = Platform.UNKNOWN.value
    architecture: str | None = None
    file_type: str = AssetFileType.OTHER.value
    size: int | None = None
    sha256: str | None = None
    mime_type: str | None = None
    installable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "downloadUrl": self.download_url,
            "platform": self.platform,
            "architecture": self.architecture,
            "fileType": self.file_type,
            "size": self.size,
            "sha256": self.sha256,
            "mimeType": self.mime_type,
            "installable": self.installable,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Asset:
        """Parse either canonical camelCase keys or common feed keys."""
        return cls(
            filename=str(raw.get("filename") or raw.get("name") or ""),
            download_url=str(raw.get("downloadUrl") or raw.get("downloadURL") or ""),
            platform=str(raw.get("platform") or Platform.UNKNOWN.value),
            architecture=(str(raw["architecture"]) if raw.get("architecture") is not None else None),
            file_type=str(raw.get("fileType") or raw.get("type") or AssetFileType.OTHER.value),
            size=(int(raw["size"]) if raw.get("size") is not None else None),
            sha256=(str(raw["sha256"]) if raw.get("sha256") else None),
            mime_type=(str(raw["mimeType"]) if raw.get("mimeType") else None),
            installable=bool(raw.get("installable", False)),
        )
