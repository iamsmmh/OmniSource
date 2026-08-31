import sys, os, json, re, time, glob
import urllib.request, urllib.error
from datetime import datetime as dt, timezone

# =====================================================================
# SHARED HELPERS
# =====================================================================
GH_TOKEN = os.environ.get('GH_TOKEN', '')

def fetch_json(url, max_retries=3):
    """GH_TOKEN is only ever attached here — this function is used
    exclusively for api.github.com calls, never for browser_download_url."""
    headers = {'User-Agent': 'github-actions/omnisource-sync'}
    if GH_TOKEN:
        headers['Authorization'] = f'token {GH_TOKEN}'
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
            print(f"::warning::Request failed (attempt {attempt}/{max_retries}), retrying in {wait}s: {e}")
            time.sleep(wait)

def check_url_alive(url, timeout=10, max_retries=2):
    """No Authorization header here by design — this hits arbitrary
    browser_download_url / CDN links, never the GitHub API."""
    if not url:
        return False
    valid_codes = {200, 206, 301, 302, 307, 308}
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=timeout) as resp:
                return resp.status in valid_codes
        except urllib.error.HTTPError as e:
            if e.code in valid_codes:
                return True
            if e.code == 405:
                try:
                    with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=timeout) as r2:
                        return r2.status in valid_codes
                except Exception:
                    return False
            return False
        except Exception:
            if attempt < max_retries:
                time.sleep(1)
                continue
            return False
    return False

def atomic_write_json(path, data):
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
    with open(tmp_path, "r", encoding="utf-8") as f:
        json.load(f)  # validate before committing
    os.replace(tmp_path, path)

def read_json_safe(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

def extract_version(ipa_name=None, tag=None, release_name=None, published_at=None):
    """Priority: filename -> tag -> release name -> published date.
    Never fails outright just because one source's format changed."""
    for source in (ipa_name, tag, release_name):
        if source:
            matches = re.findall(r'(\d+\.\d+(?:\.\d+)?)', source)
            if matches:
                return matches[-1] if source is ipa_name else matches[0]
    if published_at:
        return published_at[:10]
    return "unknown"


# =====================================================================
# STAGE 1: Sync YouProEXTRA releases (youpro, ytkp, youmod, ytkace, ytlite)
# =====================================================================
YOUPROEXTRA_REPO = 'mrdrvt99/YouProEXTRA'
TAG_MAP = {'youmod-ipa': 'youmod', 'youproextra-ipa': 'youpro', 'ytkp-ipa': 'ytkp', 'ytkace-ipa': 'ytkace'}
YOUPROEXTRA_FILES = {'ytkp': 'ytkp.json', 'youpro': 'youpro.json', 'youmod': 'youmod.json', 'ytkace': 'ytkace.json'}
YTLITE_PREFIX, YTLITE_FILE = 'ytl-ipa', 'ytlite.json'

def fetch_all_releases(repo, max_pages=10):
    results = []
    for page in range(1, max_pages + 1):
        batch = fetch_json(f'https://api.github.com/repos/{repo}/releases?per_page=100&page={page}')
        time.sleep(0.3)  # safe rate limiting between requests
        if not batch:
            break
        results.extend(batch)
        if len(batch) < 100:
            break
    return results

def update_manifest(filename, download_url, size, ipa_name, tag, release_name, date_str, body):
    if not os.path.exists(filename):
        print(f"::error::'{filename}' not found — skipping.")
        return
    with open(filename, 'r', encoding='utf-8') as f:
        source = json.load(f)
    apps = source.get('apps', [])
    if not apps:
        print(f"::error::'{filename}' has no 'apps' array — skipping.")
        return
    app = apps[0]
    original_app = json.loads(json.dumps(app))  # deep copy for unchanged-check

    if app.get('downloadURL') == download_url:
        print(f"{filename} already up to date.")
        return

    version = extract_version(ipa_name=ipa_name, tag=tag, release_name=release_name, published_at=date_str)
    label = ipa_name.replace('.ipa', '') if ipa_name else tag
    desc = f"YouTube {version} | {label}" + (f"\n\n{body}" if body else "")

    entry = {"version": version, "date": date_str, "localizedDescription": desc,
             "downloadURL": download_url, "size": size, "minOSVersion": "16.0"}
    app.update({"versions": [entry], "version": version, "versionDate": date_str,
                "versionDescription": desc, "downloadURL": download_url, "size": size})

    if app == original_app:
        print(f"{filename} unchanged after update — skipping write.")
        return

    atomic_write_json(filename, source)
    print(f"Updated {filename}: '{app.get('name')}' → YouTube {version}")

def sync_youproextra():
    print("::group::Sync YouProEXTRA Releases")
    releases = fetch_all_releases(YOUPROEXTRA_REPO)
    published = [r for r in releases if not r['draft'] and not r['prerelease']]
    ytlite_releases = [r for r in releases if not r['draft'] and r['tag_name'].startswith(YTLITE_PREFIX)]

    best = {}
    for r in published:
        tag = r['tag_name']
        if tag.startswith('youproextra-noytlite-ipa') or tag.startswith(YTLITE_PREFIX):
            continue
        for prefix, key in TAG_MAP.items():
            if tag.startswith(prefix) and key not in best:
                best[key] = r
                break

    if not best and not ytlite_releases:
        print("::warning::No matching YouProEXTRA releases found.")

    for app_key, release in best.items():
        date_str = (release.get('published_at') or '')[:10] or dt.now(timezone.utc).strftime('%Y-%m-%d')
        body = (release.get('body') or '').strip()
        asset = next((a for a in release.get('assets', []) if a['name'].endswith('.ipa')), None)
        if not asset:
            print(f"::warning::No .ipa asset for {release['tag_name']} — skipping.")
            continue
        update_manifest(
            YOUPROEXTRA_FILES[app_key], asset['browser_download_url'], asset['size'],
            asset['name'], release['tag_name'], release.get('name'), date_str, body
        )

    if ytlite_releases:
        def tag_num(r):
            m = re.search(r'ytl-ipa(\d+)', r['tag_name'])
            return int(m.group(1)) if m else -1

        min_os_map = {0: "14.0", 1: "15.0"}
        ytlite_releases.sort(key=tag_num, reverse=True)
        entries = []
        for r in ytlite_releases:
            date_str = (r.get('published_at') or '')[:10] or dt.now(timezone.utc).strftime('%Y-%m-%d')
            body = (r.get('body') or '').strip()
            asset = next((a for a in r.get('assets', []) if a['name'].endswith('.ipa')), None)
            if not asset:
                print(f"::warning::No .ipa asset for {r['tag_name']} — skipping.")
                continue
            version = extract_version(ipa_name=asset['name'], tag=r['tag_name'], release_name=r.get('name'), published_at=date_str)
            entries.append({
                "version": version, "date": date_str,
                "localizedDescription": f"YouTube {version} | {asset['name'].replace('.ipa','')}" + (f"\n\n{body}" if body else ""),
                "downloadURL": asset['browser_download_url'], "size": asset['size'],
                "minOSVersion": min_os_map.get(tag_num(r), "16.0"),
            })

        if not entries:
            print("::warning::No usable ytl-ipa releases found — skipping ytlite.json.")
        elif not os.path.exists(YTLITE_FILE):
            print(f"::error::'{YTLITE_FILE}' not found.")
        else:
            with open(YTLITE_FILE, 'r', encoding='utf-8') as f:
                ytlite_source = json.load(f)
            apps = ytlite_source.get('apps', [])
            if not apps:
                print(f"::error::'{YTLITE_FILE}' has no 'apps' array.")
            else:
                app = apps[0]
                if [v.get('downloadURL') for v in app.get('versions', [])] == [e['downloadURL'] for e in entries]:
                    print(f"{YTLITE_FILE} already up to date ({len(entries)} versions).")
                else:
                    newest = entries[0]
                    app.update({"versions": entries, "version": newest['version'], "versionDate": newest['date'],
                                "versionDescription": newest['localizedDescription'],
                                "downloadURL": newest['downloadURL'], "size": newest['size']})
                    atomic_write_json(YTLITE_FILE, ytlite_source)
                    print(f"Updated {YTLITE_FILE}: {len(entries)} versions kept (newest: {newest['version']})")
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

    releases = fetch_json(f'https://api.github.com/repos/{YTMUSIC_REPO}/releases?per_page=5')
    time.sleep(0.3)
    release = next((r for r in releases if not r['draft'] and not r['prerelease']), None)
    if release is None:
        print("::warning::No published release found — skipping.")
        print("::endgroup::")
        return

    asset = next((a for a in release.get('assets', []) if a['name'].endswith('.ipa')), None)
    if not asset:
        print("::warning::No .ipa asset found — skipping.")
        print("::endgroup::")
        return

    with open(YTMUSIC_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    apps = data.get('apps', [])
    if not apps:
        print(f"::error::'{YTMUSIC_FILE}' has no 'apps' array.")
        print("::endgroup::")
        return
    app = apps[0]
    original_app = json.loads(json.dumps(app))

    download_url = asset['browser_download_url']
    if app.get('downloadURL') == download_url:
        print(f"{YTMUSIC_FILE} already up to date: {download_url}")
        print("::endgroup::")
        return

    tag = release['tag_name']
    matches = re.findall(r'(\d+\.\d+(?:\.\d+)?)', asset['name'])
    if len(matches) >= 2:
        tweak_v, ytm_v = matches[0], matches[-1]
    elif len(matches) == 1:
        tweak_v = ytm_v = matches[0]
    else:
        fallback = extract_version(tag=tag, release_name=release.get('name'),
                                    published_at=(release.get('published_at') or '')[:10])
        tweak_v = ytm_v = fallback

    date_str = (release.get('published_at') or '')[:10] or dt.now(timezone.utc).strftime('%Y-%m-%d')
    body = (release.get('body') or '').strip()
    label = asset['name'].replace('.ipa', '')
    desc = f"YTMusicUltimate {tweak_v} | YTMusic {ytm_v} | {label}" + (f"\n\n{body}" if body else "")

    entry = {"version": tweak_v, "date": date_str, "localizedDescription": desc,
             "downloadURL": download_url, "size": asset['size'], "minOSVersion": "16.0"}
    app.update({"versions": [entry], "version": tweak_v, "versionDate": date_str,
                "versionDescription": desc, "downloadURL": download_url, "size": asset['size']})

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

    releases = fetch_json(f'https://api.github.com/repos/{SPOTIFLAC_REPO}/releases?per_page=5')
    time.sleep(0.3)
    release = next((r for r in releases if not r['draft'] and not r['prerelease']), None)
    if release is None:
        print("::warning::No published release found — skipping.")
        print("::endgroup::")
        return

    asset = next((a for a in release.get('assets', []) if a['name'].endswith('-ios-unsigned.ipa')), None)
    if not asset:
        asset = next((a for a in release.get('assets', []) if a['name'].endswith('.ipa')), None)
    if not asset:
        print("::warning::No .ipa asset found — skipping.")
        print("::endgroup::")
        return

    with open(SPOTIFLAC_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    apps = data.get('apps', [])
    if not apps:
        print(f"::error::'{SPOTIFLAC_FILE}' has no 'apps' array.")
        print("::endgroup::")
        return
    app = apps[0]
    original_app = json.loads(json.dumps(app))

    download_url = asset['browser_download_url']
    if app.get('downloadURL') == download_url:
        print(f"{SPOTIFLAC_FILE} already up to date: {download_url}")
        print("::endgroup::")
        return

    tag = release['tag_name']
    date_str = (release.get('published_at') or '')[:10] or dt.now(timezone.utc).strftime('%Y-%m-%d')
    version = extract_version(ipa_name=asset['name'], tag=tag, release_name=release.get('name'), published_at=date_str)

    body = (release.get('body') or '').strip()
    label = asset['name'].replace('.ipa', '')
    desc = f"SpotiFLAC {version} | {label}" + (f"\n\n{body}" if body else "")

    entry = {"version": version, "date": date_str, "localizedDescription": desc,
             "downloadURL": download_url, "size": asset['size'], "minOSVersion": "16.0"}
    app.update({"versions": [entry], "version": version, "versionDate": date_str,
                "versionDescription": desc, "downloadURL": download_url, "size": asset['size']})

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
    "spotiflac.json": ("SpotiFLAC.png",    "com.zarzet.spotiflac",        "zarzet"),
    "ytkace.json":    ("YouTube.png",      "com.google.ios.youtube",      "itzzace"),
    "youpro.json":    ("YouTube.png",      "com.google.ios.youtube",      "alibusut"),
    "ytlite.json":    ("YouTube.png",      "com.google.ios.youtube",      "dayanch96"),
    "ytkp.json":      ("YouTube.png",      "com.google.ios.youtube",      "ikghd"),
    "ytmusic.json":   ("YouTubeMusic.png", "com.google.ios.youtubemusic", "dayanch96"),
    "youmod.json":    ("YouTube.png",      "com.google.ios.youtube",      "Tonwalter888"),
}

def standardize(app, icon_url, bundle_id, dev_name):
    app["bundleIdentifier"], app["iconURL"], app["developerName"] = bundle_id, icon_url, dev_name
    if not app.get("versionDate"):
        app["versionDate"] = dt.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not app.get("versions") and app.get("version") and app.get("downloadURL"):
        app["versions"] = [{
            "version": app.get("version"), "date": app.get("versionDate"),
            "localizedDescription": app.get("localizedDescription", "Stable production build."),
            "downloadURL": app.get("downloadURL"), "size": app.get("size", 120000000)
        }]
    return app

def build_feed():
    print("::group::Build Master Feed")
    site_icon = f"{BASE_URL}/assets/OmniSource.png" if os.path.exists("assets/OmniSource.png") else f"{BASE_URL}/assets/icon.png"
    banner_icon = f"{BASE_URL}/assets/banner.png" if os.path.exists("assets/banner.png") else site_icon

    actual_files = {f.lower(): f for f in glob.glob("*.json")}
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
            with open(real, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"::error::Failed to parse {real}: {e}")
            had_errors = True
            continue

        apps = data.get("apps", [])
        if not apps:
            print(f"::error::'{real}' has no 'apps' array (keys: {list(data.keys())}).")
            had_errors = True
            continue

        app_name = apps[0].get("name", "Application")
        icon_url = f"{BASE_URL}/assets/{icon_name}"
        original_data = json.loads(json.dumps(data))

        data.update({
            "name": f"OmniSource - {app_name}", "website": f"{BASE_URL}/",
            "description": f"Standalone distribution feed for {app_name}, curated within OmniSource.",
            "iconURL": icon_url, "bannerURL": banner_icon
        })

        kept = []
        for entry in apps:
            url = entry.get("downloadURL", "")
            print(f"Checking download link for '{entry.get('name', app_name)}'...")
            if check_url_alive(url):
                print(f"  OK: {url}")
                kept.append(standardize(entry, icon_url, bundle_id, dev_name))
            else:
                print(f"::warning::Dead/unreachable downloadURL for '{entry.get('name', app_name)}' in {real}: {url}")
                skipped.append(f"{real} -> {entry.get('name', app_name)}")

        if not kept:
            print(f"::warning::All apps in '{real}' had dead links — excluded this run.")
            continue

        data["apps"] = kept
        master_apps.extend(kept)

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
    sync_youproextra()
    sync_ytmusic()
    sync_spotiflac()
    build_feed()

if __name__ == "__main__":
    main()
