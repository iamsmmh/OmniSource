<div align="center">

<img src="assets/OmniSource.png" width="150" alt="OmniSource logo">

# OmniSource

**The App Store for sideloaded iOS — one feed, five clients, always current.**

One source URL for **AltStore · SideStore · Feather · ESign · LiveContainer**, backed by a fast, dependency-free PWA: live catalog, app comparison, health dashboard, analytics, per-app feeds and an install center.

<p>
<img src="assets/AltStore.webp" alt="AltStore" width="28" height="28">
&nbsp;
<img src="assets/SideStore.webp" alt="SideStore" width="28" height="28">
&nbsp;
<img src="assets/Feather.webp" alt="Feather" width="28" height="28">
&nbsp;
<img src="assets/E-Sign.webp" alt="ESign" width="28" height="28">
&nbsp;
<img src="assets/LiveContainer.webp" alt="LiveContainer" width="28" height="28">
</p>

<!-- omnisource:stats:start -->

**77** apps · **61** upstream sources · **70** verified · **1** community verified · **71/77** downloads online · last sync **2026-09-10**.

<!-- omnisource:stats:end -->

<p>
  <a href="https://github.com/iamsmmh/OmniSource/actions/workflows/sync.yml"><img src="https://github.com/iamsmmh/OmniSource/actions/workflows/sync.yml/badge.svg" alt="Sync & Publish"></a>
  <a href="https://github.com/iamsmmh/OmniSource/actions/workflows/validate.yml"><img src="https://github.com/iamsmmh/OmniSource/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="https://img.shields.io/endpoint?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2Fbadge-apps.json"><img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2Fbadge-apps.json" alt="Apps"></a>
  <a href="https://img.shields.io/endpoint?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2Fbadge-health.json"><img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2Fbadge-health.json" alt="Downloads healthy"></a>
  <a href="https://iamsmmh.github.io/OmniSource/"><img src="https://img.shields.io/website?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2F&label=website" alt="Website"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/iamsmmh/OmniSource" alt="License"></a>
</p>

<p>
  <a href="#-add-the-source"><b>🚀 Add the source</b></a> ·
  <a href="https://iamsmmh.github.io/OmniSource/"><b>🌐 Website</b></a> ·
  <a href="#-app-catalog"><b>📚 Catalog</b></a> ·
  <a href="#%EF%B8%8F-how-it-works"><b>⚙️ How it works</b></a> ·
  <a href="#-machine-api"><b>🔌 API</b></a> ·
  <a href="#-faq"><b>❓ FAQ</b></a> ·
  <a href="CONTRIBUTING.md"><b>🤝 Contributing</b></a>
</p>

</div>

---

## ✨ Why OmniSource?

- 🎯 **Official upstreams only** — every release resolves from the developer's own GitHub Releases or AltStore feed. Community-built IPAs (e.g. tweaks that only ship `.deb`) are explicitly labelled **Community build**; everything else is an **Official build**.
- ✅ **Verified & health-checked** — verification labels, SHA-256 hashes and automated download probes keep the catalog installable.
- 🔄 **Fresh every 6 hours** — a scheduled pipeline syncs releases, rebuilds every feed and redeploys the site.
- 📲 **One feed, five clients** — one AltStore Source v2 URL works in AltStore, SideStore, Feather, ESign and LiveContainer, with one-tap deep links.
- 🌐 **A real website, not just JSON** — search, compare, collections, favorites, analytics and an offline-first PWA; no framework and no build step.

## 🚀 Add the source

The installable source URL:

```
https://iamsmmh.github.io/OmniSource/apps.json
```

On your iPhone, tap your client to add the source in one go:

| Client | One-tap add |
| --- | --- |
| **AltStore** | <a href="altstore://source?url=https://iamsmmh.github.io/OmniSource/apps.json">➕ Add to AltStore</a> |
| **SideStore** | <a href="sidestore://source?url=https://iamsmmh.github.io/OmniSource/apps.json">➕ Add to SideStore</a> |
| **Feather** | <a href="feather://source/iamsmmh.github.io/OmniSource/apps.json">➕ Add to Feather</a> |
| **ESign** | <a href="esign://addsource?url=https://iamsmmh.github.io/OmniSource/apps.json">➕ Add to ESign</a> |
| **LiveContainer** | <a href="livecontainer://sources?url=https://iamsmmh.github.io/OmniSource/apps.json">➕ Add to LiveContainer</a> |

If a tap does nothing (client not installed, or an older version), add the URL manually in the client's *Sources* screen — the [install center](https://iamsmmh.github.io/OmniSource/install/) has per-client, per-app steps, QR codes and deep links.

### Single-app feeds & bundle-ID collisions

Every app also publishes a standalone source at `feeds/<slug>.json` (and an RSS feed at `feeds/<slug>.xml`, combined in [`feeds/feed.xml`](https://iamsmmh.github.io/OmniSource/feeds/feed.xml)). Clients like SideStore identify apps by bundle identifier, so two apps sharing one ID (the YouTube tweak family, for example) replace each other on install. To keep them separate, add only the one you want via its single-app feed — each app page has a **Copy source link** button for exactly this.

## 🌐 Website

[**Home**](https://iamsmmh.github.io/OmniSource/) · [**Compare**](https://iamsmmh.github.io/OmniSource/compare/) (`?left=youpro&right=ytlite`) · [**Health**](https://iamsmmh.github.io/OmniSource/status/) · [**Analytics**](https://iamsmmh.github.io/OmniSource/analytics/) · [**Install center**](https://iamsmmh.github.io/OmniSource/install/) · [**Search**](https://iamsmmh.github.io/OmniSource/search/) (⌘K on every page) · [**Favorites**](https://iamsmmh.github.io/OmniSource/favorites/) · [**Collections**](https://iamsmmh.github.io/OmniSource/collections/) · app pages like [apps/ytlite/](https://iamsmmh.github.io/OmniSource/apps/ytlite/).

The site is an installable **PWA**: offline shell via service worker, cached feeds/pages, and a "new version available" reload prompt.

## 📚 App catalog

Auto-generated on every sync. Browse it more comfortably on the [website](https://iamsmmh.github.io/OmniSource/).

<details>
<summary><strong>📋 View all apps and source links</strong></summary>

<!-- omnisource:catalog:start -->

_Catalogue last changed 2026-09-10 · 77 apps · 71/77 downloads reachable._

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
| **iQFace** | `com.facebook.Facebook` | `577.1` | 2026-09-05 | 🟢 stable | ⚠️ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/iqface.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/iqface.json) | [`iqface.json`](https://iamsmmh.github.io/OmniSource/feeds/iqface.json) | [`iqface.xml`](https://iamsmmh.github.io/OmniSource/feeds/iqface.xml) |
| **RyukGram** | `com.burbn.instagram` | `445.0.0` | 2026-09-01 | 🟢 stable | ⚠️ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ryukgram.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ryukgram.json) | [`ryukgram.json`](https://iamsmmh.github.io/OmniSource/feeds/ryukgram.json) | [`ryukgram.xml`](https://iamsmmh.github.io/OmniSource/feeds/ryukgram.xml) |
| **Sparkle** | `com.burbn.instagram.sparkle` | `445.0.0` | 2026-09-01 | 🟢 stable | ⚠️ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/sparkle.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/sparkle.json) | [`sparkle.json`](https://iamsmmh.github.io/OmniSource/feeds/sparkle.json) | [`sparkle.xml`](https://iamsmmh.github.io/OmniSource/feeds/sparkle.xml) |
| **RedditFilter** | `com.atebits.Tweetie2` | `2025.37.0` | 2025-09-26 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/redditfilter.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/redditfilter.json) | [`redditfilter.json`](https://iamsmmh.github.io/OmniSource/feeds/redditfilter.json) | [`redditfilter.xml`](https://iamsmmh.github.io/OmniSource/feeds/redditfilter.xml) |
| **NexaSC** | `com.soundcloud.TouchApp` | `8.77.0` | 2026-09-07 | 🟡 beta | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/nexasc.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/nexasc.json) | [`nexasc.json`](https://iamsmmh.github.io/OmniSource/feeds/nexasc.json) | [`nexasc.xml`](https://iamsmmh.github.io/OmniSource/feeds/nexasc.xml) |
| **Messenger Flow** | `com.facebook.Messenger.flow` | `577.0.0` | 2026-09-03 | 🟢 stable | ⚠️ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/messenger-flow.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/messenger-flow.json) | [`messenger-flow.json`](https://iamsmmh.github.io/OmniSource/feeds/messenger-flow.json) | [`messenger-flow.xml`](https://iamsmmh.github.io/OmniSource/feeds/messenger-flow.xml) |
| **MSGPlusX** | `com.facebook.Messenger` | `577.0.0` | 2026-09-03 | 🟢 stable | ⚠️ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/msgplusx.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/msgplusx.json) | [`msgplusx.json`](https://iamsmmh.github.io/OmniSource/feeds/msgplusx.json) | [`msgplusx.xml`](https://iamsmmh.github.io/OmniSource/feeds/msgplusx.xml) |
| **ThreadSaver** | `com.burbn.barcelona` | `445.1` | 2026-09-01 | 🟢 stable | ⚠️ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/threadsaver.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/threadsaver.json) | [`threadsaver.json`](https://iamsmmh.github.io/OmniSource/feeds/threadsaver.json) | [`threadsaver.xml`](https://iamsmmh.github.io/OmniSource/feeds/threadsaver.xml) |
| **iMe MxGram** | `com.olcorporation.olai` | `12.8.1` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ime.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ime.json) | [`ime.json`](https://iamsmmh.github.io/OmniSource/feeds/ime.json) | [`ime.xml`](https://iamsmmh.github.io/OmniSource/feeds/ime.xml) |
| **Turrit MxGram** | `com.seastar.turrit` | `1.5.3` | 2026-09-01 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/turrit-mxgram.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/turrit-mxgram.json) | [`turrit-mxgram.json`](https://iamsmmh.github.io/OmniSource/feeds/turrit-mxgram.json) | [`turrit-mxgram.xml`](https://iamsmmh.github.io/OmniSource/feeds/turrit-mxgram.xml) |
| **RyukGram (IG 410)** | `com.burbn.instagram` | `410.1.0` | 2026-07-25 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ryukgram-ig410.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ryukgram-ig410.json) | [`ryukgram-ig410.json`](https://iamsmmh.github.io/OmniSource/feeds/ryukgram-ig410.json) | [`ryukgram-ig410.xml`](https://iamsmmh.github.io/OmniSource/feeds/ryukgram-ig410.xml) |
| **RyukGram Side by Side** | `com.ryuk.ryukgram` | `446.0.0` | 2026-09-09 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ryukgram-sidebyside.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/ryukgram-sidebyside.json) | [`ryukgram-sidebyside.json`](https://iamsmmh.github.io/OmniSource/feeds/ryukgram-sidebyside.json) | [`ryukgram-sidebyside.xml`](https://iamsmmh.github.io/OmniSource/feeds/ryukgram-sidebyside.xml) |
| **Dopamine** | `com.opa334.Dopamine` | `3.0.9` | 2026-08-22 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/dopamine.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/dopamine.json) | [`dopamine.json`](https://iamsmmh.github.io/OmniSource/feeds/dopamine.json) | [`dopamine.xml`](https://iamsmmh.github.io/OmniSource/feeds/dopamine.xml) |
| **Dopamine (RootHide)** | `com.opa334.Dopamine-roothide` | `2.4.9.26` | 2026-09-07 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/dopamine-roothide.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/dopamine-roothide.json) | [`dopamine-roothide.json`](https://iamsmmh.github.io/OmniSource/feeds/dopamine-roothide.json) | [`dopamine-roothide.xml`](https://iamsmmh.github.io/OmniSource/feeds/dopamine-roothide.xml) |
| **Bootstrap** | `com.roothide.Bootstrap` | `2.2.1` | 2026-06-12 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/bootstrap.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/bootstrap.json) | [`bootstrap.json`](https://iamsmmh.github.io/OmniSource/feeds/bootstrap.json) | [`bootstrap.xml`](https://iamsmmh.github.io/OmniSource/feeds/bootstrap.xml) |
| **Serotonin** | `pisshill.usprebooter` | `1.2.1` | 2024-01-17 | 🔴 unmaintained | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/serotonin.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/serotonin.json) | [`serotonin.json`](https://iamsmmh.github.io/OmniSource/feeds/serotonin.json) | [`serotonin.xml`](https://iamsmmh.github.io/OmniSource/feeds/serotonin.xml) |
| **Taurine** | `org.coolstar.taurine` | `1.1.7` | 2023-09-23 | 🔴 unmaintained | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/taurine.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/taurine.json) | [`taurine.json`](https://iamsmmh.github.io/OmniSource/feeds/taurine.json) | [`taurine.xml`](https://iamsmmh.github.io/OmniSource/feeds/taurine.xml) |
| **Odyssey** | `org.coolstar.odyssey` | `1.4.3` | 2023-04-04 | 🔴 unmaintained | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/odyssey.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/odyssey.json) | [`odyssey.json`](https://iamsmmh.github.io/OmniSource/feeds/odyssey.json) | [`odyssey.xml`](https://iamsmmh.github.io/OmniSource/feeds/odyssey.xml) |
| **unc0ver** | `science.xnu.undecimus` | `5.2.0` | 2020-06-09 | 🔴 unmaintained | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/unc0ver.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/unc0ver.json) | [`unc0ver.json`](https://iamsmmh.github.io/OmniSource/feeds/unc0ver.json) | [`unc0ver.xml`](https://iamsmmh.github.io/OmniSource/feeds/unc0ver.xml) |
| **SameBoy** | `com.github.liji32.sameboy.ios` | `1.0.3` | 2026-03-04 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/sameboy.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/sameboy.json) | [`sameboy.json`](https://iamsmmh.github.io/OmniSource/feeds/sameboy.json) | [`sameboy.xml`](https://iamsmmh.github.io/OmniSource/feeds/sameboy.xml) |
| **Gopeed** | `com.gopeed.gopeed` | `1.9.3` | 2026-03-18 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/gopeed.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/gopeed.json) | [`gopeed.json`](https://iamsmmh.github.io/OmniSource/feeds/gopeed.json) | [`gopeed.xml`](https://iamsmmh.github.io/OmniSource/feeds/gopeed.xml) |
| **Manic EMU** | `com.aoshuang.manicemu` | `2.0.0` | 2026-09-03 | 🟢 stable | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/manicemu.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/manicemu.json) | [`manicemu.json`](https://iamsmmh.github.io/OmniSource/feeds/manicemu.json) | [`manicemu.xml`](https://iamsmmh.github.io/OmniSource/feeds/manicemu.xml) |
| **XeniOS** | `com.xenios` | `2.0.1` | 2026-06-08 | 🟡 beta | ✅ | [AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/feeds/xenios.json) · [SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/feeds/xenios.json) | [`xenios.json`](https://iamsmmh.github.io/OmniSource/feeds/xenios.json) | [`xenios.xml`](https://iamsmmh.github.io/OmniSource/feeds/xenios.xml) |

<!-- omnisource:catalog:end -->

</details>

**Columns** — *Status*: 🟢 stable · 🟡 beta · 🔵 manually published · 🔴 unmaintained. *Download*: ✅ / ⚠️ is the last automated reachability probe. *Feed/RSS*: that app's standalone AltStore feed and RSS release feed.

## 🔍 Where the info comes from

`catalog.json` (the only hand-edited data file) declares each app's upstream and verification method; the published entry is generated from that upstream.

| Channel | What is official |
| --- | --- |
| **GitHub Releases of the app itself** | The release, IPA asset, date and notes come straight from the project's own GitHub release. |
| **Developer's own AltStore feed** | The developer's source (e.g. iKarwan's `repo.ikghd.me`); the last verified build is kept with a mirror fallback when unreachable. |
| **Community builds of official tweaks** | Tweaks such as the YouTube family publish `.deb` (or nothing); these IPAs are repackaged by named community builders and are clearly labelled **Community build**. |

Each feed entry embeds an `omnisource` metadata block (`status`, `verification`, `provenance`, `compatibility`) so clients and users can see exactly where a build came from.

## ⚙️ How it works

1. **Sync** — for every catalog app, resolve the newest release from its declared upstream (GitHub Releases or the developer's feed); download metadata only, never the IPA.
2. **Health** — HEAD-probe (ranged-GET fallback) every primary and fallback download URL.
3. **Build** — render per-app feeds, `apps.json`, RSS, badges, intelligence documents and one static page per app; refresh the marked blocks in this README.
4. **Validate** — an offline rule engine (`scripts/validate.py`), jq contract checks, `ruff` and the unit-test suite run on every push; `check_reproducible.py` proves an offline rebuild is byte-identical.
5. **Publish** — `/apps.json` and the `/api/` mirror refresh, and `scripts/build_site.py` assembles the `_site/` artifact deployed to GitHub Pages (every 6 h via `.github/workflows/sync.yml`).

```
catalog.json → scripts/omnisource.py (src/omnisource/, Python stdlib only)
            → feeds/ (JSON/XML) + apps/<slug>/ (pages) + api/
            → scripts/build_site.py → _site/ → GitHub Pages
```

Key paths: `catalog.json` source of truth · `src/omnisource/` pipeline · `scripts/` thin CLIs · `feeds/` generated output · `js/` + `assets/design-system/` the web front end · `sdk/` zero-dependency JS/Python clients · `docs/` guides ([REPOSITORY](docs/REPOSITORY.md), [API](docs/API.md), [cleanup report](docs/cleanup-report.md)).

```bash
make build      # sync + health + build
make serve      # serve _site/ locally at http://localhost:8000
make check      # ruff + validator + jq + unit tests
python3 scripts/omnisource.py --no-sync    # offline rebuild from feeds/state.json
```

The service worker is versioned (`omnisource-vN` in `sw.js`); bump it whenever the cached asset set changes.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: change **`catalog.json`**, never generated files; run `python3 scripts/omnisource.py` and commit the regenerated output. New apps need an official upstream (GitHub Releases or a developer feed). Issues: [request an app](https://github.com/iamsmmh/OmniSource/issues/new?template=01-app-request.yml) · [broken upstream](https://github.com/iamsmmh/OmniSource/issues/new?template=02-broken-upstream.yml) · [bug](https://github.com/iamsmmh/OmniSource/issues/new?template=03-bug-report.yml) · [feature idea](https://github.com/iamsmmh/OmniSource/issues/new?template=04-feature-idea.yml).

## 🔌 Machine API

Every build publishes a generated API under `/api/` ([docs/API.md](docs/API.md)): `apps.json`, `catalog.json`, `sources.json`, `verification.json`, `status.json`, `duplicates.json`, `analytics.json`, `updates.json`, `health.json`, `install.json`, `trending.json`, `related.json`, `reputation.json`, `download-intelligence.json`, `community.json`, `search-index.json`, `compare.json` and more — each with a `.gz` twin and an `api/index.json` listing. Zero-dependency client libraries live in [`sdk/javascript/`](sdk/javascript/) and [`sdk/python/`](sdk/python/).

## ❓ FAQ

**Can I install two YouTube apps side by side?**
No — apps sharing a `bundleIdentifier` replace each other on install. Pick one (the [compare page](https://iamsmmh.github.io/OmniSource/compare/) helps), or add a single-app feed (`feeds/<slug>.json`) so only the app you want is visible; the site flags every collision and gives you a copyable source link.

**How do updates work?**
Refresh sources in your client; upstreams are synced every 6 hours. For notifications, subscribe to `feeds/<slug>.xml` or the combined `feeds/feed.xml`.

**What do the statuses and badges mean?**
🟢 stable · 🟡 beta · 🔵 manually published (no live upstream) · 🔴 unmaintained. **Official build** = published by the project's own upstream; **Community build** = repackaged/mirrored by a named community builder. ✅ / ⚠️ = last download-link health probe.

**Is this safe?**
The pipeline downloads release *metadata* only, never IPAs; every entry discloses its verification method, hash and origin. Sideloading always means trusting the app's own developer — OmniSource just makes that transparent.

**A download fails — what now?**
Check [Source Health](https://iamsmmh.github.io/OmniSource/status/), then [report a broken upstream](https://github.com/iamsmmh/OmniSource/issues/new?template=02-broken-upstream.yml) (a daily automation files issues automatically too).

## ⚖️ Disclaimer

Independent community project. It aggregates third-party releases; some entries are community-built IPAs of open-source tweaks. All apps, code and trademarks belong to their respective owners. [GPL-3.0](LICENSE) © the OmniSource contributors.

<div align="center">

⭐ **Star this repo if OmniSource makes sideloading easier for you** ⭐

[🌐 Website](https://iamsmmh.github.io/OmniSource/) · [📲 Install center](https://iamsmmh.github.io/OmniSource/install/) · [🔌 API docs](docs/API.md) · [🤝 Contributing](CONTRIBUTING.md)

</div>
