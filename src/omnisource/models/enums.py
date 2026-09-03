"""Enumerations used by the canonical OmniSource data contract."""

from __future__ import annotations

from enum import StrEnum


class Platform(StrEnum):
    """A client platform for which an installable or distributable asset exists."""

    IOS = "ios"
    IPADOS = "ipados"
    ANDROID = "android"
    MACOS = "macos"
    WINDOWS = "windows"
    LINUX = "linux"
    WEB = "web"
    UNKNOWN = "unknown"


class AssetFileType(StrEnum):
    """Known package/archive types. The value is intentionally extensible."""

    IPA = "IPA"
    APK = "APK"
    AAB = "AAB"
    ZIP = "ZIP"
    DMG = "DMG"
    EXE = "EXE"
    APPIMAGE = "AppImage"
    DEB = "DEB"
    OTHER = "other"


class ApplicationStatus(StrEnum):
    """Lifecycle state exposed to OmniStore clients.

    This is deliberately separate from the historical AltStore ``status``
    labels (stable, beta, manual, ...). The latter remains available for
    backwards compatibility; this enum describes observable lifecycle health,
    not whether a package is safe to install.
    """

    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    BROKEN = "broken"
    UNKNOWN = "unknown"


class SourceKind(StrEnum):
    """Supported source adapters."""

    GITHUB = "github"
    GITHUB_TAGS = "github-tags"
    GITLAB = "gitlab"
    CODEBERG = "codeberg"
    FORGEJO = "forgejo"
    JSON_FEED = "json-feed"
    ALTSTORE = "altstore"
    FEATHER = "feather"
    MANUAL = "manual"
