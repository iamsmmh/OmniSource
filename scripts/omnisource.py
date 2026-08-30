# scripts/omnisource.py
# OmniSource — https://github.com/iamsmmh/OmniSource

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any

# =========================
# Configuration
# =========================

GH_TOKEN = os.getenv("GH_TOKEN", "")

GITHUB_API = "https://api.github.com"
BASE_URL = "https://iamsmmh.github.io/OmniSource"

PRIMARY_SOURCE = "https://github.com/iamsmmh/OmniSource"
PRIMARY_LOGO = "OmniSource.png"

YOU_PRO_EXTRA = "mrdrvt99/YouProEXTRA"
YTMUSIC_REPO = "mrdrvt99/YTMusicUltimate"

# =========================
# Individual app metadata
# Keep unchanged
# =========================

FILE_CONFIG: dict[str, tuple[str, str, str]] = {
    "uyouenhanced.json": (
        "uYouEnhanced.png",
        "com.google.ios.youtube",
        "arichornlover",
    ),
    "spotiflac.json": (
        "SpotiFLAC.png",
        "com.zarzet.spotiflac",
        "Zarzet",
    ),
    "ytkace.json": (
        "YouTube.png",
        "com.google.ios.youtube",
        "itzzace",
    ),
    "youpro.json": (
        "YouTube.png",
        "com.google.ios.youtube",
        "alibusut",
    ),
    "ytlite.json": (
        "YouTube.png",
        "com.google.ios.youtube",
        "dayanch96",
    ),
    "ytkp.json": (
        "YouTube.png",
        "com.google.ios.youtube",
        "ikghd",
    ),
    "ytmusic.json": (
        "YouTubeMusic.png",
        "com.google.ios.youtubemusic",
        "dayanch96",
    ),
    "youmod.json": (
        "YouTube.png",
        "com.google.ios.youtube",
        "Tonwalter888",
    ),
}

TAG_MAP = {
    "youmod-ipa": "youmod",
    "youproextra-ipa": "youpro",
    "ytkp-ipa": "ytkp",
    "ytkace-ipa": "ytkace",
}

MANIFESTS = {
    "youmod": "youmod.json",
    "youpro": "youpro.json",
    "ytkp": "ytkp.json",
    "ytkace": "ytkace.json",
}

IPA_RE = re.compile(r"(\d+\.\d+\.\d+)")
YTMUSIC_VERSION_RE = re.compile(r"(\d+\.\d+(?:\.\d+)?)")

HEADERS = {
    "User-Agent": "OmniSource-GitHub-Actions",
    "Accept": "application/vnd.github+json",
}

if GH_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GH_TOKEN}"


# =========================
# Utilities
# =========================

def request(
    url: str,
    *,
    method: str = "GET",
    timeout: int = 30,
    retries: int = 3,
) -> bytes | None:
    """Perform an HTTP request with retry and GitHub rate-limit handling."""

    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                url,
                method=method,
                headers=HEADERS,
            )

            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read()

        except urllib.error.HTTPError as error:
            retryable = error.code in {408, 429, 500, 502, 503, 504}

            if error.code == 403:
                remaining = error.headers.get("X-RateLimit-Remaining")

                if remaining == "0":
                    reset = error.headers.get("X-RateLimit-Reset")

                    if reset:
                        wait = max(
                            1,
                            int(reset) - int(time.time()) + 1,
                        )
                    else:
                        wait = min(60, 2 ** attempt)

                    print(
                        f"::warning::GitHub rate limit reached; "
                        f"waiting {wait}s"
                    )
                    time.sleep(wait)
                    continue

            if not retryable or attempt == retries:
                print(
                    f"::error::HTTP {error.code}: {url}"
                )
                return None

            wait = min(60, 2 ** attempt)
            print(
                f"::warning::HTTP {error.code}; "
                f"retrying in {wait}s"
            )
            time.sleep(wait)

        except (urllib.error.URLError, TimeoutError) as error:
            if attempt == retries:
                print(
                    f"::error::Request failed: {error}"
                )
                return None

            wait = min(60, 2 ** attempt)
            print(
                f"::warning::Network error; "
                f"retrying in {wait}s"
            )
            time.sleep(wait)

    return None


def fetch_json(url: str) -> Any:
    """Fetch and decode JSON, failing the workflow on API errors."""

    raw = request(url)

    if raw is None:
        sys.exit(1)

    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        print(
            f"::error::Invalid JSON from {url}: {error}"
        )
        sys.exit(1)


def url_alive(url: str) -> bool:
    """Check whether a download URL is reachable."""

    if not url:
        return False

    try:
        raw = request(
            url,
            method="HEAD",
            timeout=10,
            retries=2,
        )

        if raw is not None:
            return True

    except Exception:
        pass

    # Some hosts reject HEAD. Fall back to GET.
    try:
        raw = request(
            url,
            method="GET",
            timeout=10,
            retries=2,
        )
        return raw is not None

    except Exception:
        return False


def write_json(path: str, data: dict[str, Any]) -> None:
    """Atomically write validated JSON."""

    tmp = f"{path}.tmp"

    try:
        with open(tmp, "w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )
            file.write("\n")

        with open(tmp, "r", encoding="utf-8") as file:
            json.load(file)

        os.replace(tmp, path)

    except Exception as error:
        if os.path.exists(tmp):
            os.remove(tmp)

        print(
            f"::error::Failed writing {path}: {error}"
        )
        sys.exit(1)


def read_json(path: str) -> dict[str, Any] | None:
    """Read a JSON manifest safely."""

    if not os.path.exists(path):
        print(
            f"::warning::{path} not found; skipping"
        )
        return None

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("root JSON value is not an object")

        return data

    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(
            f"::error::Invalid manifest {path}: {error}"
        )
        return None


def published_releases(repo: str, pages: int = 10) -> list[dict[str, Any]]:
    """Return published releases, newest first."""

    result: list[dict[str, Any]] = []

    for page in range(1, pages + 1):
        url = (
            f"{GITHUB_API}/repos/{repo}/releases"
            f"?per_page=100&page={page}"
        )

        batch = fetch_json(url)

        if not isinstance(batch, list) or not batch:
            break

        result.extend(
            release
            for release in batch
            if not release.get("draft")
            and not release.get("prerelease")
        )

        if len(batch) < 100:
            break

    result.sort(
        key=lambda release: (
            release.get("published_at") or "",
            release.get("created_at") or "",
        ),
        reverse=True,
    )

    return result


def ipa_asset(release: dict[str, Any]) -> dict[str, Any] | None:
    """Return the first IPA asset from a release."""

    return next(
        (
            asset
            for asset in release.get("assets", [])
            if asset.get("name", "").lower().endswith(".ipa")
        ),
        None,
    )


# =========================
# YouProEXTRA Sync
# =========================

def update_manifest(
    filename: str,
    asset: dict[str, Any],
    release: dict[str, Any],
) -> None:
    data = read_json(filename)

    if not data:
        return

    apps = data.get("apps")

    if not isinstance(apps, list) or not apps:
        print(
            f"::warning::No apps found in {filename}"
        )
        return

    app = apps[0]

    if not isinstance(app, dict):
        print(
            f"::warning::Invalid app entry in {filename}"
        )
        return

    ipa_name = asset.get("name", "")
    match = IPA_RE.search(ipa_name)

    if not match:
        print(
            f"::warning::No version found in {ipa_name}"
        )
        return

    version = match.group(1)
    date = (release.get("published_at") or "")[:10]

    description = (
        f"YouTube {version} | "
        f"{ipa_name.removesuffix('.ipa')}"
    )

    body = (release.get("body") or "").strip()

    if body:
        description += f"\n\n{body}"

    entry = {
        "version": version,
        "date": date,
        "localizedDescription": description,
        "downloadURL": asset["browser_download_url"],
        "size": asset["size"],
        "minOSVersion": "16.0",
    }

    updated = {
        **app,
        "versions": [entry],
        "version": version,
        "versionDate": date,
        "versionDescription": description,
        "downloadURL": asset["browser_download_url"],
        "size": asset["size"],
    }

    # Avoid rewriting unchanged manifests.
    if updated == app:
        return

    apps[0] = updated
    write_json(filename, data)

    print(
        f"::notice::{filename} → {version}"
    )


def sync_youproextra() -> None:
    print("==> Syncing YouProEXTRA")

    best: dict[str, dict[str, Any]] = {}

    for release in published_releases(YOU_PRO_EXTRA):
        tag = release.get("tag_name", "")

        if (
            tag.startswith("youproextra-noytlite-ipa")
            or tag.startswith("ytl-ipa")
        ):
            continue

        for prefix, key in TAG_MAP.items():
            if tag.startswith(prefix) and key not in best:
                best[key] = release
                break

    for key, release in best.items():
        asset = ipa_asset(release)

        if not asset:
            print(
                f"::warning::No IPA asset for {key}"
            )
            continue

        update_manifest(
            MANIFESTS[key],
            asset,
            release,
        )


# =========================
# YTMusic Sync
# =========================

def sync_ytmusic() -> None:
    print("==> Syncing YTMusicUltimate")

    filename = "ytmusic.json"
    manifest = read_json(filename)

    if not manifest:
        return

    release = next(
        iter(published_releases(YTMUSIC_REPO, pages=1)),
        None,
    )

    if not release:
        print(
            "::warning::No published YTMusic release found"
        )
        return

    asset = ipa_asset(release)

    if not asset:
        print(
            "::warning::No YTMusic IPA asset found"
        )
        return

    apps = manifest.get("apps")

    if not isinstance(apps, list) or not apps:
        print(
            f"::warning::No apps found in {filename}"
        )
        return

    app = apps[0]

    if not isinstance(app, dict):
        return

    matches = YTMUSIC_VERSION_RE.findall(
        asset.get("name", "")
    )

    if len(matches) >= 2:
        tweak_version = matches[0]
        ytm_version = matches[-1]
    elif matches:
        tweak_version = ytm_version = matches[0]
    else:
        tweak_version = ytm_version = (
            release.get("tag_name", "").lstrip("v")
        )

    description = (
        f"YTMusicUltimate {tweak_version} | "
        f"YTMusic {ytm_version} | "
        f"{asset['name'].removesuffix('.ipa')}"
    )

    entry = {
        "version": tweak_version,
        "date": (release.get("published_at") or "")[:10],
        "localizedDescription": description,
        "downloadURL": asset["browser_download_url"],
        "size": asset["size"],
        "minOSVersion": "16.0",
    }

    updated = {
        **app,
        "versions": [entry],
        "version": tweak_version,
        "versionDate": entry["date"],
        "versionDescription": description,
        "downloadURL": asset["browser_download_url"],
        "size": asset["size"],
    }

    if updated == app:
        return

    apps[0] = updated
    write_json(filename, manifest)

    print(
        f"::notice::{filename} → {tweak_version}"
    )


# =========================
# Feed Builder
# =========================

def build_feed() -> None:
    print("==> Building OmniSource feed")

    apps: list[dict[str, Any]] = []

    for filename, (
        icon,
        bundle_id,
        developer,
    ) in FILE_CONFIG.items():

        data = read_json(filename)

        if not data:
            continue

        for app in data.get("apps", []):
            if not isinstance(app, dict):
                continue

            download_url = app.get("downloadURL", "")

            if not url_alive(download_url):
                print(
                    f"::warning::Unavailable URL in {filename}; "
                    f"skipping app"
                )
                continue

            standardized = {
                **app,
                "bundleIdentifier": bundle_id,
                "iconURL": f"{BASE_URL}/assets/{icon}",
                "developerName": developer,
            }

            apps.append(standardized)

    feed = {
        "name": "OmniSource",
        "identifier": "com.iamsmmh.omnisource",
        "website": PRIMARY_SOURCE,
        "iconURL": f"{BASE_URL}/assets/{PRIMARY_LOGO}",
        "apps": apps,
    }

    write_json("apps.json", feed)

    print(
        f"::notice::Generated apps.json "
        f"with {len(apps)} active apps"
    )


# =========================
# Main
# =========================

def main() -> None:
    print("========================================")
    print(" OmniSource Production Sync")
    print("========================================")

    sync_youproextra()
    sync_ytmusic()
    build_feed()

    print("========================================")
    print(" OmniSource sync completed successfully")
    print("========================================")


if __name__ == "__main__":
    main()
