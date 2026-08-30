<div align="center">

<img src="assets/YouTube.png" width="110" alt="OmniSource">

# 🌐 OmniSource

### Automated iOS Sideloading Feed Repository

[![Build Status](https://img.shields.io/github/actions/workflow/status/iamsmmh/OmniSource/update.yml?style=flat-square&logo=github-actions&logoColor=white)](https://github.com/iamsmmh/OmniSource/actions)
[![License](https://img.shields.io/github/license/iamsmmh/OmniSource?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/iamsmmh/OmniSource?style=flat-square&color=FFD700)](https://github.com/iamsmmh/OmniSource/stargazers)
[![Issues](https://img.shields.io/github/issues/iamsmmh/OmniSource?style=flat-square&color=FF6B6B)](https://github.com/iamsmmh/OmniSource/issues)

**Unified • Automated • Organized**

A centralized collection of iOS application feeds and manifests, automatically maintained through GitHub Actions and distributed through AltStore-compatible sources.

</div>

---

## ⚡ Quick Add

### 🌐 OmniSource Master Feed

The master feed contains the complete OmniSource application collection.

**AltStore**

<a href="altstore://source?url=https%3A%2F%2Fraw.githubusercontent.com%2Fiamsmmh%2FOmniSource%2Fmain%2Fapps.json">
<img src="https://img.shields.io/badge/Add%20to-AltStore-00D084?style=for-the-badge" alt="Add to AltStore">
</a>

**SideStore**

<a href="sidestore://source?url=https%3A%2F%2Fraw.githubusercontent.com%2Fiamsmmh%2FOmniSource%2Fmain%2Fapps.json">
<img src="https://img.shields.io/badge/Add%20to-SideStore-5B50F6?style=for-the-badge" alt="Add to SideStore">
</a>

### 📋 Master Source URL

```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json
```

> **Manual fallback:** If a one-tap button does not open the installed client, copy the Master Source URL and add it manually through the client's Sources/Repositories section.

---

## ✨ Features

- ⚡ Automated feed maintenance
- 🔄 Scheduled upstream release tracking
- 📦 Master source aggregation
- 📄 Standalone application feeds
- 🧩 AltStore-compatible JSON manifests
- 📱 AltStore and SideStore support
- 🌐 GitHub-hosted source distribution
- 🔍 Automated processing and validation
- 🛠️ GitHub Actions workflow automation
- 🔗 Direct raw feed access
- 👨‍💻 Full upstream developer attribution

---

## 📱 Supported Clients

| Client | Source Support | Import Method |
|:--|:--:|:--|
| 🟢 AltStore | ✅ | One-tap / Manual |
| 🟣 SideStore | ✅ | One-tap / Manual |
| 🪶 Feather | ✅ | Manual Source URL |
| 📦 LiveContainer | ✅ | Manual Source URL |
| 🛠️ ESign | ✅ | Manual Source URL |
| ✍️ Signulous | ✅ | Manual Source URL |

> **Compatibility:** OmniSource feeds use the AltStore source/manifest format. Client support ultimately depends on the installed client's source/repository implementation.

---

## 📦 Available Sources

| Application | Developer(s) | Description | Feed |
|:--|:--|:--|:--|
| 🌐 **OmniSource Master** | iamsmmh | Complete consolidated source | [`apps.json`](apps.json) |
| 🎧 **SpotiFLAC Mobile** | spotiflacapp | Lossless FLAC downloader & player | [`spotiflac.json`](spotiflac.json) |
| ▶️ **uYouEnhanced** | arichornlover & MiRO92 | uYou continuation with modern fixes and SponsorBlock | Included in master feed |
| ▶️ **YTKACE** | itzzace & mrdrvt99 | YouTube enhancer with downloads and SponsorBlock | [`ytkace.json`](ytkace.json) |
| ▶️ **YouPro** | Alibusut & mrdrvt99 | YouTube mod with premium features and downloader | [`youpro.json`](youpro.json) |
| ▶️ **YTLite** | Dayanch96 & mrdrvt99 | Lightweight and customizable YouTube mod | [`ytlite.json`](ytlite.json) |
| ▶️ **YTKillerPlus** | IKillerApp & mrdrvt99 | YouTube downloader and tweak suite | [`ytkp.json`](ytkp.json) |
| ▶️ **YouMod** | mrdrvt99 | YouTube modification with playback and interface enhancements | [`youmod.json`](youmod.json) |
| 🎵 **YTMusicUltimate** | Dayanch96 & mrdrvt99 | YouTube Music enhancement with background playback and ad blocking | [`ytmusic.json`](ytmusic.json) |

> **Note:** `uYouEnhanced` is currently included in `apps.json`, but there is no standalone `uyouenhanced.json` file in the repository.

---

## 🔗 Direct Feed URLs

### 🌐 Master

```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json
```

### 🎧 SpotiFLAC Mobile

```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/spotiflac.json
```

### ▶️ YTKACE

```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytkace.json
```

### ▶️ YouPro

```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/youpro.json
```

### ▶️ YTLite

```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytlite.json
```

### ▶️ YTKillerPlus

```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytkp.json
```

### ▶️ YouMod

```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/youmod.json
```

### 🎵 YTMusicUltimate

```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytmusic.json
```

---

## 📲 Installation Guide

### Automatic

**AltStore / SideStore**

1. Open this README on your iOS device.
2. Tap the corresponding **Add to** button above.
3. Allow the installed client to open.
4. Confirm the source import.
5. Refresh the source.

### Manual

For Feather, LiveContainer, ESign, Signulous, or when automatic import is unavailable:

1. Copy a feed URL from above.
2. Open the client's **Sources / Repositories** section.
3. Tap **+ / Add Source**.
4. Paste the URL.
5. Save and refresh.

> **Recommended:** Use the **Master Feed** if you want all applications from one source.

---

## 🧩 Feed Architecture

```text
                    ┌─────────────────────┐
                    │   Upstream Sources  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   GitHub Actions    │
                    │  Update / Validate  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   JSON Manifests    │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
             Master Feed           Standalone Feeds
              apps.json             *.json
                    │                     │
                    └──────────┬──────────┘
                               ▼
                 AltStore-Compatible Clients
```

---

## ⚙️ GitHub Actions

OmniSource uses GitHub Actions to automate feed maintenance.

### Current Workflows

| Workflow | Purpose |
|:--|:--|
| [`update.yml`](.github/workflows/update.yml) | Automated feed/update workflow |
| [`updatex.yml`](.github/workflows/updatex.yml) | Additional update automation |
| [`lint-action.yml`](.github/workflows/lint-action.yml) | Workflow validation/linting |
| [`delete-old-workflows-run.yml`](.github/workflows/delete-old-workflows-run.yml) | Workflow-run cleanup |

### Automation

```text
Upstream Releases
       ↓
GitHub Actions
       ↓
Process / Update
       ↓
Manifest Generation
       ↓
Feed Validation
       ↓
OmniSource JSON Feeds
```

---

## 🔐 Bundle Identifiers

YouTube variants in the current master manifest use separate bundle identifiers, allowing supported variants to coexist without relying on a single shared YouTube bundle ID.

| Application | Bundle Identifier |
|:--|:--|
| uYouEnhanced | `com.google.ios.youtube.uyouenhanced` |
| YTKACE | `com.google.ios.youtube.ytkace` |
| YouPro | `com.google.ios.youtube.youpro` |
| YTLite | `com.google.ios.youtube.ytlite` |
| YTKillerPlus | `com.google.ios.youtube.ytkp` |
| YTMusicUltimate | `com.google.ios.youtubemusic` |

> **Important:** Even with separate bundle identifiers, installation behavior can vary depending on the sideloading client, signing method, entitlements, and application configuration.

---

## 📊 Current Feed Overview

| Category | Count |
|:--|--:|
| Master Feed | 1 |
| Standalone Feeds | 7 |
| Applications in Master | 8 |
| Supported Clients | 6 |
| Automation Workflows | 4 |

---

## 📂 Repository Resources

- 🏠 [OmniSource Repository](https://github.com/iamsmmh/OmniSource)
- 📦 [Master Feed](apps.json)
- 📁 [All Repository Files](https://github.com/iamsmmh/OmniSource/tree/main)
- ⚙️ [GitHub Actions](https://github.com/iamsmmh/OmniSource/actions)
- 🚀 [Releases](https://github.com/iamsmmh/OmniSource/releases)
- 🐛 [Issues](https://github.com/iamsmmh/OmniSource/issues)
- 📜 [License](LICENSE)
- ⭐ [Star Repository](https://github.com/iamsmmh/OmniSource/stargazers)

---

## 🙌 Credits & Attribution

OmniSource is a distribution and feed-management project. Application development, source code, tweaks, and upstream releases remain the work of their respective developers.

### Upstream Developers

- 🎧 **SpotiFLAC Mobile** — [spotiflacapp](https://github.com/spotiflacapp)
- ▶️ **uYouEnhanced** — [arichornlover](https://github.com/arichornlover) & [MiRO92](https://github.com/MiRO92)
- ▶️ **YTKACE** — [itzzace](https://github.com/itzzace) & [mrdrvt99](https://github.com/mrdrvt99)
- ▶️ **YouPro** — [Alibusut](https://github.com/Alibusut) & [mrdrvt99](https://github.com/mrdrvt99)
- ▶️ **YTLite** — [Dayanch96](https://github.com/Dayanch96) & [mrdrvt99](https://github.com/mrdrvt99)
- ▶️ **YTKillerPlus** — [IKillerApp](https://github.com/IKillerApp) & [mrdrvt99](https://github.com/mrdrvt99)
- ▶️ **YouMod** — [mrdrvt99](https://github.com/mrdrvt99)
- 🎵 **YTMusicUltimate** — [Dayanch96](https://github.com/Dayanch96) & [mrdrvt99](https://github.com/mrdrvt99)

### Repository Credits

- ⚙️ **S M Mahbub Hossain** — OmniSource development, feed infrastructure, and automation.
- 🐧 **MountainofPenguin** — Repository architecture and structure inspiration.
- 🛡️ **HakujouSan** — Testing, feedback, and community insights.
- 🛠️ **Avieshek** — Manifest parsing, debugging, and JSON assistance.

---

## ⚖️ Disclaimer

OmniSource is an independent community project.

All third-party application names, logos, trademarks, source code, modifications, and copyrighted materials belong to their respective owners.

OmniSource acts as a feed/indexing and distribution layer and does not claim ownership of third-party applications or upstream projects.

Application availability, signing, installation, entitlements, and compatibility may change without notice.

Users are responsible for complying with applicable laws, software licenses, and the terms of the applications and services they use.

---

<div align="center">

## 🌐 OmniSource

**Automated • Organized • Unified**

[⭐ Star Repository](https://github.com/iamsmmh/OmniSource)

</div>
