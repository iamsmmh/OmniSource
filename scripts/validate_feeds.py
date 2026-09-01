#!/usr/bin/env python3
"""Validate OmniSource JSON feeds without making network requests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_APP_FIELDS = (
    "name",
    "bundleIdentifier",
    "developerName",
    "version",
    "versionDate",
    "downloadURL",
)
REQUIRED_VERSION_FIELDS = ("version", "date", "downloadURL", "size")


def is_http_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        with path.open(encoding="utf-8") as input_file:
            feed = json.load(input_file)
    except (OSError, json.JSONDecodeError) as error:
        return [f"{path.name}: cannot read valid JSON ({error})"]

    if not isinstance(feed, dict):
        return [f"{path.name}: root must be a JSON object"]

    apps = feed.get("apps")
    if not isinstance(apps, list) or not apps:
        return [f"{path.name}: apps must be a non-empty array"]

    for index, app in enumerate(apps):
        prefix = f"{path.name}: apps[{index}]"
        if not isinstance(app, dict):
            errors.append(f"{prefix} must be an object")
            continue

        for field in REQUIRED_APP_FIELDS:
            if not app.get(field):
                errors.append(f"{prefix} is missing {field}")
        if app.get("downloadURL") and not is_http_url(app["downloadURL"]):
            errors.append(f"{prefix}.downloadURL must be an HTTP(S) URL")

        versions = app.get("versions")
        if not isinstance(versions, list) or not versions:
            errors.append(f"{prefix}.versions must be a non-empty array")
            continue

        for version_index, version in enumerate(versions):
            version_prefix = f"{prefix}.versions[{version_index}]"
            if not isinstance(version, dict):
                errors.append(f"{version_prefix} must be an object")
                continue
            for field in REQUIRED_VERSION_FIELDS:
                if field not in version or version[field] in (None, ""):
                    errors.append(f"{version_prefix} is missing {field}")
            if version.get("downloadURL") and not is_http_url(version["downloadURL"]):
                errors.append(f"{version_prefix}.downloadURL must be an HTTP(S) URL")
            if "size" in version and (
                not isinstance(version["size"], int) or version["size"] < 0
            ):
                errors.append(f"{version_prefix}.size must be a non-negative integer")

        newest = versions[0]
        if isinstance(newest, dict):
            if app.get("version") != newest.get("version"):
                errors.append(f"{prefix}.version must match versions[0].version")
            if app.get("downloadURL") != newest.get("downloadURL"):
                errors.append(f"{prefix}.downloadURL must match versions[0].downloadURL")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="JSON files to validate (defaults to every root feed)",
    )
    args = parser.parse_args()
    paths = [REPO_ROOT / path for path in args.files] if args.files else sorted(REPO_ROOT.glob("*.json"))

    errors: list[str] = []
    for path in paths:
        if not path.is_file():
            errors.append(f"{path}: file not found")
            continue
        errors.extend(validate_file(path))

    if errors:
        for error in errors:
            print(f"::error::{error}")
        return 1

    print(f"Validated {len(paths)} feed(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
