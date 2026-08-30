# OmniSource consolidated script
# Generated from common.py + sync_youproextra.py + sync_ytmusic.py + build_feed.py

import json, os, sys, time, re, glob, datetime, urllib.request, urllib.error
from datetime import timezone

GH_TOKEN = os.environ.get("GH_TOKEN", "")

# =========================
# Utilities
# =========================

def fetch_json(url, max_retries=3):
    headers = {"User-Agent": "github-actions/omnisource-sync"}
    if GH_TOKEN:
        headers["Authorization"] = f"token {GH_TOKEN}"
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.URLError as e:
            if attempt == max_retries:
                print(f"::error::API request failed after {max_retries} attempts: {e}")
                sys.exit(1)
            wait = 2 ** attempt
            print(f"::warning::Retrying in {wait}s: {e}")
            time.sleep(wait)

def check_url_alive(url, timeout=10, max_retries=2):
    if not url:
        return False
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, method="HEAD"),
                timeout=timeout
            ) as resp:
                return 200 <= resp.status < 400
        except urllib.error.HTTPError as e:
            if e.code == 405:
                try:
                    with urllib.request.urlopen(
                        urllib.request.Request(url, method="GET"),
                        timeout=timeout
                    ) as r2:
                        return 200 <= r2.status < 400
                except Exception:
                    return False
            return False
        except Exception:
            if attempt < max_retries:
                time.sleep(1)
    return False

def atomic_write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    with open(tmp, "r", encoding="utf-8") as f:
        json.load(f)

    os.replace(tmp, path)

# =========================
# YouProEXTRA Sync
# =========================

SOURCE_REPO = "mrdrvt99/YouProEXTRA"

TAG_MAP = {
    "youmod-ipa": "youmod",
    "youproextra-ipa": "youpro",
    "ytkp-ipa": "ytkp",
    "ytkace-ipa": "ytkace",
}

FILES = {
    "youmod": "youmod.json",
    "youpro": "youpro.json",
    "ytkp": "ytkp.json",
    "ytkace": "ytkace.json",
}

YTLITE_PREFIX = "ytl-ipa"
YTLITE_FILE = "ytlite.json"

def fetch_all_releases(repo, max_pages=10):
    releases = []
    for page in range(1, max_pages + 1):
        batch = fetch_json(
            f"https://api.github.com/repos/{repo}/releases?per_page=100&page={page}"
        )
        if not batch:
            break
        releases.extend(batch)
        if len(batch) < 100:
            break
    return releases

def update_manifest(filename, download_url, size, ipa_name, date_str, body):
    if not os.path.exists(filename):
        return

    with open(filename, "r", encoding="utf-8") as f:
        source = json.load(f)

    apps = source.get("apps", [])
    if not apps:
        return

    app = apps[0]

    matches = re.findall(r"(\d+\.\d+\.\d+)", ipa_name)
    if not matches:
        return

    version = matches[0]
    desc = f"YouTube {version} | {ipa_name.replace('.ipa','')}"
    if body:
        desc += "\n\n" + body

    entry = {
        "version": version,
        "date": date_str,
        "localizedDescription": desc,
        "downloadURL": download_url,
        "size": size,
        "minOSVersion": "16.0"
    }

    app.update({
        "versions": [entry],
        "version": version,
        "versionDate": date_str,
        "versionDescription": desc,
        "downloadURL": download_url,
        "size": size
    })

    atomic_write_json(filename, source)

def sync_youproextra():
    releases = fetch_all_releases(SOURCE_REPO)

    published = [
        r for r in releases
        if not r["draft"] and not r["prerelease"]
    ]

    best = {}

    for release in published:
        tag = release["tag_name"]

        if tag.startswith("youproextra-noytlite-ipa"):
            continue

        if tag.startswith(YTLITE_PREFIX):
            continue

        for prefix, key in TAG_MAP.items():
            if tag.startswith(prefix) and key not in best:
                best[key] = release
                break

    for app_key, release in best.items():
        asset = next(
            (a for a in release.get("assets", []) if a["name"].endswith(".ipa")),
            None
        )

        if not asset:
            continue

        update_manifest(
            FILES[app_key],
            asset["browser_download_url"],
            asset["size"],
            asset["name"],
            (release.get("published_at") or "")[:10],
            (release.get("body") or "").strip()
        )

# =========================
# YTMusic Sync
# =========================

def sync_ytmusic():
    file_name = "ytmusic.json"

    if not os.path.exists(file_name):
        return

    releases = fetch_json(
        "https://api.github.com/repos/mrdrvt99/YTMusicUltimate/releases?per_page=5"
    )

    release = next(
        (r for r in releases if not r["draft"] and not r["prerelease"]),
        None
    )

    if not release:
        return

    asset = next(
        (a for a in release.get("assets", []) if a["name"].endswith(".ipa")),
        None
    )

    if not asset:
        return

    with open(file_name, "r", encoding="utf-8") as f:
        data = json.load(f)

    app = data["apps"][0]

    matches = re.findall(r"(\d+\.\d+(?:\.\d+)?)", asset["name"])

    if len(matches) >= 2:
        tweak_v, ytm_v = matches[0], matches[-1]
    elif len(matches) == 1:
        tweak_v = ytm_v = matches[0]
    else:
        tweak_v = ytm_v = release["tag_name"].lstrip("v")

    desc = (
        f"YTMusicUltimate {tweak_v} | "
        f"YTMusic {ytm_v} | "
        f"{asset['name'].replace('.ipa','')}"
    )

    entry = {
        "version": tweak_v,
        "date": (release.get("published_at") or "")[:10],
        "localizedDescription": desc,
        "downloadURL": asset["browser_download_url"],
        "size": asset["size"],
        "minOSVersion": "16.0"
    }

    app.update({
        "versions": [entry],
        "version": tweak_v,
        "versionDate": entry["date"],
        "versionDescription": desc,
        "downloadURL": asset["browser_download_url"],
        "size": asset["size"]
    })

    atomic_write_json(file_name, data)

# =========================
# Feed Builder
# =========================

SOURCE_OWNER = "iamsmmh"
BASE_URL = "https://iamsmmh.github.io/OmniSource"

FILE_CONFIG = {
    "uyouenhanced.json": ("uYouEnhanced.png", "com.google.ios.youtube", "arichornlover"),
    "spotiflac.json": ("SpotiFLAC.png", "com.zarzet.spotiflac", "Zarzet"),
    "ytkace.json": ("YouTube.png", "com.google.ios.youtube", "itzzace"),
    "youpro.json": ("YouTube.png", "com.google.ios.youtube", "alibusut"),
    "ytlite.json": ("YouTube.png", "com.google.ios.youtube", "dayanch96"),
    "ytkp.json": ("YouTube.png", "com.google.ios.youtube", "ikghd"),
    "ytmusic.json": ("YouTubeMusic.png", "com.google.ios.youtubemusic", "dayanch96"),
    "youmod.json": ("YouTube.png", "com.google.ios.youtube", "Tonwalter888"),
}

def standardize(app, icon_url, bundle_id, dev_name):
    app["bundleIdentifier"] = bundle_id
    app["iconURL"] = icon_url
    app["developerName"] = dev_name
    return app

def build_feed():
    apps_out = []

    for file_name, cfg in FILE_CONFIG.items():
        if not os.path.exists(file_name):
            continue

        with open(file_name, "r", encoding="utf-8") as f:
            data = json.load(f)

        icon_name, bundle_id, dev_name = cfg

        for app in data.get("apps", []):
            if check_url_alive(app.get("downloadURL", "")):
                apps_out.append(
                    standardize(
                        app,
                        f"{BASE_URL}/assets/{icon_name}",
                        bundle_id,
                        dev_name
                    )
                )

    atomic_write_json(
        "apps.json",
        {
            "name": "OmniSource",
            "identifier": "com.iamsmmh.omnisource",
            "website": BASE_URL,
            "apps": apps_out
        }
    )

# =========================
# Main
# =========================

def main():
    sync_youproextra()
    sync_ytmusic()
    build_feed()

if __name__ == "__main__":
    main()
