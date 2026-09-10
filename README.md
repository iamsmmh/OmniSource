<div align="center">

<img src="assets/OmniSource.png" width="132" alt="OmniSource logo">

# OmniSource

**The App Store for sideloaded iOS — one feed, five clients, always current.**

One AltStore-compatible source URL for **AltStore · SideStore · Feather · ESign · LiveContainer** — backed by a dependency-free web app with a live catalog, app comparison, source health, analytics, an install center and an offline-first PWA.

<!-- omnisource:stats:start -->

**58** apps · **48** upstream sources · **57** verified · **1** community verified · **58/58** downloads online · last sync **2026-09-10**.

<!-- omnisource:stats:end -->

<p>
  <a href="https://github.com/iamsmmh/OmniSource/actions/workflows/sync.yml"><img src="https://github.com/iamsmmh/OmniSource/actions/workflows/sync.yml/badge.svg" alt="Sync & Publish"></a>
  <a href="https://github.com/iamsmmh/OmniSource/actions/workflows/validate.yml"><img src="https://github.com/iamsmmh/OmniSource/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="https://img.shields.io/endpoint?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2Fbadge-apps.json"><img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2Fbadge-apps.json" alt="Apps"></a>
  <a href="https://img.shields.io/endpoint?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2Fbadge-health.json"><img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2Fbadge-health.json" alt="Downloads healthy"></a>
  <a href="https://img.shields.io/endpoint?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2Fbadge-sync.json"><img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2Fbadge-sync.json" alt="Last sync"></a>
  <a href="https://iamsmmh.github.io/OmniSource/"><img src="https://img.shields.io/website?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2F&label=website" alt="Website"></a>
  <a href="https://github.com/iamsmmh/OmniSource/stargazers"><img src="https://img.shields.io/github/stars/iamsmmh/OmniSource" alt="GitHub stars"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/iamsmmh/OmniSource" alt="License"></a>
</p>

<p>
  <a href="#-add-the-source"><b>🚀 Add the source</b></a> ·
  <a href="https://iamsmmh.github.io/OmniSource/"><b>🌐 Website</b></a> ·
  <a href="#-app-catalog"><b>📚 Catalog</b></a> ·
  <a href="#-how-it-works"><b>⚙️ How it works</b></a> ·
  <a href="#-machine-api"><b>🔌 API</b></a> ·
  <a href="#-frequently-asked-questions"><b>❓ FAQ</b></a> ·
  <a href="CONTRIBUTING.md"><b>🤝 Contributing</b></a>
</p>

</div>

---

## ✨ Why OmniSource?

| | |
| --- | --- |
| 🎯 **Official upstreams only** | Every release resolves from the developer's own GitHub Releases or AltStore feed. No random re-uploads, ever. |
| ✅ **Verified & health-checked** | Each app carries a verification label, and every download link is automatically probed so the catalog stays installable. |
| 🔄 **Fresh every 6 hours** | A scheduled pipeline syncs new releases, rebuilds every feed, and redeploys the site around the clock. |
| 📲 **One feed, five clients** | A single AltStore Source v2 URL works in AltStore, SideStore, Feather, ESign, and LiveContainer. |
| 🌐 **A real website, not just JSON** | Browse, search, compare, and install from a fast, dependency-free PWA with health dashboards and analytics. |
| 🔔 **Never miss a release** | Per-app RSS feeds, a combined release feed, and a machine-readable “What’s new” timeline. |

## 🚀 Add the source

### 1 · Copy the source URL

```
https://iamsmmh.github.io/OmniSource/apps.json
```

### 2 · Add it to your client

On your iPhone, open this page and tap your client — the source adds itself:

| Client | One-tap add |
| --- | --- |
| **AltStore** | <a href="altstore://source?url=https://iamsmmh.github.io/OmniSource/apps.json">➕ Add to AltStore</a> |
| **SideStore** | <a href="sidestore://source?url=https://iamsmmh.github.io/OmniSource/apps.json">➕ Add to SideStore</a> |
| **Feather** | <a href="feather://source/iamsmmh.github.io/OmniSource/apps.json">➕ Add to Feather</a> |
| **ESign** | Paste the URL manually — see the [install center](https://iamsmmh.github.io/OmniSource/install/) |
| **LiveContainer** | Paste the URL manually — see the [install center](https://iamsmmh.github.io/OmniSource/install/) |

> 💡 **Prefer manual setup?** Every client has an *Add Source* screen that accepts the URL above. The [install center](https://iamsmmh.github.io/OmniSource/install/) shows per-client, per-app instructions with auto-generated deep links.

### 3 · Browse & install

Open the **OmniSource** source inside your client, pick an app, and install. New versions flow in automatically on every refresh — nothing else to configure.

### Power-user feeds

Every app also publishes its own standalone feed under `feeds/<slug>.json` (subscribe to a single app instead of the whole catalog) and a per-app RSS release feed at `feeds/<slug>.xml`. Everything is combined into `feeds/feed.xml` / `feeds/rss.xml`, and the machine-readable timeline lives at `feeds/updates.json`.

## 🌐 Website

The live site is an immersive, dependency-free web app (HTML + modern CSS + vanilla JS, no build step) served by GitHub Pages:

| Page | What it does |
| --- | --- |
| [🏠 Home](https://iamsmmh.github.io/OmniSource/) | Hero, trending / recent / featured / verified rails, statistics, source health, install guide, full catalog with search + filters, release timeline |
| [⚖️ Compare](https://iamsmmh.github.io/OmniSource/compare/) | App-vs-app comparison (bundle, category, developer, size, verification…) — deep-linkable: `compare/?left=youpro&right=ytlite` |
| [💚 Source Health](https://iamsmmh.github.io/OmniSource/status/) | Uptime, latency, availability and sync state for every upstream source |
| [📊 Analytics](https://iamsmmh.github.io/OmniSource/analytics/) | App/source counts, weekly updates, verification mix, category distribution, health trends — charted from generated JSON, no backend |
| [📲 Install center](https://iamsmmh.github.io/OmniSource/install/) | Step-by-step instructions and auto-generated deep links, per app and for the master feed |
| [🔎 Search](https://iamsmmh.github.io/OmniSource/search/) | Full-text search over name, bundle, developer, source, category and tags — plus a ⌘K command palette on every page |
| [⭐ Favorites](https://iamsmmh.github.io/OmniSource/favorites/) | Keep a personal list of saved apps |
| [🗂️ Collections](https://iamsmmh.github.io/OmniSource/collections/) | Curated and custom app collections you can build, import, and export as JSON |
| [📄 App pages](https://iamsmmh.github.io/OmniSource/apps/ytlite/) | Every app has a static detail page (`apps/<slug>/`) with versions, screenshots, related apps, and install actions |

The site is a **PWA**: installable (manifest + shortcuts), offline-first (service worker precaches the shell and caches every feed and app page), with a “new version available” reload prompt.

## 📚 App catalog

The complete generated catalog is below — it refreshes automatically on every sync. For a cleaner browsing experience, use the [OmniSource website](https://iamsmmh.github.io/OmniSource/).

<details>
<summary><strong>📋 View all apps and source links</strong></summary>

<!-- omnisource:catalog:start -->

_Catalogue last changed 2026-09-10 · 58 apps · 58/58 downloads reachable._

| App | Bundle ID | Version | Updated | Status | Download | Install | Feed | RSS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **SpotiFLAC Mobile** | `com.zarz.spotiflacAndroid` | `4.9.6` | 2026-09-07 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/spotiflac.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/spotiflac.json) | [`spotiflac.json`](https://iamsmmh.github.io/OmniSource/feeds/spotiflac.json) | [`spotiflac.xml`](https://iamsmmh.github.io/OmniSource/feeds/spotiflac.xml) |
| **uYouEnhanced** | `com.google.ios.youtube` | `21.14.4` | 2026-08-22 | 🔵 manual | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/uyouenhanced.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/uyouenhanced.json) | [`uyouenhanced.json`](https://iamsmmh.github.io/OmniSource/feeds/uyouenhanced.json) | [`uyouenhanced.xml`](https://iamsmmh.github.io/OmniSource/feeds/uyouenhanced.xml) |
| **YouTubePlus** | `com.google.ios.youtube` | `21.24.3` | 2026-09-09 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ytlite.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ytlite.json) | [`ytlite.json`](https://iamsmmh.github.io/OmniSource/feeds/ytlite.json) | [`ytlite.xml`](https://iamsmmh.github.io/OmniSource/feeds/ytlite.xml) |
| **YouPro** | `com.google.ios.youtube` | `21.36.6` | 2026-09-10 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/youpro.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/youpro.json) | [`youpro.json`](https://iamsmmh.github.io/OmniSource/feeds/youpro.json) | [`youpro.xml`](https://iamsmmh.github.io/OmniSource/feeds/youpro.xml) |
| **YTKillerPlus** | `com.google.ios.youtube` | `21.36.6` | 2026-09-09 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ytkp.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ytkp.json) | [`ytkp.json`](https://iamsmmh.github.io/OmniSource/feeds/ytkp.json) | [`ytkp.xml`](https://iamsmmh.github.io/OmniSource/feeds/ytkp.xml) |
| **YTKACE** | `com.google.ios.youtube` | `21.35.3` | 2026-08-31 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ytkace.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ytkace.json) | [`ytkace.json`](https://iamsmmh.github.io/OmniSource/feeds/ytkace.json) | [`ytkace.xml`](https://iamsmmh.github.io/OmniSource/feeds/ytkace.xml) |
| **YouMod** | `com.google.ios.youtube` | `21.36.6` | 2026-09-09 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/youmod.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/youmod.json) | [`youmod.json`](https://iamsmmh.github.io/OmniSource/feeds/youmod.json) | [`youmod.xml`](https://iamsmmh.github.io/OmniSource/feeds/youmod.xml) |
| **MaxTube** | `com.google.ios.youtube` | `21.31.3` | 2026-08-03 | 🔵 manual | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/maxtube.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/maxtube.json) | [`maxtube.json`](https://iamsmmh.github.io/OmniSource/feeds/maxtube.json) | [`maxtube.xml`](https://iamsmmh.github.io/OmniSource/feeds/maxtube.xml) |
| **YTMusicUltimate** | `com.google.ios.youtubemusic` | `9.36.1` | 2026-09-09 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ytmusic.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ytmusic.json) | [`ytmusic.json`](https://iamsmmh.github.io/OmniSource/feeds/ytmusic.json) | [`ytmusic.xml`](https://iamsmmh.github.io/OmniSource/feeds/ytmusic.xml) |
| **MaxMusic** | `com.google.ios.youtubemusic` | `9.36.1` | 2026-09-10 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/maxmusic.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/maxmusic.json) | [`maxmusic.json`](https://iamsmmh.github.io/OmniSource/feeds/maxmusic.json) | [`maxmusic.xml`](https://iamsmmh.github.io/OmniSource/feeds/maxmusic.xml) |
| **UTM** | `com.utmapp.UTM` | `4.7.5` | 2026-01-03T17:51:54Z | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/utm.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/utm.json) | [`utm.json`](https://iamsmmh.github.io/OmniSource/feeds/utm.json) | [`utm.xml`](https://iamsmmh.github.io/OmniSource/feeds/utm.xml) |
| **iNKillerPlus** | `com.burbn.instagram` | `446.0.0` | 2026-09-09 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/inkillerplus.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/inkillerplus.json) | [`inkillerplus.json`](https://iamsmmh.github.io/OmniSource/feeds/inkillerplus.json) | [`inkillerplus.xml`](https://iamsmmh.github.io/OmniSource/feeds/inkillerplus.xml) |
| **TTKillerPlus** | `com.zhiliaoapp.musically` | `46.8.0` | 2026-09-09 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ttkillerplus.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ttkillerplus.json) | [`ttkillerplus.json`](https://iamsmmh.github.io/OmniSource/feeds/ttkillerplus.json) | [`ttkillerplus.xml`](https://iamsmmh.github.io/OmniSource/feeds/ttkillerplus.xml) |
| **Winston** | `lo.cafe.winston` | `1.1.5` | 2024-06-24 | 🔴 unmaintained | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/winston.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/winston.json) | [`winston.json`](https://iamsmmh.github.io/OmniSource/feeds/winston.json) | [`winston.xml`](https://iamsmmh.github.io/OmniSource/feeds/winston.xml) |
| **iTorrent** | `com.xitrix.iTorrent2` | `2.2.0` | 2026-07-19 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/itorrent.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/itorrent.json) | [`itorrent.json`](https://iamsmmh.github.io/OmniSource/feeds/itorrent.json) | [`itorrent.xml`](https://iamsmmh.github.io/OmniSource/feeds/itorrent.xml) |
| **StikDebug** | `com.stik.stikdebug` | `3.1.10` | 2026-08-27 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/stikdebug.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/stikdebug.json) | [`stikdebug.json`](https://iamsmmh.github.io/OmniSource/feeds/stikdebug.json) | [`stikdebug.xml`](https://iamsmmh.github.io/OmniSource/feeds/stikdebug.xml) |
| **BHTwitter** | `com.atebits.Tweetie2` | `4.4` | 2025-05-13 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/bhtwitter.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/bhtwitter.json) | [`bhtwitter.json`](https://iamsmmh.github.io/OmniSource/feeds/bhtwitter.json) | [`bhtwitter.xml`](https://iamsmmh.github.io/OmniSource/feeds/bhtwitter.xml) |
| **LiveContainer** | `com.kdt.livecontainer` | `3.8.0` | 2026-07-17 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/livecontainer.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/livecontainer.json) | [`livecontainer.json`](https://iamsmmh.github.io/OmniSource/feeds/livecontainer.json) | [`livecontainer.xml`](https://iamsmmh.github.io/OmniSource/feeds/livecontainer.xml) |
| **Feather** | `thewonderofyou.Feather` | `2.9.0` | 2026-07-05 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/feather.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/feather.json) | [`feather.json`](https://iamsmmh.github.io/OmniSource/feeds/feather.json) | [`feather.xml`](https://iamsmmh.github.io/OmniSource/feeds/feather.xml) |
| **SideStore** | `com.SideStore.SideStore` | `0.6.3` | 2026-05-05 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/sidestore.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/sidestore.json) | [`sidestore.json`](https://iamsmmh.github.io/OmniSource/feeds/sidestore.json) | [`sidestore.xml`](https://iamsmmh.github.io/OmniSource/feeds/sidestore.xml) |
| **Aidoku** | `app.aidoku.Aidoku` | `0.9` | 2026-09-03 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/aidoku.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/aidoku.json) | [`aidoku.json`](https://iamsmmh.github.io/OmniSource/feeds/aidoku.json) | [`aidoku.xml`](https://iamsmmh.github.io/OmniSource/feeds/aidoku.xml) |
| **Provenance** | `org.provenance-emu.provenance` | `3.3.0` | 2026-03-14 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/provenance.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/provenance.json) | [`provenance.json`](https://iamsmmh.github.io/OmniSource/feeds/provenance.json) | [`provenance.xml`](https://iamsmmh.github.io/OmniSource/feeds/provenance.xml) |
| **Delta** | `com.rileytestut.Delta` | `1.6` | 2024-07-11 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/delta.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/delta.json) | [`delta.json`](https://iamsmmh.github.io/OmniSource/feeds/delta.json) | [`delta.xml`](https://iamsmmh.github.io/OmniSource/feeds/delta.xml) |
| **PPSSPP** | `org.ppsspp.ppsspp` | `1.20.4` | 2026-05-16 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ppsspp.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ppsspp.json) | [`ppsspp.json`](https://iamsmmh.github.io/OmniSource/feeds/ppsspp.json) | [`ppsspp.xml`](https://iamsmmh.github.io/OmniSource/feeds/ppsspp.xml) |
| **Yattee** | `stream.yattee.app` | `1.5.1` | 2024-01-28 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/yattee.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/yattee.json) | [`yattee.json`](https://iamsmmh.github.io/OmniSource/feeds/yattee.json) | [`yattee.xml`](https://iamsmmh.github.io/OmniSource/feeds/yattee.xml) |
| **Streamyfin** | `com.fredrikburmester.streamyfin` | `0.54.1` | 2026-06-02 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/streamyfin.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/streamyfin.json) | [`streamyfin.json`](https://iamsmmh.github.io/OmniSource/feeds/streamyfin.json) | [`streamyfin.xml`](https://iamsmmh.github.io/OmniSource/feeds/streamyfin.xml) |
| **Spotube** | `oss.krtirtho.spotube.stable` | `5.1.2` | 2026-06-05 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/spotube.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/spotube.json) | [`spotube.json`](https://iamsmmh.github.io/OmniSource/feeds/spotube.json) | [`spotube.xml`](https://iamsmmh.github.io/OmniSource/feeds/spotube.xml) |
| **Jellify** | `com.cosmonautical.jellify` | `1.2.10` | 2026-09-02 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/jellify.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/jellify.json) | [`jellify.json`](https://iamsmmh.github.io/OmniSource/feeds/jellify.json) | [`jellify.xml`](https://iamsmmh.github.io/OmniSource/feeds/jellify.xml) |
| **Zeus** | `com.zeusln.zeus` | `13.2.1` | 2026-09-02 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/zeus.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/zeus.json) | [`zeus.json`](https://iamsmmh.github.io/OmniSource/feeds/zeus.json) | [`zeus.xml`](https://iamsmmh.github.io/OmniSource/feeds/zeus.xml) |
| **BlueWallet** | `io.bluewallet.bluewallet` | `8.0.1` | 2026-07-21 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/bluewallet.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/bluewallet.json) | [`bluewallet.json`](https://iamsmmh.github.io/OmniSource/feeds/bluewallet.json) | [`bluewallet.xml`](https://iamsmmh.github.io/OmniSource/feeds/bluewallet.xml) |
| **Voyager** | `app.vger.voyager` | `2.49.0` | 2026-09-06 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/voyager.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/voyager.json) | [`voyager.json`](https://iamsmmh.github.io/OmniSource/feeds/voyager.json) | [`voyager.xml`](https://iamsmmh.github.io/OmniSource/feeds/voyager.xml) |
| **Saber** | `com.adilhanney.saber` | `1.36.1` | 2026-08-30 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/saber.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/saber.json) | [`saber.json`](https://iamsmmh.github.io/OmniSource/feeds/saber.json) | [`saber.xml`](https://iamsmmh.github.io/OmniSource/feeds/saber.xml) |
| **Anx Reader** | `com.anxcye.anxReader` | `1.14.0` | 2026-03-19 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/anxreader.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/anxreader.json) | [`anxreader.json`](https://iamsmmh.github.io/OmniSource/feeds/anxreader.json) | [`anxreader.xml`](https://iamsmmh.github.io/OmniSource/feeds/anxreader.xml) |
| **Apollo** | `com.christianselig.Apollo` | `3.6.0` | 2026-08-18 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/apollo.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/apollo.json) | [`apollo.json`](https://iamsmmh.github.io/OmniSource/feeds/apollo.json) | [`apollo.xml`](https://iamsmmh.github.io/OmniSource/feeds/apollo.xml) |
| **DolphiniOS** | `me.oatmealdome.DolphiniOS-njb` | `5.0.0` | 2026-06-20 | 🟡 beta | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/dolphinish.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/dolphinish.json) | [`dolphinish.json`](https://iamsmmh.github.io/OmniSource/feeds/dolphinish.json) | [`dolphinish.xml`](https://iamsmmh.github.io/OmniSource/feeds/dolphinish.xml) |
| **iSH** | `app.ish.iSH` | `813` | 2026-08-22 | 🟡 beta | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ish.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ish.json) | [`ish.json`](https://iamsmmh.github.io/OmniSource/feeds/ish.json) | [`ish.xml`](https://iamsmmh.github.io/OmniSource/feeds/ish.xml) |
| **qBitControl** | `MikeMichael225.qBitControl` | `1.4.1` | 2026-07-23 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/qbitcontrol.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/qbitcontrol.json) | [`qbitcontrol.json`](https://iamsmmh.github.io/OmniSource/feeds/qbitcontrol.json) | [`qbitcontrol.xml`](https://iamsmmh.github.io/OmniSource/feeds/qbitcontrol.xml) |
| **qBitConnect** | `com.bluematter.qbitconnect` | `1.6.6` | 2025-11-02 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/qbitconnect.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/qbitconnect.json) | [`qbitconnect.json`](https://iamsmmh.github.io/OmniSource/feeds/qbitconnect.json) | [`qbitconnect.xml`](https://iamsmmh.github.io/OmniSource/feeds/qbitconnect.xml) |
| **VCMI** | `eu.vcmi.vcmiclient` | `1.7.5` | 2026-08-15 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/vcmi.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/vcmi.json) | [`vcmi.json`](https://iamsmmh.github.io/OmniSource/feeds/vcmi.json) | [`vcmi.xml`](https://iamsmmh.github.io/OmniSource/feeds/vcmi.xml) |
| **MAME4iOS** | `com.example.mame4ios` | `2022.5` | 2022-12-12 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/mame4ios.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/mame4ios.json) | [`mame4ios.json`](https://iamsmmh.github.io/OmniSource/feeds/mame4ios.json) | [`mame4ios.xml`](https://iamsmmh.github.io/OmniSource/feeds/mame4ios.xml) |
| **qBitController** | `dev.bartuzen.qbitcontroller` | `2.2.1` | 2026-07-28 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/qbitcontroller.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/qbitcontroller.json) | [`qbitcontroller.json`](https://iamsmmh.github.io/OmniSource/feeds/qbitcontroller.json) | [`qbitcontroller.xml`](https://iamsmmh.github.io/OmniSource/feeds/qbitcontroller.xml) |
| **Mini vMac** | `net.namedfork.minivmac` | `2.6` | 2024-07-09 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/minivmac.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/minivmac.json) | [`minivmac.json`](https://iamsmmh.github.io/OmniSource/feeds/minivmac.json) | [`minivmac.xml`](https://iamsmmh.github.io/OmniSource/feeds/minivmac.xml) |
| **StikNES** | `com.stik.StikNES` | `2.0.2` | 2025-02-23 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/stiknes.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/stiknes.json) | [`stiknes.json`](https://iamsmmh.github.io/OmniSource/feeds/stiknes.json) | [`stiknes.xml`](https://iamsmmh.github.io/OmniSource/feeds/stiknes.xml) |
| **TwitchAdBlock** | `tv.twitch` | `30.7` | 2026-08-14 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/twitchadblock.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/twitchadblock.json) | [`twitchadblock.json`](https://iamsmmh.github.io/OmniSource/feeds/twitchadblock.json) | [`twitchadblock.xml`](https://iamsmmh.github.io/OmniSource/feeds/twitchadblock.xml) |
| **NeoFreeBird** | `com.atebits.Tweetie2` | `2.2` | 2025-11-03 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/neofreebird.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/neofreebird.json) | [`neofreebird.json`](https://iamsmmh.github.io/OmniSource/feeds/neofreebird.json) | [`neofreebird.xml`](https://iamsmmh.github.io/OmniSource/feeds/neofreebird.xml) |
| **Conduit** | `app.cogwheel.conduit` | `4.1.4` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/conduit.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/conduit.json) | [`conduit.json`](https://iamsmmh.github.io/OmniSource/feeds/conduit.json) | [`conduit.xml`](https://iamsmmh.github.io/OmniSource/feeds/conduit.xml) |
| **Fladder** | `nl.jknaapen.fladder` | `0.11.1` | 2026-09-08 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/fladder.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/fladder.json) | [`fladder.json`](https://iamsmmh.github.io/OmniSource/feeds/fladder.json) | [`fladder.xml`](https://iamsmmh.github.io/OmniSource/feeds/fladder.xml) |
| **AnymeX** | `com.ryan.anymex` | `3.1.7` | 2026-08-30 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/anymex.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/anymex.json) | [`anymex.json`](https://iamsmmh.github.io/OmniSource/feeds/anymex.json) | [`anymex.xml`](https://iamsmmh.github.io/OmniSource/feeds/anymex.xml) |
| **Sora** | `me.cranci.sulfur` | `1.3.0` | 2026-08-20 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/sora.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/sora.json) | [`sora.json`](https://iamsmmh.github.io/OmniSource/feeds/sora.json) | [`sora.xml`](https://iamsmmh.github.io/OmniSource/feeds/sora.xml) |
| **RainTweak** | `com.hammerandchisel.discord` | `0.9.3` | 2026-06-19 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/raintweak.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/raintweak.json) | [`raintweak.json`](https://iamsmmh.github.io/OmniSource/feeds/raintweak.json) | [`raintweak.xml`](https://iamsmmh.github.io/OmniSource/feeds/raintweak.xml) |
| **Infuse Plus** | `com.firecore.infuse` | `8.5.3` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/infuseplus.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/infuseplus.json) | [`infuseplus.json`](https://iamsmmh.github.io/OmniSource/feeds/infuseplus.json) | [`infuseplus.xml`](https://iamsmmh.github.io/OmniSource/feeds/infuseplus.xml) |
| **Glow** | `com.facebook.Facebook.glow` | `577.1` | 2026-09-05 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/glow.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/glow.json) | [`glow.json`](https://iamsmmh.github.io/OmniSource/feeds/glow.json) | [`glow.xml`](https://iamsmmh.github.io/OmniSource/feeds/glow.xml) |
| **Swiftgram** | `app.swiftgram.ios` | `12.9.2` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/swiftgram.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/swiftgram.json) | [`swiftgram.json`](https://iamsmmh.github.io/OmniSource/feeds/swiftgram.json) | [`swiftgram.xml`](https://iamsmmh.github.io/OmniSource/feeds/swiftgram.xml) |
| **Telegram MxGram** | `ph.telegra.Telegraph` | `12.9.3` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/telegram-mxgram.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/telegram-mxgram.json) | [`telegram-mxgram.json`](https://iamsmmh.github.io/OmniSource/feeds/telegram-mxgram.json) | [`telegram-mxgram.xml`](https://iamsmmh.github.io/OmniSource/feeds/telegram-mxgram.xml) |
| **iQFace** | `com.facebook.Facebook` | `577.1` | 2026-09-05 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/iqface.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/iqface.json) | [`iqface.json`](https://iamsmmh.github.io/OmniSource/feeds/iqface.json) | [`iqface.xml`](https://iamsmmh.github.io/OmniSource/feeds/iqface.xml) |
| **RyukGram** | `com.burbn.instagram` | `445.0.0` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ryukgram.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ryukgram.json) | [`ryukgram.json`](https://iamsmmh.github.io/OmniSource/feeds/ryukgram.json) | [`ryukgram.xml`](https://iamsmmh.github.io/OmniSource/feeds/ryukgram.xml) |
| **Sparkle** | `com.burbn.instagram.sparkle` | `445.0.0` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/sparkle.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/sparkle.json) | [`sparkle.json`](https://iamsmmh.github.io/OmniSource/feeds/sparkle.json) | [`sparkle.xml`](https://iamsmmh.github.io/OmniSource/feeds/sparkle.xml) |
| **RedditFilter** | `com.atebits.Tweetie2` | `2025.37.0` | 2025-09-26 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/redditfilter.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/redditfilter.json) | [`redditfilter.json`](https://iamsmmh.github.io/OmniSource/feeds/redditfilter.json) | [`redditfilter.xml`](https://iamsmmh.github.io/OmniSource/feeds/redditfilter.xml) |

<!-- omnisource:catalog:end -->

</details>

**Columns** — *Status*: 🟢 stable · 🟡 beta · 🔵 manually published · 🔴 unmaintained.
*Download*: ✅ / ⚠️ reflects the last automated reachability probe.
*Feed/RSS*: standalone AltStore feed and per-app RSS release feed for that app.

## 🔍 Where the info comes from

Every app in `catalog.json` declares its upstream and verification method, and the published entry is generated from that upstream — the catalog is never the source of versions, dates or download URLs.

| Channel | Apps | What is official |
| --- | --- | --- |
| **GitHub Releases of the app itself** | Aidoku, BHTwitter, Feather, iTorrent, LiveContainer, Provenance, SideStore, SpotiFLAC, StikDebug, UTM, Winston, YTKACE, MaxMusic | The release, its IPA asset, date and notes come straight from the project's own GitHub release. |
| **Developer's own AltStore feed** | YTKillerPlus, iNKillerPlus, TTKillerPlus | iKarwan's source (`repo.ikghd.me`). When unreachable, the last verified build is kept and a mirror fallback is offered. |
| **Ready-to-sideload builds of official tweaks** | uYouEnhanced, YouTubePlus, YouPro, YouMod, YTMusicUltimate, MaxTube | The underlying tweak's project is the official source of record; because those projects publish `.deb` (or nothing), this source serves **community-built IPAs** of the official tweak, clearly labelled in each entry's metadata. |

Each feed entry embeds an `omnisource` metadata block with `status`, `verification` and `compatibility` (including these source notes), so clients and users can see exactly where a build came from.

## ⚙️ How it works

### Architecture

```
catalog.json   (hand-edited source of truth)
      │
      ▼
scripts/omnisource.py  ──▶  src/omnisource/  (Python, stdlib-only)
      │                         ├─ providers/    GitHub Releases + external-feed adapters
      │                         ├─ feeds/        AltStore v2, RSS, updates-timeline renderers
      │                         ├─ validation    offline rule engine (catalog, feeds, docs, pages)
      │                         ├─ intelligence  trending · related · reputation · download-intel
      │                         │                community · search-index · compare · screenshots
      │                         ├─ install       per-client deep-link cards
      │                         ├─ app_pages     App-Store-style static pages (apps/<slug>/)
      │                         └─ site          _site/ builder (sitemap, robots, API mirror, minify)
      ▼
feeds/   (canonical JSON/XML)        apps/<slug>/   (pages)
      │                                   │
      └───────────────┬───────────────────┘
                      ▼
   scripts/build_site.py  ──▶  _site/  (the deployable site, full URL family)
                      │
                      ▼
        GitHub Pages  ──▶  website + /apps.json + /feeds/… + /api/…
```

* **Data plane** — `catalog.json` is the only hand-edited data file. The pipeline syncs official upstreams, probes every download link and regenerates all feeds, intelligence documents, badges and app pages. Generated files are never hand-edited.
* **Site plane** — hand-maintained page sources at the repository root (`index.html`, `install/`, `js/`, `sw.js`, …) plus the generated feeds and app pages. `feeds/` is the single source of truth; the only feed mirrored at the root is `/apps.json` (the installable source URL), and `scripts/build_site.py` assembles the full flat URL family (`/<slug>.json`, `/<slug>.xml`, `feed.xml`, …) into the `_site/` artifact for the `actions/deploy-pages` deployment — so the repository tree stays clean while every historical subscriber URL keeps working.
* **Presentation plane** — HTML + modern CSS + vanilla JS. No framework, no build step, no runtime dependencies. One design system (`assets/design-system/`) styles the website and the generated app pages alike; shared logic lives in `js/core.js` (theme, ⌘K palette, search engine, PWA) and `js/site.js` (page renderers).

### Generation flow

1. **Sync** — for every catalog app, resolve the newest release from its declared upstream (GitHub Releases or the developer's AltStore feed), download metadata only (never the IPA), and store versions, sizes, hashes and dates in `feeds/state.json`.
2. **Health** — HEAD-probe (ranged-GET fallback) every primary + fallback download URL; record reachability, latency and staleness.
3. **Build** — render per-app AltStore feeds, `apps.json`, RSS, `updates.json`, badges, all intelligence documents and one static page per app; refresh the marked stats/catalog blocks in this README.
4. **Validate** — the offline rule engine (`scripts/validate.py`) plus jq contract checks run on every push; `check_reproducible.py` proves an offline rebuild produces byte-identical output (date values normalized).
5. **Publish** — `/apps.json` and the `/api/` mirror are refreshed in the same run, and `scripts/build_site.py` assembles `_site/` for `actions/deploy-pages@v4`.

| Pipeline | Runs | What it does |
| --- | --- | --- |
| **Sync & Publish** (`.github/workflows/sync.yml`) | every 6 h · on push | Sync → health → build → publish root URLs + `_site/` → deploy Pages |
| **Validate** (`.github/workflows/validate.yml`) | every push & PR | Offline structural checks, mirror drift, reproducibility, `ruff`, `actionlint` |
| **Merge** (`.github/workflows/merge.yml`) | on `feeds/*.json` change | Rebuild the unified `feeds/apps.json` from the modular feeds and republish the root URLs |
| **Health Check** (`.github/workflows/health-check.yml`) | daily | Probe every download URL; open a GitHub Issue on breakage |

## 🗂️ Repository layout

| Path | Purpose |
| --- | --- |
| `catalog.json` | Source of truth: apps, official upstreams, verification and compatibility metadata |
| `apps.json` | The installable source URL (byte-identical to `feeds/apps.json`) |
| `config/` | Runtime defaults for sync, retries, health checks and history |
| `assets/` | App/client icons (PNG + WebP) and the shared design system |
| `src/omnisource/` | The Python package: providers, feed renderers, validation, intelligence engines, app pages, site builder |
| `scripts/` | Thin CLI entry points over the package (one command, one module) |
| `schemas/` | Catalog and AltStore feed contracts |
| `tests/` | Offline unit test suite |
| `feeds/` | Generated feeds, RSS, badges, health data, intelligence documents, pipeline state |
| `api/` | Machine-readable mirror of every feed (JSON + `.gz` twins) |
| `apps/<slug>/` | Generated App-Store-style app pages |
| `index.html`, `install/`, `js/`, `sw.js`, … | The website sources: hand-maintained pages + design system (see `docs/website.md`) |
| `sdk/` | Zero-dependency client SDKs (JavaScript + Python) |
| `docs/` | Repository guide, API contracts, audit, and the [cleanup report](docs/cleanup-report.md) |

See the [repository guide](docs/REPOSITORY.md) for the detailed map and data-flow diagram.

## 🚢 Deployment

Deployment is fully automated — push to `main` and GitHub Pages updates:

1. `sync.yml` runs the pipeline (sync, health, build) and commits the regenerated feeds/pages back via a bot push.
2. It assembles the site with `python3 scripts/build_site.py` and uploads `_site/` with `actions/upload-pages-artifact@v3`.
3. A separate `deploy` job publishes it with `actions/deploy-pages@v4` (environment: `github-pages`).
4. `validate.yml` guards every push and PR; the daily `health-check.yml` files breakage issues.

Local development mirrors production exactly:

```bash
make build      # sync + health + build (python3 scripts/omnisource.py)
make site       # assemble _site/
make serve      # serve _site/ on http://localhost:8000
make check      # ruff + validator + jq checks + unit tests
```

The service worker is versioned (`omnisource-vN`): bump the version in `sw.js` whenever the cached asset set changes, and the update toast in `js/core.js` offers the reload.

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) first. Issues use templates: [request an app](https://github.com/iamsmmh/OmniSource/issues/new?template=01-app-request.yml), report a [broken upstream](https://github.com/iamsmmh/OmniSource/issues/new?template=02-broken-upstream.yml), [file a bug](https://github.com/iamsmmh/OmniSource/issues/new?template=03-bug-report.yml) or [suggest a feature](https://github.com/iamsmmh/OmniSource/issues/new?template=04-feature-idea.yml).

Developer commands:

```bash
python3 scripts/omnisource.py              # sync official upstreams + rebuild everything
python3 scripts/omnisource.py --no-sync    # rebuild from feeds/state.json (offline)
python3 scripts/validate.py                # offline structural checks (feeds + docs + pages)
bash scripts/validate_jq.sh                # jq-only lint + AltStore v2 checks
python3 scripts/check_reproducible.py      # offline rebuild must not drift
python3 scripts/health_check.py            # HEAD-probe every download URL
python3 scripts/build_site.py              # assemble the deployable _site/
python3 -m unittest discover -s tests      # run the test suite
```

Golden rule: change `catalog.json`, never the generated files. Scripts are Python stdlib only — no virtualenv, no dependencies.

**Adding an app**

1. Add an entry to `catalog.json`: `slug`, identity, `icon` (add a PNG under `assets/` and a WebP twin), `verification` (source method + publisher), `compatibility`, and an `upstream` block pointing at the **official** source (`repo` + matching `assetSuffixes` for GitHub releases, or `feedURL` for a developer AltStore feed; `manualRelease` only when no live upstream exists).
2. Run `python3 scripts/omnisource.py` and commit the regenerated feeds, app page and README blocks.

Useful optional `upstream` knobs:

- `keepVersions` — how many releases the feed keeps per app (default `1`; `0` keeps every matching release). Keeping a few versions lets users roll back after a bad release.
- `includePrereleases` — opt an app into pre-release/beta builds when its upstream publishes them.
- `versionPattern` / `assetNamePattern` / `tagPrefix` — narrow which releases and assets are used when upstream tags differ from app versions.
- `minOSVersion` / `minOSVersionByTagNumber` — record the minimum iOS each build needs so the website can filter by device compatibility.

Sideloading clients replace an installed app whose `bundleIdentifier` matches, so two catalog entries must not share a bundle ID unless that replacement behaviour is intended (the validator and website both surface these conflicts).

## 🔌 Machine API

Every build publishes a generated API under `/api/` on the site (see [docs/API.md](docs/API.md)): `apps.json`, `catalog.json` (discovery index), `sources.json`, `verification.json`, `status.json`, `duplicates.json`, `analytics.json`, `updates.json`, `health.json`, plus the discovery layer: `trending.json`, `related.json`, `reputation.json`, `download-intelligence.json`, `community.json`, `install.json`, `search-index.json`, `compare.json` and `screenshots.json`. Each JSON document is also published as a gzip twin and mirrored in `api/index.json`. The website consumes the same documents; zero-dependency client libraries live in [`sdk/javascript/`](sdk/javascript/) and [`sdk/python/`](sdk/python/).

## 🧭 Discovery features

* **Trending** — `feeds/trending.json` ranks every app by recency, availability, featured status and verification level; powers the home rails.
* **Related apps** — `feeds/related.json` builds a relationship graph from bundle identifier, category, developer and tags.
* **Source reputation** — `feeds/reputation.json` scores each upstream on uptime, update cadence and broken releases (TRUSTED / RELIABLE / AVERAGE / EXPERIMENTAL).
* **Download intelligence** — `feeds/download-intelligence.json` reports per-app availability, latency, mirror count and release consistency.
* **Install cards** — `feeds/install.json` generates AltStore / SideStore / Feather / ESign / LiveContainer install URLs (never hard-coded).
* **Search index** — `feeds/search-index.json` is a Fuse.js-compatible index behind the ⌘K palette and the [search page](https://iamsmmh.github.io/OmniSource/search/), with history and popular searches.
* **Comparison** — `feeds/compare.json` precomputes every pair; the [compare page](https://iamsmmh.github.io/OmniSource/compare/) deep-links as `?left=<slug>&right=<slug>`.
* **Source health** — `feeds/status.json` drives the [health center](https://iamsmmh.github.io/OmniSource/status/) (uptime, latency, sync state).
* **Analytics** — `feeds/analytics.json` (totals, weekly changes, 30-day history) drives the [dashboard](https://iamsmmh.github.io/OmniSource/analytics/).
* **Community** — `feeds/community.json` lists popular, recently added, rising and requested apps.

## ❓ Frequently asked questions

**How do app updates work?**
The pipeline checks every upstream every 6 hours. Just refresh sources in your client and new versions appear like any other update. Prefer push-style awareness? Subscribe to an app's RSS feed (`feeds/<slug>.xml`) or the combined `feeds/feed.xml`.

**Can I install two YouTube apps side by side?**
No — apps that share a `bundleIdentifier` (e.g. all the YouTube clients, or YTMusicUltimate + MaxMusic) replace each other on install. Pick one; the [compare page](https://iamsmmh.github.io/OmniSource/compare/) helps you choose. The website warns you about these conflicts.

**What do the status colors mean?**
🟢 stable · 🟡 beta · 🔵 manually published (no live upstream to sync from) · 🔴 unmaintained (kept for reference, may be outdated).

**What does ✅ / ⚠️ under Download mean?**
The result of the last automated reachability probe of the download link — ✅ reachable, ⚠️ currently failing (the entry is kept so you can retry or use a mirror).

**A download fails or a link looks dead. What now?**
Check the [Source Health](https://iamsmmh.github.io/OmniSource/status/) page to see if the upstream is down, then [report a broken upstream](https://github.com/iamsmmh/OmniSource/issues/new?template=02-broken-upstream.yml). A daily automation also probes every link and files an issue on breakage.

**How do I remove the source?**
Delete OmniSource from your client's source list. Already-installed apps stay on your device — they just stop receiving updates from this feed.

**How do I request a new app?**
[Request an app](https://github.com/iamsmmh/OmniSource/issues/new?template=01-app-request.yml). It needs an official upstream (the developer's GitHub Releases or AltStore feed) so the pipeline can sync it automatically.

**Is this safe?**
The pipeline only ever downloads release *metadata* (never IPAs), every entry is labelled with its verification method and origin, and community-built IPAs are explicitly marked as such. Sideloading always requires trusting the app's own developer — this source just makes that transparent.

## 🗺️ Roadmap

- [x] Auto-generated discovery catalog, verification levels, health board and analytics
- [x] Static App-Store-style app pages + machine API
- [x] Trending, related, reputation, download intelligence, install cards, search, comparison
- [x] JavaScript + Python SDKs
- [x] Immersive design-system rebuild: home, compare, status, analytics, install, search
- [x] PWA (offline shell + feeds, install prompt, update toast, manifest shortcuts)
- [x] Sitemap, robots, WebP assets, minified CSS in the deploy bundle
- [ ] OmniSource mobile app consuming `/api/`
- [ ] Community app submissions (PRs to `catalog.json`)
- [ ] Ratings, reviews and request tracking in the web experience
- [ ] Signed release notifications

## 🧹 Cleanup report

The repository is kept lean on purpose: `feeds/` is the only home of generated feeds, the root tree carries just `/apps.json` (the installable source URL) plus the `api/` mirror, and the front end runs on one shared design system. Full inventory of removed files, bug fixes and the root-reorganization pass, with reasons and replacements: [docs/cleanup-report.md](docs/cleanup-report.md).

## ⚖️ Disclaimer

OmniSource is an independent community project. It aggregates third-party releases; some entries are community-built IPAs of open-source tweaks whose projects publish no IPA themselves. All apps, code and trademarks belong to their respective owners, and you are responsible for complying with applicable laws and terms of service.

## 📄 License

[GPL-3.0](LICENSE) © the OmniSource contributors.

<div align="center">

⭐ **Star this repo if OmniSource makes sideloading easier for you** ⭐

[🌐 Website](https://iamsmmh.github.io/OmniSource/) · [📲 Install center](https://iamsmmh.github.io/OmniSource/install/) · [🔌 API docs](docs/API.md) · [🤝 Contributing](CONTRIBUTING.md)

</div>
