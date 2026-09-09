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
URL manually. Each app also publishes its own standalone feed at
`https://iamsmmh.github.io/OmniSource/<slug>.json`, a per-app RSS release feed at
`https://iamsmmh.github.io/OmniSource/<slug>.xml`, and a combined release feed (`feed.xml`/`rss.xml`).
A machine-readable "What's new" timeline is published at `updates.json` for the website (see the
catalog below).

## Catalog

The complete generated catalog is available below. For a cleaner browsing experience, use the [OmniSource website](https://iamsmmh.github.io/OmniSource/).

<details>
<summary><strong>View all apps and source links</strong></summary>

<!-- omnisource:catalog:start -->

_Catalogue last changed 2026-09-09 · 22 apps · 22/22 downloads reachable._

| App | Bundle ID | Version | Updated | Status | Download | Install | Feed | RSS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **SpotiFLAC Mobile** | `com.zarz.spotiflacAndroid` | `4.9.6` | 2026-09-07 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/spotiflac.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/spotiflac.json) | [`spotiflac.json`](https://iamsmmh.github.io/OmniSource/spotiflac.json) | [`spotiflac.xml`](https://iamsmmh.github.io/OmniSource/spotiflac.xml) |
| **uYouEnhanced** | `com.google.ios.youtube` | `21.14.4` | 2026-08-22 | 🔵 manual | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/uyouenhanced.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/uyouenhanced.json) | [`uyouenhanced.json`](https://iamsmmh.github.io/OmniSource/uyouenhanced.json) | [`uyouenhanced.xml`](https://iamsmmh.github.io/OmniSource/uyouenhanced.xml) |
| **YouTubePlus** | `com.google.ios.youtube` | `21.24.3` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/ytlite.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/ytlite.json) | [`ytlite.json`](https://iamsmmh.github.io/OmniSource/ytlite.json) | [`ytlite.xml`](https://iamsmmh.github.io/OmniSource/ytlite.xml) |
| **YouPro** | `com.google.ios.youtube` | `21.24.3` | 2026-08-16 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/youpro.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/youpro.json) | [`youpro.json`](https://iamsmmh.github.io/OmniSource/youpro.json) | [`youpro.xml`](https://iamsmmh.github.io/OmniSource/youpro.xml) |
| **YTKillerPlus** | `com.google.ios.youtube` | `21.36.6` | 2026-09-09 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/ytkp.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/ytkp.json) | [`ytkp.json`](https://iamsmmh.github.io/OmniSource/ytkp.json) | [`ytkp.xml`](https://iamsmmh.github.io/OmniSource/ytkp.xml) |
| **YTKACE** | `com.google.ios.youtube` | `21.35.3` | 2026-08-31 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/ytkace.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/ytkace.json) | [`ytkace.json`](https://iamsmmh.github.io/OmniSource/ytkace.json) | [`ytkace.xml`](https://iamsmmh.github.io/OmniSource/ytkace.xml) |
| **YouMod** | `com.google.ios.youtube` | `21.35.3` | 2026-08-30 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/youmod.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/youmod.json) | [`youmod.json`](https://iamsmmh.github.io/OmniSource/youmod.json) | [`youmod.xml`](https://iamsmmh.github.io/OmniSource/youmod.xml) |
| **MaxTube** | `com.google.ios.youtube` | `21.31.3` | 2026-08-03 | 🔵 manual | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/maxtube.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/maxtube.json) | [`maxtube.json`](https://iamsmmh.github.io/OmniSource/maxtube.json) | [`maxtube.xml`](https://iamsmmh.github.io/OmniSource/maxtube.xml) |
| **YTMusicUltimate** | `com.google.ios.youtubemusic` | `9.35.2` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/ytmusic.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/ytmusic.json) | [`ytmusic.json`](https://iamsmmh.github.io/OmniSource/ytmusic.json) | [`ytmusic.xml`](https://iamsmmh.github.io/OmniSource/ytmusic.xml) |
| **MaxMusic** | `com.google.ios.youtubemusic` | `9.35.2` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/maxmusic.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/maxmusic.json) | [`maxmusic.json`](https://iamsmmh.github.io/OmniSource/maxmusic.json) | [`maxmusic.xml`](https://iamsmmh.github.io/OmniSource/maxmusic.xml) |
| **UTM** | `com.utmapp.UTM` | `4.7.5` | 2026-01-03T17:51:54Z | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/utm.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/utm.json) | [`utm.json`](https://iamsmmh.github.io/OmniSource/utm.json) | [`utm.xml`](https://iamsmmh.github.io/OmniSource/utm.xml) |
| **iNKillerPlus** | `com.burbn.instagram` | `446.0.0` | 2026-09-09 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/inkillerplus.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/inkillerplus.json) | [`inkillerplus.json`](https://iamsmmh.github.io/OmniSource/inkillerplus.json) | [`inkillerplus.xml`](https://iamsmmh.github.io/OmniSource/inkillerplus.xml) |
| **TTKillerPlus** | `com.zhiliaoapp.musically` | `46.8.0` | 2026-09-09 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/ttkillerplus.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/ttkillerplus.json) | [`ttkillerplus.json`](https://iamsmmh.github.io/OmniSource/ttkillerplus.json) | [`ttkillerplus.xml`](https://iamsmmh.github.io/OmniSource/ttkillerplus.xml) |
| **Winston** | `lo.cafe.winston` | `1.1.5` | 2024-06-24 | 🔴 unmaintained | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/winston.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/winston.json) | [`winston.json`](https://iamsmmh.github.io/OmniSource/winston.json) | [`winston.xml`](https://iamsmmh.github.io/OmniSource/winston.xml) |
| **iTorrent** | `com.xitrix.iTorrent2` | `2.2.0` | 2026-07-19 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/itorrent.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/itorrent.json) | [`itorrent.json`](https://iamsmmh.github.io/OmniSource/itorrent.json) | [`itorrent.xml`](https://iamsmmh.github.io/OmniSource/itorrent.xml) |
| **StikDebug** | `com.stik.stikdebug` | `3.1.10` | 2026-08-27 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/stikdebug.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/stikdebug.json) | [`stikdebug.json`](https://iamsmmh.github.io/OmniSource/stikdebug.json) | [`stikdebug.xml`](https://iamsmmh.github.io/OmniSource/stikdebug.xml) |
| **BHTwitter** | `com.atebits.Tweetie2` | `4.4` | 2025-05-13 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/bhtwitter.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/bhtwitter.json) | [`bhtwitter.json`](https://iamsmmh.github.io/OmniSource/bhtwitter.json) | [`bhtwitter.xml`](https://iamsmmh.github.io/OmniSource/bhtwitter.xml) |
| **LiveContainer** | `com.kdt.livecontainer` | `3.8.0` | 2026-07-17 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/livecontainer.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/livecontainer.json) | [`livecontainer.json`](https://iamsmmh.github.io/OmniSource/livecontainer.json) | [`livecontainer.xml`](https://iamsmmh.github.io/OmniSource/livecontainer.xml) |
| **Feather** | `thewonderofyou.Feather` | `2.9.0` | 2026-07-05 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feather.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feather.json) | [`feather.json`](https://iamsmmh.github.io/OmniSource/feather.json) | [`feather.xml`](https://iamsmmh.github.io/OmniSource/feather.xml) |
| **SideStore** | `com.SideStore.SideStore` | `0.6.3` | 2026-05-05 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/sidestore.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/sidestore.json) | [`sidestore.json`](https://iamsmmh.github.io/OmniSource/sidestore.json) | [`sidestore.xml`](https://iamsmmh.github.io/OmniSource/sidestore.xml) |
| **Aidoku** | `app.aidoku.Aidoku` | `0.9` | 2026-09-03 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/aidoku.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/aidoku.json) | [`aidoku.json`](https://iamsmmh.github.io/OmniSource/aidoku.json) | [`aidoku.xml`](https://iamsmmh.github.io/OmniSource/aidoku.xml) |
| **Provenance** | `org.provenance-emu.provenance` | `3.3.0` | 2026-03-14 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/provenance.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/provenance.json) | [`provenance.json`](https://iamsmmh.github.io/OmniSource/provenance.json) | [`provenance.xml`](https://iamsmmh.github.io/OmniSource/provenance.xml) |

<!-- omnisource:catalog:end -->

</details>

**Columns** — *Status*: 🟢 stable · 🟡 beta · 🔵 manually published · 🔴 unmaintained.
*Download*: ✅ / ⚠️ reflects the last automated reachability probe.
*Feed/RSS*: standalone AltStore feed and per-app RSS release feed for that app.

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
catalog.json ──▶ scripts/omnisource.py ──▶ feeds/*.json + feeds/*.xml ──▶ GitHub Pages ──▶ your client
  (hand edited)   (every 6 h: sync from      (generated)                   https://iamsmmh.github.io/OmniSource/
                  official upstreams,
                  probe links, build feeds)
```

`catalog.json` is the only hand-edited data file. Everything under `feeds/`—per-app feeds,
`apps.json`, the `updates.json` website timeline, per-app + combined RSS, health data, badges and
pipeline state—is generated. During deployment, the site builder also publishes these files at the
historical flat URLs, so existing subscribers keep working.

| Pipeline | Runs | What it does |
| --- | --- | --- |
| **Sync & Publish** | every 6 h · on push | Resolve upstream releases, probe links, rebuild every feed, deploy Pages |
| **Validate** | every push & PR | Offline structural checks (`validate.py` + `validate_jq.sh`), reproducibility, `ruff`, `actionlint` |
| **Health Check** | daily | HEAD-probe every download URL and report broken links via a GitHub Issue |

## Repository layout

| Path | Purpose |
| --- | --- |
| `catalog.json` | Source of truth: apps, official upstreams, verification and compatibility metadata |
| `config/` | Runtime defaults for sync, retries, health checks and history |
| `assets/` | App and client icons served over Pages |
| `src/omnisource/` | Organized Python package for providers, feeds, validation and release tracking |
| `scripts/` | Small CLI entry points, including the shared Pages site builder |
| `schemas/` | Catalog and AltStore feed contracts |
| `tests/` | Offline unit test suite |
| `feeds/` | All generated feeds, badges, RSS, health data and pipeline state |
| `website/` | Static interface organized into HTML, CSS and JavaScript |
| `docs/` | Maintainer documentation and repository map |

See the concise [repository guide](docs/REPOSITORY.md) before making structural changes.

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

Useful optional `upstream` knobs:

- `keepVersions` — how many releases the feed keeps per app (default `1`; `0` keeps every matching
  release). Keeping a few versions lets users roll back after a bad release.
- `includePrereleases` — opt an app into pre-release/beta builds when its upstream publishes them.
- `versionPattern` / `assetNamePattern` / `tagPrefix` — narrow which releases and assets are used
  when upstream tags differ from app versions.
- `minOSVersion` / `minOSVersionByTagNumber` — record the minimum iOS each build needs so the
  website can filter by device compatibility.

Remember that sideloading clients replace an installed app whose `bundleIdentifier` matches, so two
catalog entries must not share a bundle ID unless that replacement behaviour is intended (the
validator and website both surface these conflicts).

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) first. Issues use templates: [request an app](
https://github.com/iamsmmh/OmniSource/issues/new?template=01-app-request.yml), report a [broken
upstream](https://github.com/iamsmmh/OmniSource/issues/new?template=02-broken-upstream.yml), [file a
bug](https://github.com/iamsmmh/OmniSource/issues/new?template=03-bug-report.yml) or [suggest a
feature](https://github.com/iamsmmh/OmniSource/issues/new?template=04-feature-idea.yml).

## Disclaimer

OmniSource is an independent community project. It aggregates third-party releases; some entries are
community-built IPAs of open-source tweaks whose projects publish no IPA themselves. All apps, code
and trademarks belong to their respective owners, and you are responsible for complying with
applicable laws and terms of service.

## License

[GPL-3.0](LICENSE) © the OmniSource contributors.
