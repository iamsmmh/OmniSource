<div align="center">

<img src="assets/OmniSource.png" width="140" alt="OmniSource logo">

# OmniSource

### The App Store for sideloaded iOS.

One AltStore-compatible feed for **AltStore · SideStore · Feather · ESign · LiveContainer** — wrapped in a full web experience with live catalog, comparison, source health, analytics, an install center, and an offline-first PWA.

<!-- omnisource:stats:start -->

**22** apps · **18** upstream sources · **21** verified · **1** community verified · **22/22** downloads online · last sync **2026-09-09**.

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
  <a href="#-get-started-in-60-seconds"><b>🚀 Get started</b></a> ·
  <a href="https://iamsmmh.github.io/OmniSource/"><b>🌐 Website</b></a> ·
  <a href="#-app-catalog"><b>📚 Catalog</b></a> ·
  <a href="#-frequently-asked-questions"><b>❓ FAQ</b></a> ·
  <a href="#-machine-api"><b>🔌 API</b></a> ·
  <a href="CONTRIBUTING.md"><b>🤝 Contributing</b></a>
</p>

</div>

---

## ✨ Why OmniSource?

- 🎯 **Official upstreams only** — every release resolves from the developer's own GitHub Releases or the developer's own AltStore feed. No random re-uploads, ever.
- ✅ **Verified & health-checked** — each app carries a verification label, and every download link is automatically probed so the catalog stays installable.
- 🔄 **Fresh every 6 hours** — a scheduled pipeline syncs new releases, rebuilds every feed, and redeploys the site around the clock.
- 📲 **One feed, five clients** — a single AltStore Source v2 URL works in AltStore, SideStore, Feather, ESign, and LiveContainer.
- 🌐 **A real website, not just JSON** — browse, search, compare, and install from a fast dependency-free PWA with health dashboards and analytics.
- 🔔 **Never miss a release** — per-app RSS feeds, a combined release feed, and a machine-readable "What's new" timeline.

## 🚀 Get started in 60 seconds

### Step 1 — Copy the source URL

```
https://iamsmmh.github.io/OmniSource/apps.json
```

### Step 2 — Add it to your client

On your iPhone, open this page and tap your client — the source adds itself:

| Client | One-tap add |
| --- | --- |
| **AltStore** | <a href="altstore://source?url=https://iamsmmh.github.io/OmniSource/apps.json">➕ Add to AltStore</a> |
| **SideStore** | <a href="sidestore://source?url=https://iamsmmh.github.io/OmniSource/apps.json">➕ Add to SideStore</a> |
| **Feather** | <a href="feather://source/iamsmmh.github.io/OmniSource/apps.json">➕ Add to Feather</a> |
| **ESign** | Paste the URL manually (ESign exposes no one-tap protocol) — see the [install center](https://iamsmmh.github.io/OmniSource/install/) |
| **LiveContainer** | Paste the URL manually (LiveContainer exposes no one-tap protocol) — see the [install center](https://iamsmmh.github.io/OmniSource/install/) |

> 💡 **Prefer manual setup?** Every client has an *Add Source* screen that accepts the URL above. The [install center](https://iamsmmh.github.io/OmniSource/install/) shows per-client, per-app instructions with auto-generated deep links.

### Step 3 — Browse & install

Open the **OmniSource** source inside your client, pick an app, and install. New versions flow in automatically on every refresh — nothing else to configure.

### Power-user feeds

Each app also publishes its own standalone feed at `https://iamsmmh.github.io/OmniSource/<slug>.json` (subscribe to a single app instead of the whole catalog), a per-app RSS release feed at `https://iamsmmh.github.io/OmniSource/<slug>.xml`, and everything is combined into `feed.xml` / `rss.xml`. A machine-readable "What's new" timeline lives at `updates.json`.

## 🌐 Website

The live site is an immersive, dependency-free web app (HTML5 + modern CSS + vanilla JS, no build step) served by GitHub Pages:

| Page | What it does |
| --- | --- |
| [🏠 Home](https://iamsmmh.github.io/OmniSource/) | Hero, trending / recent / featured / verified rails, statistics, source health, install guide, full catalog with search + filters, release timeline |
| [⚖️ Compare](https://iamsmmh.github.io/OmniSource/compare/) | App-vs-app comparison (bundle, category, developer, size, verification…) — deep-linkable: `compare/?left=youpro&right=ytlite` |
| [💚 Source Health](https://iamsmmh.github.io/OmniSource/status/) | Uptime, latency, availability and sync state for every upstream source |
| [📊 Analytics](https://iamsmmh.github.io/OmniSource/analytics/) | App/source counts, weekly updates, verification mix, category distribution, health trends — all charted from generated JSON, no backend |
| [📲 Install center](https://iamsmmh.github.io/OmniSource/install/) | Step-by-step instructions and auto-generated deep links for AltStore, SideStore, Feather, ESign and LiveContainer, per app and for the master feed |
| [🔎 Search](https://iamsmmh.github.io/OmniSource/search/) | Full-text search over name, bundle, developer, source, category and tags — plus a ⌘K command palette on every page |
| [⭐ Favorites](https://iamsmmh.github.io/OmniSource/favorites/) | Keep a personal list of saved apps |
| [🗂️ Collections](https://iamsmmh.github.io/OmniSource/collections/) | Curated and custom app collections you can build, import, and export as JSON |
| [📄 App pages](https://iamsmmh.github.io/OmniSource/apps/ytlite/) | Every app has a static detail page (`apps/<slug>/`) with versions, screenshots, related apps, and install actions |

The site is a **PWA**: installable (manifest + shortcuts), offline-first (service worker precaches the shell and caches every feed and app page), with a "new version available" reload prompt.

## 📚 App catalog

The complete generated catalog is below — it refreshes automatically on every sync. For a cleaner browsing experience, use the [OmniSource website](https://iamsmmh.github.io/OmniSource/).

<details>
<summary><strong>📋 View all apps and source links</strong></summary>

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

## 🔍 Where the info comes from

Every app in `catalog.json` declares its upstream and verification method, and the published entry is generated from that upstream — the catalog is never the source of versions, dates or download URLs.

| Channel | Apps | What is official |
| --- | --- | --- |
| **GitHub Releases of the app itself** | Aidoku, BHTwitter, Feather, iTorrent, LiveContainer, Provenance, SideStore, SpotiFLAC, StikDebug, UTM, Winston, YTKACE, MaxMusic | The release, its IPA asset, date and notes come straight from the project's own GitHub release. |
| **Developer's own AltStore feed** | YTKillerPlus, iNKillerPlus, TTKillerPlus | iKarwan's source (`repo.ikghd.me`). When unreachable, the last verified build is kept and a mirror fallback is offered. |
| **Ready-to-sideload builds of official tweaks** | uYouEnhanced, YouTubePlus, YouPro, YouMod, YTMusicUltimate, MaxTube | The underlying tweak's project is the official source of record; because those projects publish `.deb` (or nothing), this source serves **community-built IPAs** of the official tweak, clearly labelled in each entry's metadata. |

Each feed entry embeds an `omnisource` metadata block with `status`, `verification` and `compatibility` (including these source notes), so clients and users can see exactly where a build came from.

## ❓ Frequently asked questions

**How do app updates work?**
The pipeline checks every upstream every 6 hours. Just refresh sources in your client and new versions appear like any other update. Prefer push-style awareness? Subscribe to an app's RSS feed (`<slug>.xml`) or the combined `feed.xml`.

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

## Architecture

```
catalog.json (hand-edited source of truth)
      │
      ▼
scripts/omnisource.py ──▶ src/omnisource/ (Python, stdlib-only)
      │                       ├─ providers/   GitHub Releases + external-feed adapters
      │                       ├─ feeds/       AltStore v2, RSS, updates-timeline renderers
      │                       ├─ validation   offline rule engine (catalog, feeds, docs, pages)
      │                       ├─ intelligence trending · related · reputation · download-intel
      │                       │                community · search-index · compare · screenshots
      │                       ├─ install      per-client deep-link cards
      │                       ├─ app_pages    App-Store-style static pages (apps/<slug>/)
      │                       └─ site         _site/ builder (sitemap, robots, API mirror, minify)
      ▼
feeds/  (canonical JSON/XML)   apps/<slug>/  (pages)
      │                              │
      └──────────────┬───────────────┘
                     ▼
        scripts/build_site.py  ──▶  _site/  (the deployable site)
                     │
                     ▼
        GitHub Pages  ──▶  hand-maintained pages (7) + design system + sw.js (PWA)
```

* **Data plane** — `catalog.json` is the only hand-edited data file. The pipeline syncs official upstreams, probes every download link and regenerates all feeds, intelligence documents, badges and app pages. Generated files are never hand-edited.
* **Site plane** — hand-maintained page sources at the repository root (`index.html`, `install/`, `js/`, `sw.js`, …) plus the generated feeds and app pages. `scripts/build_site.py` (over `src/omnisource/site.py`) assembles `_site/` from that state: shared `assets/` (WebP icons, the design system), every feed at three URL families (flat root, `/feeds/`, `/api/` with gzip twins), the static app pages, `sitemap.xml`, `robots.txt` and the home page's live statistics. Nothing generated is committed at the root. GitHub Pages deploys the `_site/` artifact via `sync.yml` (GitHub Actions deployment), so there is a single publisher and plain pushes can never serve a half-built site.
* **Presentation plane** — HTML5 + modern CSS + vanilla JS with Web Components. No framework, no build step, no dependencies: GitHub Pages serves it as-is. A single design system (`assets/design-system/`) styles the website and the generated app pages alike; shared logic lives in `js/core.js` (theme, ⌘K palette, search engine, PWA) and `js/site.js` (page renderers).

## Generation flow

1. **Sync** — for every catalog app, resolve the newest release from its declared upstream (GitHub Releases or the developer's AltStore feed), download metadata only (never the IPA), and store versions, sizes, hashes and dates in `feeds/state.json`.
2. **Health** — HEAD-probe (ranged-GET fallback) every primary + fallback download URL; record reachability, latency and staleness.
3. **Build** — render per-app AltStore feeds, `apps.json`, RSS, `updates.json`, badges, all intelligence documents and one static page per app; refresh the marked stats/catalog blocks in this README.
4. **Validate** — the offline rule engine (`scripts/validate.py`) plus jq contract checks run on every push; `check_reproducible.py` proves an offline rebuild produces byte-identical output (date values normalized).
5. **Deploy** — `scripts/build_site.py` assembles `_site/` and `actions/deploy-pages@v4` publishes it. Existing subscriptions keep working at the historical flat URLs.

| Pipeline | Runs | What it does |
| --- | --- | --- |
| **Sync & Publish** (`.github/workflows/sync.yml`) | every 6 h · on push | Sync → health → build → assemble `_site/` → deploy Pages |
| **Validate** (`.github/workflows/validate.yml`) | every push & PR | Offline structural checks, reproducibility, `ruff`, `actionlint` |
| **Merge** (`.github/workflows/merge.yml`) | on `feeds/*.json` change | Rebuild the unified `feeds/apps.json` from the modular feeds |
| **Health Check** (`.github/workflows/health-check.yml`) | daily | Probe every download URL; open a GitHub Issue on breakage |

## Directory structure

| Path | Purpose |
| --- | --- |
| `catalog.json` | Source of truth: apps, official upstreams, verification and compatibility metadata |
| `config/` | Runtime defaults for sync, retries, health checks and history |
| `assets/` | App/client icons (PNG + WebP) and the shared design system |
| `src/omnisource/` | The Python package: providers, feed renderers, validation, intelligence engines, app pages, site builder |
| `scripts/` | Thin CLI entry points over the package (one command, one module) |
| `schemas/` | Catalog and AltStore feed contracts |
| `tests/` | Offline unit test suite (124 tests) |
| `feeds/` | Generated feeds, RSS, badges, health data, intelligence documents, pipeline state |
| `apps/<slug>/` | Generated App-Store-style app pages |
| `index.html`, `install/`, `js/`, `sw.js`, … (root) | The website sources: 7 hand-maintained pages + design system, assembled into `_site/` at deploy time (see `docs/website.md`) |
| `sdk/` | Zero-dependency client SDKs (JavaScript + Python) |
| `docs/` | Repository guide, API contracts, audit, and the [cleanup report](docs/cleanup-report.md) |

See the [repository guide](docs/REPOSITORY.md) for the detailed map and data-flow diagram.

## Deployment guide

Deployment is fully automated — push to `main` and GitHub Pages updates:

1. `sync.yml` runs the pipeline (sync, health, build) with GitHub Actions caching and concurrency limits; it commits the regenerated feeds/pages back via a bot push (allowlisted: `*.json`, `*.xml`, `apps/**`, `README.md`).
2. It assembles the site with `python3 scripts/build_site.py` and uploads `_site/` with `actions/upload-pages-artifact@v3`.
3. A separate `deploy` job publishes it with `actions/deploy-pages@v4` (environment: `github-pages`).
4. `validate.yml` guards every push and PR; the daily `health-check.yml` file breakage issues.

Local development mirrors production exactly:

```bash
make build      # sync + health + build (python3 scripts/omnisource.py)
make site       # assemble _site/
make serve      # serve _site/ on http://localhost:8000
make check      # ruff + validator + jq checks + unit tests
```

The service worker is versioned (`omnisource-vN`): bump the version in `sw.js` whenever the cached asset set changes, and the update toast in `js/core.js` offers the reload.

## Contributing

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

Golden rule: change `catalog.json`, never the generated files. Scripts are Python stdlib only — no virtualenv, no dependencies. Web changes are plain files at the repository root (pages, `js/`, `sw.js`) and in `assets/design-system/` — no build step, preview with `make serve`.

**Adding an app**

1. Add an entry to `catalog.json`: `slug`, identity, `icon` (add a PNG under `assets/` and a WebP twin), `verification` (source method + publisher), `compatibility`, and an `upstream` block pointing at the **official** source (`repo` + matching `assetSuffixes` for GitHub releases, or `feedURL` for a developer AltStore feed; `manualRelease` only when no live upstream exists).
2. Run `python3 scripts/omnisource.py` and commit the regenerated feeds, app page and README blocks.

Useful optional `upstream` knobs:

- `keepVersions` — how many releases the feed keeps per app (default `1`; `0` keeps every matching release). Keeping a few versions lets users roll back after a bad release.
- `includePrereleases` — opt an app into pre-release/beta builds when its upstream publishes them.
- `versionPattern` / `assetNamePattern` / `tagPrefix` — narrow which releases and assets are used when upstream tags differ from app versions.
- `minOSVersion` / `minOSVersionByTagNumber` — record the minimum iOS each build needs so the website can filter by device compatibility.

Remember that sideloading clients replace an installed app whose `bundleIdentifier` matches, so two catalog entries must not share a bundle ID unless that replacement behaviour is intended (the validator and website both surface these conflicts).

## 🔌 Machine API

Every build publishes a generated API under `/api/` on the site (see [docs/API.md](docs/API.md)): `apps.json`, `catalog.json` (discovery index), `sources.json`, `verification.json`, `status.json`, `duplicates.json`, `analytics.json`, `updates.json`, `health.json`, plus the discovery layer: `trending.json`, `related.json`, `reputation.json`, `download-intelligence.json`, `community.json`, `install.json`, `search-index.json`, `compare.json` and `screenshots.json`. Each JSON document is also published as a gzip twin and mirrored in `api/index.json`. The website consumes the same documents; zero-dependency client libraries live in [`sdk/javascript/`](sdk/javascript/) and [`sdk/python/`](sdk/python/).

## Discovery features

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

## Roadmap

- [x] Auto-generated discovery catalog, verification levels, health board and analytics
- [x] Static App-Store-style app pages + machine API
- [x] Trending, related, reputation, download intelligence, install cards, search, comparison
- [x] JavaScript + Python SDKs
- [x] Immersive design-system rebuild: home, compare, status, analytics, install, search
- [x] PWA v3 (offline shell + feeds, install prompt, update toast, manifest shortcuts)
- [x] Sitemap, robots, WebP assets, minified CSS in the deploy bundle
- [ ] OmniSource mobile app consuming `/api/`
- [ ] Community app submissions (PRs to `catalog.json`)
- [ ] Ratings, reviews and request tracking in the web experience
- [ ] Signed release notifications

## Cleanup report

The 2026-09 modernization pass removed dead and duplicate files and consolidated the generator surface — 24 files removed (18-file `api/` duplicate tree, 3 disjoint stylesheets, 2 legacy page scripts, a redundant page-regeneration script) and the front end rebuilt on a single design system. Full inventory with reasons and replacements: [docs/cleanup-report.md](docs/cleanup-report.md).

## Disclaimer

OmniSource is an independent community project. It aggregates third-party releases; some entries are community-built IPAs of open-source tweaks whose projects publish no IPA themselves. All apps, code and trademarks belong to their respective owners, and you are responsible for complying with applicable laws and terms of service.

## License

[GPL-3.0](LICENSE) © the OmniSource contributors.

<div align="center">

⭐ **Star this repo if OmniSource makes sideloading easier for you** ⭐

[🌐 Website](https://iamsmmh.github.io/OmniSource/) · [📲 Install center](https://iamsmmh.github.io/OmniSource/install/) · [🔌 API docs](docs/API.md) · [🤝 Contributing](CONTRIBUTING.md)

</div>
