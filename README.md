<div align="center">

<img src="assets/OmniSource.png" width="120" alt="OmniSource logo">

# OmniSource

**A curated iOS application repository and distribution platform.**

One AltStore-compatible feed for **AltStore · SideStore · Feather · ESign · LiveContainer**.

<p>
  <a href="https://github.com/iamsmmh/OmniSource/actions/workflows/sync.yml"><img src="https://github.com/iamsmmh/OmniSource/actions/workflows/sync.yml/badge.svg" alt="Sync &amp; Publish"></a>
  <a href="https://github.com/iamsmmh/OmniSource/actions/workflows/validate.yml"><img src="https://github.com/iamsmmh/OmniSource/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="https://github.com/iamsmmh/OmniSource/actions/workflows/health-check.yml"><img src="https://github.com/iamsmmh/OmniSource/actions/workflows/health-check.yml/badge.svg" alt="Health Check"></a>
  <img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2Ffeeds%2Fhealth.json&query=%24.totals.apps&label=apps&color=5B5BD6&cacheSeconds=3600" alt="App count">
  <img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2Ffeeds%2Fhealth.json&query=%24.totals.reachable&label=downloads%20online&color=success&cacheSeconds=3600" alt="Downloads online">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/iamsmmh/OmniSource" alt="License"></a>
</p>

[Website](https://iamsmmh.github.io/OmniSource/) ·
[Install](docs/INSTALLATION.md) ·
[Catalog](docs/CATALOG.md) ·
[Compatibility](docs/COMPATIBILITY.md) ·
[Architecture](docs/ARCHITECTURE.md) ·
[Contribute](docs/CONTRIBUTING.md)

</div>

---

OmniSource tracks upstream iOS app releases, verifies every download link, and publishes a single
AltStore Source **v2** feed. Every entry is rebuilt automatically from its upstream project, and a
daily health check reports broken links so the catalog stays installable.

## Add the source

```
https://iamsmmh.github.io/OmniSource/apps.json
```

One tap from your device:

| Client | Install action |
| --- | --- |
| **AltStore** | <a href="altstore://source?url=https://iamsmmh.github.io/OmniSource/apps.json">➕ Add to AltStore</a> |
| **SideStore** | <a href="sidestore://source?url=https://iamsmmh.github.io/OmniSource/apps.json">➕ Add to SideStore</a> |
| **Feather** | <a href="feather://source/iamsmmh.github.io/OmniSource/apps.json">➕ Add to Feather</a> |

ESign and LiveContainer don't expose a source deep-link protocol — open them and paste the feed URL
manually. Step-by-step walkthroughs for every client live in the
[Installation Guide](docs/INSTALLATION.md).

Prefer a single app? Each app also publishes its own feed at
`https://iamsmmh.github.io/OmniSource/<slug>.json` (slugs below).

## Catalog

<!-- omnisource:catalog:start -->

_Catalogue last changed 2026-09-01 · 8 apps · 8/8 downloads reachable._

| App | Bundle ID | Version | Updated | Status | Download | Install | Feed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **SpotiFLAC Mobile** | `com.zarzet.spotiflac` | `4.9.5` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/spotiflac.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/spotiflac.json) | [`spotiflac.json`](https://iamsmmh.github.io/OmniSource/spotiflac.json) |
| **uYouEnhanced** | `com.google.ios.youtube` | `21.14.4` | 2026-08-22 | 🔵 manual | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/uyouenhanced.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/uyouenhanced.json) | [`uyouenhanced.json`](https://iamsmmh.github.io/OmniSource/uyouenhanced.json) |
| **YouTubePlus** | `com.google.ios.youtube` | `21.24.3` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/ytlite.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/ytlite.json) | [`ytlite.json`](https://iamsmmh.github.io/OmniSource/ytlite.json) |
| **YouPro** | `com.google.ios.youtube` | `21.24.3` | 2026-08-16 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/youpro.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/youpro.json) | [`youpro.json`](https://iamsmmh.github.io/OmniSource/youpro.json) |
| **YTKillerPlus** | `com.google.ios.youtube` | `21.35.3` | 2026-08-30 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/ytkp.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/ytkp.json) | [`ytkp.json`](https://iamsmmh.github.io/OmniSource/ytkp.json) |
| **YTKACE** | `com.google.ios.youtube` | `21.35.3` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/ytkace.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/ytkace.json) | [`ytkace.json`](https://iamsmmh.github.io/OmniSource/ytkace.json) |
| **YouMod** | `com.google.ios.youtube` | `21.35.3` | 2026-08-30 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/youmod.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/youmod.json) | [`youmod.json`](https://iamsmmh.github.io/OmniSource/youmod.json) |
| **YTMusicUltimate** | `com.google.ios.youtubemusic` | `9.35.2` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/ytmusic.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/ytmusic.json) | [`ytmusic.json`](https://iamsmmh.github.io/OmniSource/ytmusic.json) |

<!-- omnisource:catalog:end -->

**Columns** — *Status*: 🟢 stable · 🟡 beta · 🔵 manually published · 🔴 unmaintained.
*Download*: ✅ / ⚠️ reflects the last automated reachability probe. *Install*: one-tap deep links
that open the per-app feed directly in AltStore or SideStore. *Feed*: the per-app JSON source.

## How it works

```
catalog.json ──▶ scripts/omnisource.py ──▶ feeds/*.json ──▶ GitHub Pages ──▶ your client
  (edited)         (every 6 hours)          (generated)
```

`catalog.json` is the only hand-edited data file. Everything else — the master feed, the per-app
feeds, the root-level compatibility mirrors, the health snapshot and the table above — is
generated. `feeds/` is the single source of truth for distribution: a dedicated merge workflow
rebuilds the root `apps.json` from it on every change. See the
[Architecture Guide](docs/ARCHITECTURE.md).

| Pipeline | Runs | What it does |
| --- | --- | --- |
| **Sync & Publish** | every 6 h · on push | Resolve upstream releases, probe links, rebuild every feed, deploy Pages |
| **Validate** | every push & PR | `jq` + Python structural checks, reproducibility, `ruff`, `actionlint` |
| **Merge Feeds** | when `feeds/` changes | Rebuild the unified root `apps.json` from the modular feeds |
| **Health Check** | daily | HEAD-probe every download URL + mirror and report broken links via a GitHub Issue |

## Repository layout

| Path | Purpose |
| --- | --- |
| `catalog.json` | Source of truth: apps, upstream repositories, metadata, fallback mirrors |
| `feeds/` | Generated AltStore feeds + `health.json` + pipeline state (**SSOT for distribution**) |
| `*.json` (root) | Generated mirrors that keep historical feed URLs working |
| `schemas/` | JSON Schema for `catalog.json` and the AltStore v2 feed format |
| `assets/` | App and client icons served over Pages |
| `scripts/` | `omnisource.py` (build) · `validate.py` (checks) · `validate_jq.sh` (jq lint) · `merge_feeds.py` (merge) · `health_check.py` (probe) |
| `website/` | Static GitHub Pages site |
| `docs/` | Installation, catalog, compatibility, contributing, architecture, audit |

## Usage

### For users

1. Tap **Add to AltStore** / **Add to SideStore** above (or paste the feed URL in Feather/ESign).
2. Open the source in your client and pick an app.
3. Sign with your own Apple ID or certificate and install.

> [!IMPORTANT]
> Nothing in OmniSource is pre-signed, and free Apple IDs are limited to **three** sideloaded apps
> with a **seven-day** signature. AltStore and SideStore refresh automatically; Feather and ESign
> use your own certificate for longer-lived installs.

### For developers

```bash
git clone https://github.com/iamsmmh/OmniSource.git
cd OmniSource

python3 scripts/omnisource.py     # sync upstream + rebuild every feed
python3 scripts/validate.py       # offline structural checks
bash scripts/validate_jq.sh       # jq-only JSON lint + AltStore v2 checks
python3 scripts/health_check.py   # HEAD-probe every download URL
```

All scripts are Python/bundled-`jq` standard-library only — no virtualenv, no dependencies. See
[CONTRIBUTING](docs/CONTRIBUTING.md) for the golden rule: change `catalog.json`, never the
generated files.

## Resilience

- **Fallback mirrors** — an app may declare `fallbackDownloadURLs` in `catalog.json`; the feed,
  the website and the health check all honour them, so a build stays installable when its primary
  host goes dark.
- **Last-good build** — if an upstream goes quiet, the feed keeps serving the previous release
  instead of dropping the app.
- **Broken-link reporting** — the daily health check files a GitHub Issue with every unreachable
  URL, so failures are visible and triaged.

## Disclaimer

OmniSource is an independent community project. It aggregates and redistributes third-party
releases; all apps, code and trademarks belong to their respective owners. Availability may change
without notice, and you are responsible for complying with applicable laws and terms of service.

Credits to upstream maintainers are listed in [docs/CATALOG.md](docs/CATALOG.md).

## License

[GPL-3.0](LICENSE) © the OmniSource contributors.
