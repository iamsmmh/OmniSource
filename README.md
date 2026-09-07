<div align="center">

<img src="assets/OmniSource.png" width="120" alt="OmniSource logo">

# OmniSource

**A curated iOS sideloading app source.**

One AltStore-compatible feed for **AltStore · SideStore · Feather · ESign · LiveContainer**.

<p>
  <a href="https://github.com/iamsmmh/OmniSource/actions/workflows/sync.yml"><img src="https://github.com/iamsmmh/OmniSource/actions/workflows/sync.yml/badge.svg" alt="Sync & Publish"></a>
  <a href="https://github.com/iamsmmh/OmniSource/actions/workflows/validate.yml"><img src="https://github.com/iamsmmh/OmniSource/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/iamsmmh/OmniSource" alt="License"></a>
</p>

</div>

OmniSource resolves each app's release from its **official upstream source** — the developer's GitHub
Releases or the developer's own AltStore feed — and publishes a single AltStore Source **v2** feed.
A scheduled pipeline keeps every entry current and probes every download link, so the catalog stays
installable.

## Add the source

```
https://iamsmmh.github.io/OmniSource/apps.json
```

| Client | Install action |
| --- | --- |
| **AltStore** | <a href="altstore://source?url=https://iamsmmh.github.io/OmniSource/apps.json">➕ Add to AltStore</a> |
| **SideStore** | <a href="sidestore://source?url=https://iamsmmh.github.io/OmniSource/apps.json">➕ Add to SideStore</a> |
| **Feather** | <a href="feather://source/iamsmmh.github.io/OmniSource/apps.json">➕ Add to Feather</a> |

ESign and LiveContainer don't expose a source deep-link protocol — open the client and paste the feed
URL manually. Each app also publishes its own feed at `https://iamsmmh.github.io/OmniSource/<slug>.json`
(see the catalog below).

## Catalog

<!-- omnisource:catalog:start -->

_Catalogue last changed 2026-09-07 · 22 apps · 22/22 downloads reachable._

| App | Bundle ID | Version | Updated | Status | Download | Install | Feed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **SpotiFLAC Mobile** | `com.zarz.spotiflacAndroid` | `4.9.6` | 2026-09-07 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/spotiflac.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/spotiflac.json) | [`spotiflac.json`](https://iamsmmh.github.io/OmniSource/spotiflac.json) |
| **uYouEnhanced** | `com.google.ios.youtube` | `21.14.4` | 2026-08-22 | 🔵 manual | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/uyouenhanced.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/uyouenhanced.json) | [`uyouenhanced.json`](https://iamsmmh.github.io/OmniSource/uyouenhanced.json) |
| **YouTubePlus** | `com.google.ios.youtube` | `21.24.3` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/ytlite.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/ytlite.json) | [`ytlite.json`](https://iamsmmh.github.io/OmniSource/ytlite.json) |
| **YouPro** | `com.google.ios.youtube` | `21.24.3` | 2026-08-16 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/youpro.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/youpro.json) | [`youpro.json`](https://iamsmmh.github.io/OmniSource/youpro.json) |
| **YTKillerPlus** | `com.google.ios.youtube` | `21.35.3` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/ytkp.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/ytkp.json) | [`ytkp.json`](https://iamsmmh.github.io/OmniSource/ytkp.json) |
| **YTKACE** | `com.google.ios.youtube` | `21.35.3` | 2026-08-31 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/ytkace.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/ytkace.json) | [`ytkace.json`](https://iamsmmh.github.io/OmniSource/ytkace.json) |
| **YouMod** | `com.google.ios.youtube` | `21.35.3` | 2026-08-30 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/youmod.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/youmod.json) | [`youmod.json`](https://iamsmmh.github.io/OmniSource/youmod.json) |
| **MaxTube** | `com.google.ios.youtube` | `21.31.3` | 2026-08-03 | 🔵 manual | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/maxtube.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/maxtube.json) | [`maxtube.json`](https://iamsmmh.github.io/OmniSource/maxtube.json) |
| **YTMusicUltimate** | `com.google.ios.youtubemusic` | `9.35.2` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/ytmusic.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/ytmusic.json) | [`ytmusic.json`](https://iamsmmh.github.io/OmniSource/ytmusic.json) |
| **MaxMusic** | `com.google.ios.youtubemusic` | `9.35.2` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/maxmusic.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/maxmusic.json) | [`maxmusic.json`](https://iamsmmh.github.io/OmniSource/maxmusic.json) |
| **UTM** | `com.utmapp.UTM` | `4.7.5` | 2026-01-03T17:51:54Z | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/utm.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/utm.json) | [`utm.json`](https://iamsmmh.github.io/OmniSource/utm.json) |
| **iNKillerPlus** | `com.burbn.instagram` | `445.0.0` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/inkillerplus.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/inkillerplus.json) | [`inkillerplus.json`](https://iamsmmh.github.io/OmniSource/inkillerplus.json) |
| **TTKillerPlus** | `com.zhiliaoapp.musically` | `46.7.0` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/ttkillerplus.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/ttkillerplus.json) | [`ttkillerplus.json`](https://iamsmmh.github.io/OmniSource/ttkillerplus.json) |
| **Winston** | `lo.cafe.winston` | `1.1.5` | 2024-06-24 | 🔴 unmaintained | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/winston.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/winston.json) | [`winston.json`](https://iamsmmh.github.io/OmniSource/winston.json) |
| **iTorrent** | `com.xitrix.iTorrent2` | `2.2.0` | 2026-07-19 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/itorrent.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/itorrent.json) | [`itorrent.json`](https://iamsmmh.github.io/OmniSource/itorrent.json) |
| **StikDebug** | `com.stik.stikdebug` | `3.1.10` | 2026-08-27 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/stikdebug.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/stikdebug.json) | [`stikdebug.json`](https://iamsmmh.github.io/OmniSource/stikdebug.json) |
| **BHTwitter** | `com.atebits.Tweetie2` | `4.4` | 2025-05-13 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/bhtwitter.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/bhtwitter.json) | [`bhtwitter.json`](https://iamsmmh.github.io/OmniSource/bhtwitter.json) |
| **LiveContainer** | `com.kdt.livecontainer` | `3.8.0` | 2026-07-17 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/livecontainer.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/livecontainer.json) | [`livecontainer.json`](https://iamsmmh.github.io/OmniSource/livecontainer.json) |
| **Feather** | `thewonderofyou.Feather` | `2.9.0` | 2026-07-05 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feather.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feather.json) | [`feather.json`](https://iamsmmh.github.io/OmniSource/feather.json) |
| **SideStore** | `com.SideStore.SideStore` | `0.6.3` | 2026-05-05 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/sidestore.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/sidestore.json) | [`sidestore.json`](https://iamsmmh.github.io/OmniSource/sidestore.json) |
| **Aidoku** | `app.aidoku.Aidoku` | `0.9` | 2026-09-03 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/aidoku.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/aidoku.json) | [`aidoku.json`](https://iamsmmh.github.io/OmniSource/aidoku.json) |
| **Provenance** | `org.provenance-emu.provenance` | `3.3.0` | 2026-03-14 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/provenance.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/provenance.json) | [`provenance.json`](https://iamsmmh.github.io/OmniSource/provenance.json) |

<!-- omnisource:catalog:end -->

**Columns** — *Status*: 🟢 stable · 🟡 beta · 🔵 manually published · 🔴 unmaintained.
*Download*: ✅ / ⚠️ reflects the last automated reachability probe.

## Where the info comes from

Every app in `catalog.json` declares its upstream and verification method, and the published entry is
generated from that upstream — the catalog is never the source of versions, dates or download URLs.

| Channel | Apps | What is official |
| --- | --- | --- |
| **GitHub Releases of the app itself** | Aidoku, BHTwitter, Feather, iTorrent, LiveContainer, Provenance, SideStore, SpotiFLAC, StikDebug, UTM, Winston, YTKACE, MaxMusic | The release, its IPA asset, date and notes come straight from the project's own GitHub release. |
| **Developer's own AltStore feed** | YTKillerPlus, iNKillerPlus, TTKillerPlus | iKarwan's source (`repo.ikghd.me`). When unreachable, the last verified build is kept and a mirror fallback is offered. |
| **Ready-to-sideload builds of official tweaks** | uYouEnhanced, YouTubePlus, YouPro, YouMod, YTMusicUltimate, MaxTube | The underlying tweak's project is the official source of record; because those projects publish `.deb` (or nothing), this source serves **community-built IPAs** of the official tweak, clearly labelled in each entry's metadata. |

Each feed entry embeds an `omnisource` metadata block with `status`, `verification` and
`compatibility` (including these source notes), so clients and users can see exactly where a build
came from.

## How it works

```
catalog.json ──▶ scripts/omnisource.py ──▶ feeds/*.json ──▶ GitHub Pages ──▶ your client
  (hand edited)   (every 6 h: sync from      (generated)      https://iamsmmh.github.io/OmniSource/
                  official upstreams,
                  probe links, build feeds)
```

`catalog.json` is the only hand-edited data file. Everything under `feeds/` (per-app feeds,
`apps.json`, `health.json`, `state.json`) and the root-level mirrors (`apps.json`, `<slug>.json`) is
generated — edit `catalog.json`, never the generated files.

| Pipeline | Runs | What it does |
| --- | --- | --- |
| **Sync & Publish** | every 6 h · on push | Resolve upstream releases, probe links, rebuild every feed, deploy Pages |
| **Validate** | every push & PR | Offline structural checks (`validate.py` + `validate_jq.sh`), reproducibility, `ruff`, `actionlint` |
| **Health Check** | daily | HEAD-probe every download URL and report broken links via a GitHub Issue |

## Repository layout

| Path | Purpose |
| --- | --- |
| `catalog.json` | Source of truth: apps, official upstreams, verification and compatibility metadata |
| `feeds/` | Generated AltStore v2 feeds + `health.json` + pipeline `state.json` |
| `assets/` | App and client icons served over Pages |
| `src/omnisource/` | Sync pipeline (providers, release tracking, AltStore feed rendering, validation) |
| `scripts/` | CLI wrappers: `omnisource.py` · `validate.py` · `validate_jq.sh` · `health_check.py` |
| `website/` | Minimal static GitHub Pages landing page |

## For developers

```bash
python3 scripts/omnisource.py     # sync official upstreams + rebuild every feed
python3 scripts/validate.py       # offline structural checks
bash scripts/validate_jq.sh       # jq-only lint + AltStore v2 checks
python3 scripts/health_check.py   # HEAD-probe every download URL
```

Golden rule: change `catalog.json`, never the generated files. Scripts are Python stdlib only — no
virtualenv, no dependencies.

## Adding an app

1. Add an entry to `catalog.json`: `slug`, identity, `icon` (add the file under `assets/`),
   `verification` (source method + publisher), `compatibility`, and an `upstream` block pointing at
   the **official** source (`repo` + matching `assetSuffixes` for GitHub releases, or `feedURL` for a
   developer AltStore feed; `manualRelease` only when no live upstream exists).
2. Run `python3 scripts/omnisource.py` and commit the regenerated feeds.

## Disclaimer

OmniSource is an independent community project. It aggregates third-party releases; some entries are
community-built IPAs of open-source tweaks whose projects publish no IPA themselves. All apps, code
and trademarks belong to their respective owners, and you are responsible for complying with
applicable laws and terms of service.

## License

[GPL-3.0](LICENSE) © the OmniSource contributors.
