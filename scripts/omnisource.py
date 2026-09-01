import glob
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime as dt, timezone

# =====================================================================
# SHARED HELPERS
# =====================================================================

def fetch_json(url, max_retries=3):
    """Fetch a GitHub API response with bounded retries.

    Authentication is deliberately limited to this API helper.  Download
    URLs are third-party input and must never receive the repository token.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-actions/omnisource-sync",
    }
    token = os.environ.get("GH_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for attempt in range(1, max_retries + 1):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
                json.JSONDecodeError) as error:
            if attempt == max_retries:
                print(f"::error::API request failed after {max_retries} attempts: {error}")
                raise RuntimeError(f"Could not fetch GitHub API response: {url}") from error
            wait = 2 ** attempt
            print(
                f"::warning::Request failed (attempt {attempt}/{max_retries}), "
                f"retrying in {wait}s: {error}"
            )
            time.sleep(wait)


def check_url_alive(url, timeout=10, max_retries=2):
    """Check an arbitrary download URL without sending GitHub credentials.

    Some release/CDN servers reject HEAD.  The fallback is a one-byte ranged
    GET so a failed HEAD check never downloads an entire IPA into the runner.
    Transient 429/5xx responses are retried; permanent failures are not.
    """
    if not isinstance(url, str) or not url:
        return False
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False

    valid_codes = {200, 206, 301, 302, 307, 308}
    headers = {"User-Agent": "github-actions/omnisource-sync"}
    for attempt in range(1, max_retries + 1):
        try:
            request = urllib.request.Request(url, headers=headers, method="HEAD")
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.status in valid_codes
        except urllib.error.HTTPError as error:
            if error.code in valid_codes:
                return True
            if error.code == 405:
                try:
                    fallback_headers = {**headers, "Range": "bytes=0-0"}
                    request = urllib.request.Request(url, headers=fallback_headers)
                    with urllib.request.urlopen(request, timeout=timeout) as response:
                        return response.status in valid_codes
                except urllib.error.HTTPError as fallback_error:
                    if fallback_error.code not in {429, 500, 502, 503, 504}:
                        return False
                except (urllib.error.URLError, TimeoutError):
                    pass
            elif error.code not in {429, 500, 502, 503, 504}:
                return False
        except (urllib.error.URLError, TimeoutError):
            pass

        if attempt < max_retries:
            time.sleep(1)
    return False


def atomic_write_json(path, data):
    """Write and validate JSON before replacing the destination."""
    tmp_path = f"{path}.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as output:
            json.dump(data, output, indent=2, ensure_ascii=False)
            output.write("\n")
        with open(tmp_path, "r", encoding="utf-8") as input_file:
            json.load(input_file)
        os.replace(tmp_path, path)
    finally:
        # Leave no stale temporary file after a failed write or validation.
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass


def read_json_safe(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as input_file:
            return json.load(input_file)
    except (json.JSONDecodeError, OSError):
        return None


def extract_version(ipa_name=None, tag=None, release_name=None, published_at=None):
    """Priority: filename -> tag -> release name -> published date.
    Never fails outright just because one source's format changed.
    """
    for source in (ipa_name, tag, release_name):
        if source:
            matches = re.findall(r"(\d+\.\d+(?:\.\d+)?)", str(source))
            if matches:
                # Upstream IPA names put the host-app version first and the
                # tweak version after it (for example, 21.24.3_5.2.2).
                return matches[0]
    if published_at:
        return str(published_at)[:10]
    return "unknown"


def is_published_release(release):
    return (
        isinstance(release, dict)
        and not release.get("draft", False)
        and not release.get("prerelease", False)
    )


def ipa_asset(release, suffix=None):
    assets = release.get("assets", []) if isinstance(release, dict) else []
    if not isinstance(assets, list):
        return None
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = str(asset.get("name", ""))
        if name.lower().endswith((suffix or ".ipa").lower()):
            return asset
    return None


# =====================================================================
# STAGE 1: Sync YouProEXTRA releases (youpro, ytkp, youmod, ytkace, ytlite)
# =====================================================================
YOUPROEXTRA_REPO = 'mrdrvt99/YouProEXTRA'
TAG_MAP = {
    "youmod-ipa": "youmod",
    "youproextra-ipa": "youpro",
    "ytkp-ipa": "ytkp",
    "ytkace-ipa": "ytkace",
}
YOUPROEXTRA_FILES = {
    "ytkp": "ytkp.json",
    "youpro": "youpro.json",
    "youmod": "youmod.json",
    "ytkace": "ytkace.json",
}
YTLITE_PREFIX, YTLITE_FILE = 'ytl-ipa', 'ytlite.json'

def fetch_all_releases(repo, max_pages=10):
    results = []
    for page in range(1, max_pages + 1):
        batch = fetch_json(
            f"https://api.github.com/repos/{repo}/releases?per_page=100&page={page}"
        )
        if not isinstance(batch, list):
            raise RuntimeError(f"Unexpected releases response for {repo}")
        if not batch:
            break
        results.extend(batch)
        if len(batch) < 100:
            break
        time.sleep(0.3)  # safe rate limiting between requests
    return results


def update_manifest(filename, download_url, size, ipa_name, tag, release_name, date_str, body):
    if not os.path.exists(filename):
        print(f"::error::'{filename}' not found — skipping.")
        return
    if not isinstance(download_url, str) or not download_url:
        print(f"::warning::No download URL for the release asset — skipping {filename}.")
        return
    with open(filename, "r", encoding="utf-8") as input_file:
        source = json.load(input_file)
    apps = source.get("apps", [])
    if not isinstance(apps, list) or not apps or not isinstance(apps[0], dict):
        print(f"::error::'{filename}' has no valid 'apps' array — skipping.")
        return
    app = apps[0]
    original_app = json.loads(json.dumps(app))  # deep copy for unchanged-check

    version = extract_version(
        ipa_name=ipa_name, tag=tag, release_name=release_name, published_at=date_str
    )
    label = str(ipa_name).removesuffix(".ipa") if ipa_name else tag
    desc = f"YouTube {version} | {label}" + (f"\n\n{body}" if body else "")

    entry = {
        "version": version,
        "date": date_str,
        "localizedDescription": desc,
        "downloadURL": download_url,
        "size": size,
        "minOSVersion": "16.0",
    }
    app.update(
        {
            "versions": [entry],
            "version": version,
            "versionDate": date_str,
            "versionDescription": desc,
            "downloadURL": download_url,
            "size": size,
        }
    )

    if app == original_app:
        print(f"{filename} unchanged after update — skipping write.")
        return

    atomic_write_json(filename, source)
    print(f"Updated {filename}: '{app.get('name')}' → YouTube {version}")

def sync_youproextra():
    print("::group::Sync YouProEXTRA Releases")
    releases = fetch_all_releases(YOUPROEXTRA_REPO)
    published = [r for r in releases if is_published_release(r)]
    ytlite_releases = [
        r for r in published if str(r.get("tag_name", "")).startswith(YTLITE_PREFIX)
    ]

    best = {}
    for release in published:
        tag = str(release.get("tag_name", ""))
        if tag.startswith("youproextra-noytlite-ipa") or tag.startswith(YTLITE_PREFIX):
            continue
        for prefix, key in TAG_MAP.items():
            if tag.startswith(prefix) and key not in best:
                best[key] = release
                break

    if not best and not ytlite_releases:
        print("::warning::No matching YouProEXTRA releases found.")

    for app_key, release in best.items():
        date_str = (release.get("published_at") or "")[:10] or dt.now(
            timezone.utc
        ).strftime("%Y-%m-%d")
        body = (release.get("body") or "").strip()
        asset = ipa_asset(release)
        if not asset:
            print(
                f"::warning::No .ipa asset for "
                f"{release.get('tag_name', 'release')} — skipping."
            )
            continue
        update_manifest(
            YOUPROEXTRA_FILES[app_key],
            asset.get("browser_download_url"),
            asset.get("size", 0),
            asset.get("name", "build.ipa"),
            release.get("tag_name"),
            release.get("name"),
            date_str,
            body,
        )

    if ytlite_releases:
        def tag_num(release):
            match = re.search(r"ytl-ipa(\d+)", str(release.get("tag_name", "")))
            return int(match.group(1)) if match else -1

        min_os_map = {0: "14.0", 1: "15.0"}
        # GitHub returns releases newest-first, but tags are the stable ordering
        # for this feed.  The date tie-breaker handles malformed/un-numbered tags.
        ytlite_releases.sort(
            key=lambda release: (tag_num(release), release.get("published_at") or ""),
            reverse=True,
        )
        entries = []
        seen_urls = set()
        for release in ytlite_releases:
            date_str = (release.get("published_at") or "")[:10] or dt.now(
                timezone.utc
            ).strftime("%Y-%m-%d")
            body = (release.get("body") or "").strip()
            asset = ipa_asset(release)
            if not asset:
                print(
                    f"::warning::No .ipa asset for "
                    f"{release.get('tag_name', 'release')} — skipping."
                )
                continue
            download_url = asset.get("browser_download_url")
            if not download_url or download_url in seen_urls:
                continue
            seen_urls.add(download_url)
            asset_name = str(asset.get("name", "build.ipa"))
            version = extract_version(
                ipa_name=asset_name,
                tag=release.get("tag_name"),
                release_name=release.get("name"),
                published_at=date_str,
            )
            entries.append(
                {
                    "version": version,
                    "date": date_str,
                    "localizedDescription": f"YouTube {version} | {asset_name.removesuffix('.ipa')}"
                    + (f"\n\n{body}" if body else ""),
                    "downloadURL": download_url,
                    "size": asset.get("size", 0),
                    "minOSVersion": min_os_map.get(tag_num(release), "16.0"),
                }
            )

        if not entries:
            print("::warning::No usable ytl-ipa releases found — skipping ytlite.json.")
        elif not os.path.exists(YTLITE_FILE):
            print(f"::error::'{YTLITE_FILE}' not found.")
        else:
            with open(YTLITE_FILE, "r", encoding="utf-8") as input_file:
                ytlite_source = json.load(input_file)
            apps = ytlite_source.get("apps", [])
            if not isinstance(apps, list) or not apps or not isinstance(apps[0], dict):
                print(f"::error::'{YTLITE_FILE}' has no valid 'apps' array.")
            else:
                app = apps[0]
                original_app = json.loads(json.dumps(app))
                newest = entries[0]
                app.update(
                    {
                        "versions": entries,
                        "version": newest["version"],
                        "versionDate": newest["date"],
                        "versionDescription": newest["localizedDescription"],
                        "downloadURL": newest["downloadURL"],
                        "size": newest["size"],
                    }
                )
                if app == original_app:
                    print(f"{YTLITE_FILE} already up to date ({len(entries)} versions).")
                else:
                    atomic_write_json(YTLITE_FILE, ytlite_source)
                    print(
                        f"Updated {YTLITE_FILE}: {len(entries)} versions kept "
                        f"(newest: {newest['version']})"
                    )
    print("::endgroup::")


# =====================================================================
# STAGE 2: Sync YTMusicUltimate release
# =====================================================================
YTMUSIC_REPO, YTMUSIC_FILE = 'mrdrvt99/YTMusicUltimate', 'ytmusic.json'

def sync_ytmusic():
    print("::group::Sync YTMusicUltimate Release")
    if not os.path.exists(YTMUSIC_FILE):
        print(f"::error::'{YTMUSIC_FILE}' not found — skipping.")
        print("::endgroup::")
        return

    releases = fetch_all_releases(YTMUSIC_REPO, max_pages=3)
    release = None
    asset = None
    for candidate in releases:
        if not is_published_release(candidate):
            continue
        candidate_asset = ipa_asset(candidate)
        if candidate_asset:
            release, asset = candidate, candidate_asset
            break
    if release is None or asset is None:
        print("::warning::No published release with an .ipa asset found — skipping.")
        print("::endgroup::")
        return

    with open(YTMUSIC_FILE, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)
    apps = data.get("apps", [])
    if not isinstance(apps, list) or not apps or not isinstance(apps[0], dict):
        print(f"::error::'{YTMUSIC_FILE}' has no valid 'apps' array.")
        print("::endgroup::")
        return
    app = apps[0]
    original_app = json.loads(json.dumps(app))

    download_url = asset.get("browser_download_url")
    if not download_url:
        print("::warning::The .ipa asset has no download URL — skipping.")
        print("::endgroup::")
        return

    tag = release.get("tag_name")
    asset_name = str(asset.get("name", "build.ipa"))
    matches = re.findall(r"(\d+\.\d+(?:\.\d+)?)", asset_name)
    if len(matches) >= 2:
        tweak_v, ytm_v = matches[0], matches[-1]
    elif len(matches) == 1:
        tweak_v = ytm_v = matches[0]
    else:
        fallback = extract_version(
            tag=tag,
            release_name=release.get("name"),
            published_at=(release.get("published_at") or "")[:10],
        )
        tweak_v = ytm_v = fallback

    date_str = (release.get("published_at") or "")[:10] or dt.now(timezone.utc).strftime("%Y-%m-%d")
    body = (release.get("body") or "").strip()
    label = asset_name.removesuffix(".ipa")
    desc = f"YTMusicUltimate {tweak_v} | YTMusic {ytm_v} | {label}" + (f"\n\n{body}" if body else "")

    entry = {
        "version": tweak_v,
        "date": date_str,
        "localizedDescription": desc,
        "downloadURL": download_url,
        "size": asset.get("size", 0),
        "minOSVersion": "16.0",
    }
    app.update({
        "versions": [entry],
        "version": tweak_v,
        "versionDate": date_str,
        "versionDescription": desc,
        "downloadURL": download_url,
        "size": asset.get("size", 0),
    })

    if app == original_app:
        print(f"{YTMUSIC_FILE} unchanged after update — skipping write.")
        print("::endgroup::")
        return

    atomic_write_json(YTMUSIC_FILE, data)
    print(f"{YTMUSIC_FILE} updated: YTMusicUltimate {tweak_v} → YTMusic {ytm_v}")
    print("::endgroup::")


# =====================================================================
# STAGE 3: Sync SpotiFLAC Mobile release
# =====================================================================
SPOTIFLAC_REPO, SPOTIFLAC_FILE = 'spotiflacapp/SpotiFLAC-Mobile', 'spotiflac.json'

def sync_spotiflac():
    print("::group::Sync SpotiFLAC Mobile Release")
    if not os.path.exists(SPOTIFLAC_FILE):
        print(f"::error::'{SPOTIFLAC_FILE}' not found — skipping.")
        print("::endgroup::")
        return

    releases = fetch_all_releases(SPOTIFLAC_REPO, max_pages=3)
    release = None
    asset = None
    for candidate in releases:
        if not is_published_release(candidate):
            continue
        candidate_asset = ipa_asset(candidate, suffix="-ios-unsigned.ipa") or ipa_asset(candidate)
        if candidate_asset:
            release, asset = candidate, candidate_asset
            break
    if release is None or asset is None:
        print("::warning::No published release with an .ipa asset found — skipping.")
        print("::endgroup::")
        return

    with open(SPOTIFLAC_FILE, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)
    apps = data.get("apps", [])
    if not isinstance(apps, list) or not apps or not isinstance(apps[0], dict):
        print(f"::error::'{SPOTIFLAC_FILE}' has no valid 'apps' array.")
        print("::endgroup::")
        return
    app = apps[0]
    original_app = json.loads(json.dumps(app))

    download_url = asset.get("browser_download_url")
    if not download_url:
        print("::warning::The .ipa asset has no download URL — skipping.")
        print("::endgroup::")
        return

    tag = release.get("tag_name")
    asset_name = str(asset.get("name", "build.ipa"))
    date_str = (release.get("published_at") or "")[:10] or dt.now(timezone.utc).strftime("%Y-%m-%d")
    version = extract_version(
        ipa_name=asset_name,
        tag=tag,
        release_name=release.get("name"),
        published_at=date_str,
    )

    body = (release.get("body") or "").strip()
    label = asset_name.removesuffix(".ipa")
    desc = f"SpotiFLAC {version} | {label}" + (f"\n\n{body}" if body else "")

    entry = {
        "version": version,
        "date": date_str,
        "localizedDescription": desc,
        "downloadURL": download_url,
        "size": asset.get("size", 0),
        "minOSVersion": "16.0",
    }
    app.update({
        "versions": [entry],
        "version": version,
        "versionDate": date_str,
        "versionDescription": desc,
        "downloadURL": download_url,
        "size": asset.get("size", 0),
    })

    if app == original_app:
        print(f"{SPOTIFLAC_FILE} unchanged after update — skipping write.")
        print("::endgroup::")
        return

    atomic_write_json(SPOTIFLAC_FILE, data)
    print(f"{SPOTIFLAC_FILE} updated: SpotiFLAC → {version} ({tag})")
    print("::endgroup::")


# =====================================================================
# STAGE 4: Compile master feed with asset routing, dev names, link checks
# =====================================================================
SOURCE_OWNER = "iamsmmh"
SOURCE_REPO_URL = "https://github.com/iamsmmh/OmniSource"
BASE_URL = "https://iamsmmh.github.io/OmniSource"

# filename (lowercase) -> (icon filename, bundle id, developer name)
FILE_CONFIG = {
    "spotiflac.json": ("SpotiFLAC.png", "com.zarzet.spotiflac", "zarzet"),
    "uyouenhanced.json": ("uYouEnhanced.png", "com.google.ios.youtube", "arichornlover"),
    "ytkace.json": ("YouTube.png", "com.google.ios.youtube", "itzzace"),
    "youpro.json": ("YouTube.png", "com.google.ios.youtube", "alibusut"),
    "ytlite.json": ("YouTube.png", "com.google.ios.youtube", "dayanch96"),
    "ytkp.json": ("YouTube.png", "com.google.ios.youtube", "ikghd"),
    "ytmusic.json": ("YouTubeMusic.png", "com.google.ios.youtubemusic", "dayanch96"),
    "youmod.json": ("YouTube.png", "com.google.ios.youtube", "Tonwalter888"),
}


def standardize(app, icon_url, bundle_id, dev_name):
    """Normalize fields that must be consistent in standalone and master feeds."""
    app["bundleIdentifier"], app["iconURL"], app["developerName"] = bundle_id, icon_url, dev_name
    if not app.get("versionDate"):
        app["versionDate"] = dt.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    versions = app.get("versions")
    if not isinstance(versions, list):
        versions = []
        app["versions"] = versions
    if not versions and app.get("version") and app.get("downloadURL"):
        versions.append(
            {
                "version": app["version"],
                "date": app["versionDate"],
                "localizedDescription": app.get(
                    "localizedDescription", "Stable production build."
                ),
                "downloadURL": app["downloadURL"],
                "size": app.get("size", 120000000),
                "minOSVersion": "16.0",
            }
        )

    # AltStore treats the first version as the current build.  Repair stale
    # top-level mirrors so an upstream feed cannot leave the master manifest
    # pointing at a different IPA than versions[0].
    if versions and isinstance(versions[0], dict):
        newest = versions[0]
        for field in ("version", "downloadURL", "size"):
            if field in newest:
                app[field] = newest[field]
        if not app.get("versionDescription") and newest.get("localizedDescription"):
            app["versionDescription"] = newest["localizedDescription"]
    return app

def build_feed():
    print("::group::Build Master Feed")
    site_icon = (
        f"{BASE_URL}/assets/OmniSource.png"
        if os.path.exists("assets/OmniSource.png")
        else f"{BASE_URL}/assets/icon.png"
    )
    banner_icon = (
        f"{BASE_URL}/assets/banner.png"
        if os.path.exists("assets/banner.png")
        else site_icon
    )

    actual_files = {
        os.path.basename(path).lower(): os.path.basename(path)
        for path in glob.glob("*.json")
        if os.path.isfile(path)
    }
    print("::group::Repo root JSON files detected")
    for f in sorted(actual_files.values()):
        print(f"  - {f}")
    print("::endgroup::")

    master_apps, had_errors, skipped = [], False, []

    for expected, (icon_name, bundle_id, dev_name) in FILE_CONFIG.items():
        real = actual_files.get(expected.lower())
        if real is None:
            print(f"::error::Expected '{expected}' not found. Files present: {sorted(actual_files.values())}")
            had_errors = True
            continue
        if real != expected:
            print(f"::warning::Matched '{expected}' to on-disk file '{real}' (case mismatch).")

        try:
            with open(real, "r", encoding="utf-8") as input_file:
                data = json.load(input_file)
        except (json.JSONDecodeError, OSError) as error:
            print(f"::error::Failed to parse {real}: {error}")
            had_errors = True
            continue
        if not isinstance(data, dict):
            print(f"::error::'{real}' must contain a JSON object at the root.")
            had_errors = True
            continue

        apps = data.get("apps", [])
        if not isinstance(apps, list) or not apps:
            print(f"::error::'{real}' has no 'apps' array (keys: {list(data.keys())}).")
            had_errors = True
            continue
        if not all(isinstance(entry, dict) for entry in apps):
            print(f"::error::'{real}' contains a non-object app entry.")
            had_errors = True
            continue

        app_name = apps[0].get("name", "Application")
        icon_url = f"{BASE_URL}/assets/{icon_name}"
        original_data = json.loads(json.dumps(data))

        data.update(
            {
                "name": f"OmniSource - {app_name}",
                "website": f"{BASE_URL}/",
                "description": f"Standalone distribution feed for {app_name}, curated within OmniSource.",
                "iconURL": icon_url,
                "bannerURL": banner_icon,
            }
        )

        normalized = [standardize(entry, icon_url, bundle_id, dev_name) for entry in apps]
        kept = []
        for entry in normalized:
            url = entry.get("downloadURL", "")
            print(f"Checking download link for '{entry.get('name', app_name)}'...")
            if check_url_alive(url):
                print(f"  OK: {url}")
                kept.append(entry)
            else:
                print(
                    f"::warning::Dead/unreachable downloadURL for "
                    f"'{entry.get('name', app_name)}' in {real}: {url}"
                )
                skipped.append(f"{real} -> {entry.get('name', app_name)}")

        # Keep standalone manifests complete, but never publish an entry that
        # failed its link check in the master feed.  A failed check is an error
        # so a transient outage cannot silently remove apps from a release.
        data["apps"] = normalized
        master_apps.extend(kept)
        if len(kept) != len(normalized):
            had_errors = True
        if not kept:
            print(f"::warning::All apps in '{real}' had dead links — excluded this run.")
            continue

        if data == original_data:
            print(f"{real} unchanged — skipping write.")
        else:
            try:
                atomic_write_json(real, data)
                print(f"Synchronized: {real} ({len(kept)} app(s))")
            except (OSError, json.JSONDecodeError) as e:
                print(f"::error::Failed to write {real}: {e}")
                had_errors = True

    if not master_apps:
        print("::error::No valid application definitions identified. Aborting.")
        print("::endgroup::")
        sys.exit(1)

    # Deterministic ordering — prevents random diffs between runs
    master_apps.sort(key=lambda app: app.get("name", "").lower())

    new_feed_body = {
        "name": "OmniSource",
        "identifier": f"com.{SOURCE_OWNER.lower()}.omnisource",
        "subtitle": "Consolidated iOS Applications & Tweaks Repository",
        "description": "Master AltStore and SideStore repository compiled and managed under OmniSource.",
        "sourceURL": SOURCE_REPO_URL,
        "iconURL": site_icon,
        "bannerURL": banner_icon,
        "website": f"{BASE_URL}/",
        "apps": master_apps
    }

    existing_feed = read_json_safe("apps.json")
    existing_comparable = None
    if existing_feed is not None:
        existing_comparable = {k: v for k, v in existing_feed.items() if k != "generatedAt"}

    if existing_comparable == new_feed_body:
        print("apps.json unchanged — skipping write.")
    else:
        new_feed_body["generatedAt"] = dt.now(timezone.utc).isoformat()
        atomic_write_json("apps.json", new_feed_body)
        print(f"Master feed generated with {len(master_apps)} app definitions (expected up to {len(FILE_CONFIG)}).")

    if skipped:
        print("::warning::Apps excluded this run due to dead links:")
        for item in skipped:
            print(f"  - {item}")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("## OmniSource Build Summary\n\n")
            f.write(f"- **Apps compiled:** {len(master_apps)} / {len(FILE_CONFIG)}\n")
            if skipped:
                f.write(f"- **Dead links excluded:** {len(skipped)}\n")
                for item in skipped:
                    f.write(f"  - `{item}`\n")
            f.write("- ✅ No structural errors.\n" if not had_errors else "- ⚠️ Structural errors occurred — check logs.\n")

    print("::endgroup::")
    if had_errors:
        print("::error::Completed with structural errors — see annotations above.")
        sys.exit(1)


# =====================================================================
# Entry point — runs all stages in order
# =====================================================================
def main():
    try:
        sync_youproextra()
        sync_ytmusic()
        sync_spotiflac()
        build_feed()
    except RuntimeError:
        # fetch_json already emitted a GitHub Actions annotation.
        sys.exit(1)


if __name__ == "__main__":
    main()
