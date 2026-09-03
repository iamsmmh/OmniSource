"""Canonical application model shared by feeds and API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .release import Release


@dataclass(frozen=True)
class Application:
    """The normalized, platform-neutral application record.

    The JSON representation intentionally uses the names in the OmniStore
    contract. Values unavailable from an upstream are represented as ``null``
    or an empty array/string; this model never invents metadata.
    """

    id: str
    name: str
    developer: str = ""
    description: str = ""
    short_description: str = ""
    icon: str | None = None
    screenshots: tuple[str, ...] = ()
    category: str = "other"
    categories: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    repository: str | None = None
    source_type: str = "unknown"
    homepage: str | None = None
    documentation: str | None = None
    license: str | None = None
    platforms: tuple[str, ...] = ()
    bundle_id: str | None = None
    package_name: str | None = None
    minimum_ios_version: str | None = None
    minimum_android_version: str | None = None
    latest_version: str = ""
    latest_build: str | None = None
    latest_release_date: str = ""
    latest_release_notes: str = ""
    download_assets: tuple[dict[str, Any], ...] = ()
    versions: tuple[Release, ...] = ()
    status: str = "unknown"
    featured: bool = False
    verified: bool = False
    last_updated: str = ""
    health: dict[str, Any] = field(default_factory=dict)
    integrity: dict[str, Any] = field(default_factory=dict)
    aliases: tuple[str, ...] = ()
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the canonical contract with stable, explicit fields."""
        categories = list(self.categories or ((self.category,) if self.category else ()))
        payload: dict[str, Any] = {
            "id": self.id,
            "appId": self.id,
            "name": self.name,
            "developer": self.developer,
            "description": self.description,
            "shortDescription": self.short_description,
            "icon": self.icon,
            "screenshots": list(self.screenshots),
            "category": self.category,
            "categories": categories,
            "tags": list(self.tags),
            "repository": self.repository,
            "repositoryUrl": self.repository,
            "sourceType": self.source_type,
            "homepage": self.homepage,
            "documentation": self.documentation,
            "license": self.license,
            "platforms": list(self.platforms),
            "bundleId": self.bundle_id,
            "bundleIdentifier": self.bundle_id,
            "packageName": self.package_name,
            "minimumIOSVersion": self.minimum_ios_version,
            "minimumAndroidVersion": self.minimum_android_version,
            "minimumOSVersion": self.minimum_ios_version or self.minimum_android_version,
            "latestVersion": self.latest_version,
            "latestBuild": self.latest_build,
            "latestReleaseDate": self.latest_release_date,
            "latestReleaseNotes": self.latest_release_notes,
            "version": self.latest_version,
            "buildNumber": self.latest_build,
            "releaseDate": self.latest_release_date,
            "changelog": self.latest_release_notes,
            "downloadUrl": self._primary_download_url(),
            "downloadURL": self._primary_download_url(),
            "downloadAssets": list(self.download_assets),
            "versions": [release.to_dict() for release in self.versions],
            "status": self.status,
            "featured": self.featured,
            "verified": self.verified,
            "lastUpdated": self.last_updated,
            "health": dict(self.health),
            "integrity": dict(self.integrity),
            "aliases": list(self.aliases),
        }
        if self.extra:
            payload.update(self.extra)
        return payload

    def _primary_download_url(self) -> str | None:
        if self.download_assets:
            url = self.download_assets[0].get("downloadUrl")
            if url:
                return str(url)
        if self.versions and self.versions[0].assets:
            return self.versions[0].assets[0].download_url
        return None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Application:
        versions_raw = raw.get("versions")
        assets_raw = raw.get("downloadAssets")
        categories = raw.get("categories")
        tags = raw.get("tags")
        return cls(
            id=str(raw.get("id") or raw.get("appId") or ""),
            name=str(raw.get("name") or ""),
            developer=str(raw.get("developer") or raw.get("developerName") or ""),
            description=str(raw.get("description") or raw.get("localizedDescription") or ""),
            short_description=str(raw.get("shortDescription") or raw.get("subtitle") or ""),
            icon=(str(raw["icon"]) if raw.get("icon") else (str(raw["iconURL"]) if raw.get("iconURL") else None)),
            screenshots=tuple(str(item) for item in raw.get("screenshots", raw.get("screenshotURLs", [])) if item),
            category=str(raw.get("category") or "other"),
            categories=tuple(str(item) for item in categories if item) if isinstance(categories, list) else (),
            tags=tuple(str(item) for item in tags if item) if isinstance(tags, list) else (),
            repository=(
                str(raw["repository"])
                if raw.get("repository")
                else (str(raw["repositoryUrl"]) if raw.get("repositoryUrl") else None)
            ),
            source_type=str(raw.get("sourceType") or "unknown"),
            homepage=(str(raw["homepage"]) if raw.get("homepage") else None),
            documentation=(str(raw["documentation"]) if raw.get("documentation") else None),
            license=(str(raw["license"]) if raw.get("license") else None),
            platforms=tuple(str(item) for item in raw.get("platforms", []) if item),
            bundle_id=(str(raw["bundleId"]) if raw.get("bundleId") else None),
            package_name=(str(raw["packageName"]) if raw.get("packageName") else None),
            minimum_ios_version=(str(raw["minimumIOSVersion"]) if raw.get("minimumIOSVersion") else None),
            minimum_android_version=(str(raw["minimumAndroidVersion"]) if raw.get("minimumAndroidVersion") else None),
            latest_version=str(raw.get("latestVersion") or raw.get("version") or ""),
            latest_build=(str(raw["latestBuild"]) if raw.get("latestBuild") is not None else None),
            latest_release_date=str(raw.get("latestReleaseDate") or raw.get("releaseDate") or ""),
            latest_release_notes=str(raw.get("latestReleaseNotes") or raw.get("changelog") or ""),
            download_assets=tuple(item for item in assets_raw if isinstance(item, dict))
            if isinstance(assets_raw, list)
            else (),
            versions=tuple(Release.from_dict(item) for item in versions_raw if isinstance(item, dict))
            if isinstance(versions_raw, list)
            else (),
            status=str(raw.get("status") or "unknown"),
            featured=bool(raw.get("featured", False)),
            verified=bool(raw.get("verified", False)),
            last_updated=str(raw.get("lastUpdated") or ""),
            health=dict(raw.get("health") or {}) if isinstance(raw.get("health"), dict) else {},
            integrity=dict(raw.get("integrity") or {}) if isinstance(raw.get("integrity"), dict) else {},
            aliases=tuple(str(item) for item in raw.get("aliases", []) if item),
        )
