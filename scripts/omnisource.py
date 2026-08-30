# scripts/omnisource.py
# OmniSource — https://github.com/iamsmmh/OmniSource

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

GH_TOKEN = os.getenv("GH_TOKEN", "")

# =========================
# Primary OmniSource
# =========================

BASE_URL = "https://iamsmmh.github.io/OmniSource"
PRIMARY_SOURCE = "https://github.com/iamsmmh/OmniSource"
PRIMARY_LOGO = "OmniSource.png"

# =========================
# Utilities
# =========================

def fetch_json(url, retries=3):
    headers = {
        "User-Agent": "github-actions/omnisource-sync",
        "Accept": "application/vnd.github+json",
    }
    if GH_TOKEN:
        headers["Authorization"] = f"Bearer {GH_TOKEN}"

    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, json.JSONDecodeError) as error:
            if attempt == retries:
                print(f"::error::Request failed: {error}")
                sys.exit(1)
            wait = 2 ** attempt
            print(f"::warning::Retrying in {wait}s: {error}")
            time.sleep(wait)


def url_alive(url, retries=2):
    if not url:
        return False

    headers = {"User-Agent": "github-actions/omnisource-sync"}

    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers=headers,
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return 200 <= response.status < 400

        except urllib.error.HTTPError as error:
            if error.code == 405:
                try:
                    req = urllib.request.Request(
                        url,
                        headers=headers,
                    )
                    with urllib.request.urlopen(req, timeout=10) as response:
                        return 200 <= response.status < 400
                except Exception:
                    return False
            return False

        except Exception:
            if attempt < retries - 1:
                time.sleep(1)

    return False


def write_json(path, data):
    tmp = f"{path}.tmp"

    with open(tmp, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")

    with open(tmp, "r", encoding="utf-8") as file:
        json.load(file)

    os.replace(tmp, path)


def releases(repo, pages=10):
    result = []

    for page in range(1, pages + 1):
        batch = fetch_json(
            f"https://api.github.com/repos/{repo}/releases"
            f"?per_page=100&page={page}"
        )

        if not batch:
            break

        result.extend(batch)

        if len(batch) < 100:
            break

    return result


# =========================
# YouProEXTRA
# =========================

SOURCE_REPO = "mrdrvt99/YouProEXTRA"

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


def update_manifest(file_name, asset, release):
    if not os.path.exists(file_name):
        return

    with open(file_name, "r", encoding="utf-8") as file:
        data = json.load(file)

    apps = data.get("apps", [])
    if not apps:
        return

    name = asset["name"]
    versions = re.findall(r"(\d+\.\d+\.\d+)", name)

    if not versions:
        return

    version = versions[0]
    date = (release.get("published_at") or "")[:10]
    description = f"YouTube {version} | {name.removesuffix('.ipa')}"

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

    apps[0].update({
        "versions": [entry],
        "version": version,
        "versionDate": date,
        "versionDescription": description,
        "downloadURL": asset["browser_download_url"],
        "size": asset["size"],
    })

    write_json(file_name, data)


def sync_youproextra():
    best = {}

    for release in releases(SOURCE_REPO):
        if release.get("draft") or release.get("prerelease"):
            continue

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
        asset = next(
            (
                asset
                for asset in release.get("assets", [])
                if asset.get("name", "").endswith(".ipa")
            ),
            None,
        )

        if asset:
            update_manifest(
                MANIFESTS[key],
                asset,
                release,
            )


# =========================
# YTMusicUltimate
# =========================

def sync_ytmusic():
    file_name = "ytmusic.json"

    if not os.path.exists(file_name):
        return

    data = fetch_json(
        "https://api.github.com/repos/mrdrvt99/YTMusicUltimate/releases"
        "?per_page=5"
    )

    release = next(
        (
            item
            for item in data
            if not item.get("draft")
            and not item.get("prerelease")
        ),
        None,
    )

    if not release:
        return

    asset = next(
        (
            item
            for item in release.get("assets", [])
            if item.get("name", "").endswith(".ipa")
        ),
        None,
    )

    if not asset:
        return

    with open(file_name, "r", encoding="utf-8") as file:
        manifest = json.load(file)

    apps = manifest.get("apps", [])
    if not apps:
        return

    matches = re.findall(
        r"(\d+\.\d+(?:\.\d+)?)",
        asset["name"],
    )

    if len(matches) >= 2:
        tweak_version, ytm_version = matches[0], matches[-1]
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

    apps[0].update({
        "versions": [entry],
        "version": tweak_version,
        "versionDate": entry["date"],
        "versionDescription": description,
        "downloadURL": asset["browser_download_url"],
        "size": asset["size"],
    })

    write_json(file_name, manifest)


# =========================
# Feed Builder
# =========================

# Individual app logos, bundle IDs and developer names
# intentionally remain unchanged.

FILE_CONFIG = {
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


def build_feed():
    apps = []

    for file_name, (
        icon,
        bundle_id,
        developer,
    ) in FILE_CONFIG.items():

        if not os.path.exists(file_name):
            continue

        try:
            with open(file_name, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            continue

        for app in data.get("apps", []):
            if not url_alive(app.get("downloadURL", "")):
                continue

            app["bundleIdentifier"] = bundle_id
            app["iconURL"] = f"{BASE_URL}/assets/{icon}"
            app["developerName"] = developer

            apps.append(app)

    write_json(
        "apps.json",
        {
            "name": "OmniSource",
            "identifier": "com.iamsmmh.omnisource",
            "website": PRIMARY_SOURCE,
            "iconURL": f"{BASE_URL}/assets/{PRIMARY_LOGO}",
            "apps": apps,
        },
    )

    print(f"::notice::OmniSource feed: {len(apps)} active apps")


# =========================
# Main
# =========================

def main():
    print("==> OmniSource sync started")

    sync_youproextra()
    sync_ytmusic()
    build_feed()

    print("==> OmniSource sync completed")


if __name__ == "__main__":
    main()
