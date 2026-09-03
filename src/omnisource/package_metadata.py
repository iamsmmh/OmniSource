"""Optional metadata extraction from IPA/APK packages.

Inspection is deliberately best-effort and never part of the normal sync
network path. IPA Info.plist files are handled with the Python standard
library, including Apple's binary plist format. APK inspection supports plain
XML manifests; binary Android manifests are reported as unavailable unless a
caller supplies an external parser.
"""

from __future__ import annotations

import plistlib
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PackageMetadata:
    package_type: str
    bundle_id: str | None = None
    package_name: str | None = None
    display_name: str | None = None
    version: str | None = None
    build: str | None = None
    minimum_os_version: str | None = None
    minimum_sdk: int | None = None
    target_sdk: int | None = None
    warnings: tuple[str, ...] = ()
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "packageType": self.package_type,
            "bundleId": self.bundle_id,
            "packageName": self.package_name,
            "displayName": self.display_name,
            "version": self.version,
            "build": self.build,
            "minimumOSVersion": self.minimum_os_version,
            "minimumSdk": self.minimum_sdk,
            "targetSdk": self.target_sdk,
            "warnings": list(self.warnings),
        }


def inspect_package(path: Path, *, package_type: str | None = None) -> PackageMetadata:
    """Inspect an IPA/APK ZIP without executing anything from the archive."""
    kind = (package_type or path.suffix.lstrip(".")).upper()
    if kind not in {"IPA", "APK"}:
        return PackageMetadata(kind.lower() or "unknown", warnings=("unsupported package type",))
    try:
        with zipfile.ZipFile(path) as archive:
            if kind == "IPA":
                return _inspect_ipa(archive)
            return _inspect_apk(archive)
    except (OSError, zipfile.BadZipFile) as error:
        return PackageMetadata(kind.lower(), warnings=(f"package could not be opened: {error}",))


def _inspect_ipa(archive: zipfile.ZipFile) -> PackageMetadata:
    candidates = sorted(
        name for name in archive.namelist() if name.startswith("Payload/") and name.endswith(".app/Info.plist")
    )
    if not candidates:
        return PackageMetadata("ipa", warnings=("Payload/*.app/Info.plist not found",))
    try:
        raw = plistlib.loads(archive.read(candidates[0]))
    except (KeyError, plistlib.InvalidFileException, ValueError) as error:
        return PackageMetadata("ipa", warnings=(f"Info.plist could not be parsed: {error}",))
    if not isinstance(raw, dict):
        return PackageMetadata("ipa", warnings=("Info.plist is not a dictionary",))
    return PackageMetadata(
        package_type="ipa",
        bundle_id=_string(raw.get("CFBundleIdentifier")),
        display_name=_string(raw.get("CFBundleDisplayName")) or _string(raw.get("CFBundleName")),
        version=_string(raw.get("CFBundleShortVersionString")),
        build=_string(raw.get("CFBundleVersion")),
        minimum_os_version=_string(raw.get("MinimumOSVersion")),
        raw={
            key: raw[key]
            for key in ("CFBundleIdentifier", "CFBundleShortVersionString", "CFBundleVersion", "MinimumOSVersion")
            if key in raw
        },
    )


def _inspect_apk(archive: zipfile.ZipFile) -> PackageMetadata:
    name = "AndroidManifest.xml"
    if name not in archive.namelist():
        return PackageMetadata("apk", warnings=("AndroidManifest.xml not found",))
    payload = archive.read(name)
    # Android manifests are untrusted archive input. Reject declarations that
    # enable entity expansion and cap the parser input before using the
    # standard-library XML parser (which does not fetch external entities).
    if len(payload) > 8 * 1024 * 1024 or b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
        return PackageMetadata("apk", warnings=("AndroidManifest.xml contains unsupported XML declarations",))
    try:
        root = ET.fromstring(payload)  # noqa: S314
    except ET.ParseError:
        return PackageMetadata("apk", warnings=("binary AndroidManifest.xml requires aapt/apkanalyzer",))
    android_ns = "{http://schemas.android.com/apk/res/android}"
    attrs = root.attrib
    version_code = attrs.get(android_ns + "versionCode")
    min_sdk = attrs.get(android_ns + "minSdkVersion")
    target_sdk = attrs.get(android_ns + "targetSdkVersion")
    return PackageMetadata(
        package_type="apk",
        package_name=attrs.get("package"),
        display_name=None,
        version=attrs.get(android_ns + "versionName"),
        build=version_code,
        minimum_sdk=_as_int(min_sdk),
        target_sdk=_as_int(target_sdk),
        raw={"package": attrs.get("package"), "versionName": attrs.get(android_ns + "versionName")},
    )


def _string(value: object) -> str | None:
    return str(value) if value not in (None, "") else None


def _as_int(value: object) -> int | None:
    try:
        return int(str(value)) if value not in (None, "") else None
    except ValueError:
        return None
