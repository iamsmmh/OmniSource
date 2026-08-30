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
# ============================================================
# Configuration
# ============================================================
GH_TOKEN = os.getenv("GH_TOKEN", "")
GITHUB_API = "https://api.github.com"
BASE_URL = "https://iamsmmh.github.io/OmniSource"
PRIMARY_SOURCE = "https://github.com/iamsmmh/OmniSource"
PRIMARY_LOGO = "OmniSource.png"
YOU_PRO_EXTRA = "mrdrvt99/YouProEXTRA"
YTMUSIC_REPO = "mrdrvt99/YTMusicUltimate"
UYOU_REPO = "arichornlover/uYouEnhanced"
SPOTIFLAC_REPO = "spotiflacapp/SpotiFLAC-Mobile"
# ============================================================
# Individual app metadata — unchanged
# ============================================================
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
# ============================================================
# Version patterns
# ============================================================
THREE_PART_VERSION_RE = re.compile(
    r"(\d+\.\d+\.\d+)"
)
VERSION_RE = re.compile(
    r"(\d+\.\d+(?:\.\d+)?)"
)
# ============================================================
# GitHub API headers
# GH_TOKEN is used ONLY for GitHub API requests.
# ============================================================
API_HEADERS = {
    "User-Agent": "OmniSource-GitHub-Actions",
    "Accept": "application/vnd.github+json",
}
if GH_TOKEN:
    API_HEADERS["Authorization"] = f"Bearer {GH_TOKEN}"
# ============================================================
# HTTP / GitHub API
# ============================================================
def api_request(
    url: str,
    timeout: int = 30,
    retries: int = 3,
) -> bytes | None:
    """Authenticated GitHub API request with retry handling."""
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(
                url,
                headers=API_HEADERS,
            )
            with urllib.request.urlopen(
                request,
                timeout=timeout,
            ) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code == 403:
                remaining = error.headers.get(
                    "X-RateLimit-Remaining"
                )
                if remaining == "0":
                    reset = error.headers.get(
                        "X-RateLimit-Reset"
                    )
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
            retryable = error.code in {
                408,
                429,
                500,
                502,
                503,
                504,
            }
            if not retryable or attempt == retries:
                print(
                    f"::error::GitHub API HTTP "
                    f"{error.code}: {url}"
                )
                return None
            wait = min(60, 2 ** attempt)
            print(
                f"::warning::HTTP {error.code}; "
                f"retrying in {wait}s"
            )
            time.sleep(wait)
        except (
            urllib.error.URLError,
            TimeoutError,
        ) as error:
            if attempt == retries:
                print(
                    f"::error::GitHub API request failed: "
                    f"{error}"
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
    """Fetch JSON from GitHub API."""
    raw = api_request(url)
    if raw is None:
        sys.exit(1)
    try:
        return json.loads(
            raw.decode("utf-8")
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as error:
        print(
            f"::error::Invalid JSON from {url}: {error}"
        )
        sys.exit(1)
# ============================================================
# Public download URL validation
# IMPORTANT: NO GH_TOKEN
# ============================================================
def url_alive(url: str) -> bool:
    """Check a public download URL without authentication."""
    if not url:
        return False
    headers = {
        "User-Agent": "OmniSource-GitHub-Actions",
    }
    # First try HEAD.
    try:
        request = urllib.request.Request(
            url,
            method="HEAD",
            headers=headers,
        )
        with urllib.request.urlopen(
            request,
            timeout=15,
        ) as response:
            return 200 <= response.status < 400
    except urllib.error.HTTPError as error:
        if error.code not in {403, 405}:
            return False
    except (
        urllib.error.URLError,
        TimeoutError,
    ):
        pass
    # Fallback: request only one byte.
    try:
        request = urllib.request.Request(
            url,
            headers={
                **headers,
                "Range": "bytes=0-0",
            },
        )
        with urllib.request.urlopen(
            request,
            timeout=15,
        ) as response:
            return response.status in {
                200,
                206,
            }
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
    ):
        return False
# ============================================================
# JSON helpers
# ============================================================
def read_json(
    path: str,
) -> dict[str, Any] | None:
    if not os.path.exists(path):
        print(
            f"::warning::{path} not found; skipping"
        )
        return None
    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)
        if not isinstance(data, dict):
            raise ValueError(
                "JSON root must be an object"
            )
        return data
    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
    ) as error:
        print(
            f"::error::Invalid manifest {path}: "
            f"{error}"
        )
        return None
def write_json(
    path: str,
    data: dict[str, Any],
) -> None:
    tmp = f"{path}.tmp"
    try:
        with open(
            tmp,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )
            file.write("\n")
        # Validate before replacement.
        with open(
            tmp,
            "r",
            encoding="utf-8",
        ) as file:
            json.load(file)
        os.replace(tmp, path)
    except Exception as error:
        if os.path.exists(tmp):
            os.remove(tmp)
        print(
            f"::error::Failed writing {path}: "
            f"{error}"
        )
        sys.exit(1)
# ============================================================
# Release helpers
# ============================================================
def published_releases(
    repo: str,
    pages: int = 10,
) -> list[dict[str, Any]]:
    releases: list[dict[str, Any]] = []
    for page in range(1, pages + 1):
        data = fetch_json(
            f"{GITHUB_API}/repos/{repo}/releases"
            f"?per_page=100&page={page}"
        )
        if not isinstance(data, list) or not data:
            break
        releases.extend(
            release
            for release in data
            if not release.get("draft")
            and not release.get("prerelease")
        )
        if len(data) < 100:
            break
    releases.sort(
        key=lambda release: (
            release.get("published_at") or "",
            release.get("created_at") or "",
        ),
        reverse=True,
    )
    return releases
def ipa_asset(
    release: dict[str, Any],
) -> dict[str, Any] | None:
    return next(
        (
            asset
            for asset in release.get("assets", [])
            if asset.get("name", "")
            .lower()
            .endswith(".ipa")
        ),
        None,
    )
# ============================================================
# YouProEXTRA
# ============================================================
def sync_youproextra() -> None:
    print("==> Syncing YouProEXTRA")
    best: dict[str, dict[str, Any]] = {}
    for release in published_releases(
        YOU_PRO_EXTRA
    ):
        tag = release.get(
            "tag_name",
            "",
        )
        if (
            tag.startswith(
                "youproextra-noytlite-ipa"
            )
            or tag.startswith("ytl-ipa")
        ):
            continue
        for prefix, key in TAG_MAP.items():
            if (
                tag.startswith(prefix)
                and key not in best
            ):
                best[key] = release
                break
    for key, release in best.items():
        asset = ipa_asset(release)
        if not asset:
            print(
                f"::warning::No IPA asset for {key}"
            )
            continue
        filename = MANIFESTS[key]
        data = read_json(filename)
        if not data:
            continue
        apps = data.get("apps")
        if not isinstance(apps, list) or not apps:
            continue
        app = apps[0]
        if not isinstance(app, dict):
            continue
        name = asset.get("name", "")
        match = THREE_PART_VERSION_RE.search(name)
        if not match:
            print(
                f"::warning::No version found in {name}"
            )
            continue
        version = match.group(1)
        date = (
            release.get("published_at") or ""
        )[:10]
        description = (
            f"YouTube {version} | "
            f"{name.removesuffix('.ipa')}"
        )
        body = (
            release.get("body") or ""
        ).strip()
        if body:
            description += f"\n\n{body}"
        entry = {
            "version": version,
            "date": date,
            "localizedDescription": description,
            "downloadURL": asset[
                "browser_download_url"
            ],
            "size": asset["size"],
            "minOSVersion": "16.0",
        }
        updated = {
            **app,
            "versions": [entry],
            "version": version,
            "versionDate": date,
            "versionDescription": description,
            "downloadURL": asset[
                "browser_download_url"
            ],
            "size": asset["size"],
        }
        if updated == app:
            continue
        apps[0] = updated
        write_json(filename, data)
        print(
            f"::notice::{filename} → {version}"
        )
# ============================================================
# YTMusicUltimate
# ============================================================
def sync_ytmusic() -> None:
    print("==> Syncing YTMusicUltimate")
    filename = "ytmusic.json"
    data = read_json(filename)
    if not data:
        return
    release = next(
        iter(
            published_releases(
                YTMUSIC_REPO,
                pages=1,
            )
        ),
        None,
    )
    if not release:
        print(
            "::warning::No YTMusic release found"
        )
        return
    asset = ipa_asset(release)
    if not asset:
        print(
            "::warning::No YTMusic IPA found"
        )
        return
    apps = data.get("apps")
    if not isinstance(apps, list) or not apps:
        return
    app = apps[0]
    if not isinstance(app, dict):
        return
    matches = VERSION_RE.findall(
        asset.get("name", "")
    )
    if len(matches) >= 2:
        tweak_version = matches[0]
        ytm_version = matches[-1]
    elif len(matches) == 1:
        tweak_version = ytm_version = matches[0]
    else:
        tweak_version = ytm_version = (
            release.get("tag_name", "")
            .lstrip("v")
        )
    date = (
        release.get("published_at") or ""
    )[:10]
    description = (
        f"YTMusicUltimate {tweak_version} | "
        f"YTMusic {ytm_version} | "
        f"{asset['name'].removesuffix('.ipa')}"
    )
    entry = {
        "version": tweak_version,
        "date": date,
        "localizedDescription": description,
        "downloadURL": asset[
            "browser_download_url"
        ],
        "size": asset["size"],
        "minOSVersion": "16.0",
    }
    updated = {
        **app,
        "versions": [entry],
        "version": tweak_version,
        "versionDate": date,
        "versionDescription": description,
        "downloadURL": asset[
            "browser_download_url"
        ],
        "size": asset["size"],
    }
    if updated == app:
        return
    apps[0] = updated
    write_json(filename, data)
    print(
        f"::notice::{filename} → {tweak_version}"
    )
# ============================================================
# uYouEnhanced
# ============================================================
def sync_uyouenhanced() -> None:
    print("==> Syncing uYouEnhanced")
    filename = "uyouenhanced.json"
    data = read_json(filename)
    if not data:
        return
    release = next(
        iter(
            published_releases(
                UYOU_REPO,
                pages=1,
            )
        ),
        None,
    )
    if not release:
        print(
            "::warning::No uYouEnhanced release found"
        )
        return
    asset = ipa_asset(release)
    if not asset:
        print(
            "::warning::No uYouEnhanced IPA found"
        )
        return
    apps = data.get("apps")
    if not isinstance(apps, list) or not apps:
        return
    app = apps[0]
    if not isinstance(app, dict):
        return
    name = asset.get("name", "")
    matches = VERSION_RE.findall(name)
    version = (
        matches[0]
        if matches
        else release.get(
            "tag_name",
            "",
        ).lstrip("v")
    )
    date = (
        release.get("published_at") or ""
    )[:10]
    description = (
        f"uYouEnhanced {version} | "
        f"{name.removesuffix('.ipa')}"
    )
    body = (
        release.get("body") or ""
    ).strip()
    if body:
        description += f"\n\n{body}"
    entry = {
        "version": version,
        "date": date,
        "localizedDescription": description,
        "downloadURL": asset[
            "browser_download_url"
        ],
        "size": asset["size"],
        "minOSVersion": "16.0",
    }
    updated = {
        **app,
        "versions": [entry],
        "version": version,
        "versionDate": date,
        "versionDescription": description,
        "downloadURL": asset[
            "browser_download_url"
        ],
        "size": asset["size"],
    }
    if updated == app:
        return
    apps[0] = updated
    write_json(filename, data)
    print(
        f"::notice::{filename} → {version}"
    )
# ============================================================
# SpotiFLAC
# ============================================================
def sync_spotiflac() -> None:
    print("==> Syncing SpotiFLAC")
    filename = "spotiflac.json"
    data = read_json(filename)
    if not data:
        return
    release = next(
        iter(
            published_releases(
                SPOTIFLAC_REPO,
                pages=1,
            )
        ),
        None,
    )
    if not release:
        print(
            "::warning::No SpotiFLAC release found"
        )
        return
    asset = ipa_asset(release)
    if not asset:
        print(
            "::warning::No SpotiFLAC IPA found"
        )
        return
    apps = data.get("apps")
    if not isinstance(apps, list) or not apps:
        return
    app = apps[0]
    if not isinstance(app, dict):
        return
    name = asset.get("name", "")
    matches = VERSION_RE.findall(name)
    version = (
        matches[0]
        if matches
        else release.get(
            "tag_name",
            "",
        ).lstrip("v")
    )
    date = (
        release.get("published_at") or ""
    )[:10]
    description = (
        f"SpotiFLAC {version} | "
        f"{name.removesuffix('.ipa')}"
    )
    body = (
        release.get("body") or ""
    ).strip()
    if body:
        description += f"\n\n{body}"
    entry = {
        "version": version,
        "date": date,
        "localizedDescription": description,
        "downloadURL": asset[
            "browser_download_url"
        ],
        "size": asset["size"],
        "minOSVersion": "16.0",
    }
    updated = {
        **app,
        "versions": [entry],
        "version": version,
        "versionDate": date,
        "versionDescription": description,
        "downloadURL": asset[
            "browser_download_url"
        ],
        "size": asset["size"],
    }
    if updated == app:
        return
    apps[0] = updated
    write_json(filename, data)
    print(
        f"::notice::{filename} → {version}"
    )
# ============================================================
# Feed Builder
# ============================================================
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
            download_url = app.get(
                "downloadURL",
                "",
            )
            # Public URL check.
            # GH_TOKEN is intentionally NOT used.
            if not url_alive(download_url):
                print(
                    f"::warning::Unavailable public "
                    f"download URL in {filename}; "
                    f"skipping"
                )
                continue
            apps.append({
                **app,
                "bundleIdentifier": bundle_id,
                "iconURL": (
                    f"{BASE_URL}/assets/{icon}"
                ),
                "developerName": developer,
            })
    feed = {
        "name": "OmniSource",
        "identifier": "com.iamsmmh.omnisource",
        "website": PRIMARY_SOURCE,
        "iconURL": (
            f"{BASE_URL}/assets/{PRIMARY_LOGO}"
        ),
        "apps": apps,
    }
    write_json(
        "apps.json",
        feed,
    )
    print(
        f"::notice::apps.json generated with "
        f"{len(apps)} active apps"
    )
# ============================================================
# Main
# ============================================================
def main() -> None:
    print("========================================")
    print(" OmniSource Production Sync")
    print("========================================")
    sync_youproextra()
    sync_ytmusic()
    sync_uyouenhanced()
    sync_spotiflac()
    build_feed()
    print("========================================")
    print(" OmniSource sync completed successfully")
    print("========================================")
if __name__ == "__main__":
    main()
