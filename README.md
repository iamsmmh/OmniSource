<div align="center">

<a href="https://github.com/iamsmmh/OmniSource">
  <img src="assets/OmniSource.png" width="130" alt="OmniSource Logo">
</a>

# 🌐 OmniSource

**Automated iOS Sideloading Feed Repository**

[![Build Status](https://img.shields.io/github/actions/workflow/status/iamsmmh/OmniSource/main.yml?style=flat-square&logo=github-actions&logoColor=white)](https://github.com/iamsmmh/OmniSource/actions)
[![License](https://img.shields.io/github/license/iamsmmh/OmniSource?style=flat-square)](https://github.com/iamsmmh/OmniSource/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/iamsmmh/OmniSource?style=flat-square&color=FFD700)](https://github.com/iamsmmh/OmniSource/stargazers)
[![Issues](https://img.shields.io/github/issues/iamsmmh/OmniSource?style=flat-square&color=FF6B6B)](https://github.com/iamsmmh/OmniSource/issues)

A centralized, automated collection of application feeds and manifests maintained via GitHub Actions.

</div>

---

## 🚀 Feeds & Installation

Tap **Add to AltStore** on iOS to import automatically, or copy any raw feed URL below into your preferred sideloading client.

| App | Platform | Add Source | Manifest |
|------|:--------:|:----------:|----------|
| <img src="assets/OmniSource.png" width="22"> **OmniSource Master** | All-in-One | [Add to AltStore](https://altstore.io/source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json) | [apps.json](https://github.com/iamsmmh/OmniSource/blob/main/apps.json) |
| <img src="assets/SpotiFLAC.png" width="22"> **SpotiFLAC Mobile** | iOS | [Add to AltStore](https://altstore.io/source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/spotiflac.json) | [spotiflac.json](https://github.com/iamsmmh/OmniSource/blob/main/spotiflac.json) |
| <img src="assets/YouTube.png" width="22"> **YTLite** | iOS | [Add to AltStore](https://altstore.io/source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytlite.json) | [ytlite.json](https://github.com/iamsmmh/OmniSource/blob/main/ytlite.json) |
| <img src="assets/YouTube.png" width="22"> **YTKillerPlus** | iOS | [Add to AltStore](https://altstore.io/source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytkp.json) | [ytkp.json](https://github.com/iamsmmh/OmniSource/blob/main/ytkp.json) |
| <img src="assets/YouTube.png" width="22"> **YouPro** | iOS | [Add to AltStore](https://altstore.io/source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/youpro.json) | [youpro.json](https://github.com/iamsmmh/OmniSource/blob/main/youpro.json) |
| <img src="assets/YouTube.png" width="22"> **YouMod** | iOS | [Add to AltStore](https://altstore.io/source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/youmod.json) | [youmod.json](https://github.com/iamsmmh/OmniSource/blob/main/youmod.json) |
| <img src="assets/YouTube.png" width="22"> **YTKACE** | iOS | [Add to AltStore](https://altstore.io/source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytkace.json) | [ytkace.json](https://github.com/iamsmmh/OmniSource/blob/main/ytkace.json) |
| <img src="assets/YouTubeMusic.png" width="22"> **YTMusicUltimate** | iOS | [Add to AltStore](https://altstore.io/source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytmusic.json) | [ytmusic.json](https://github.com/iamsmmh/OmniSource/blob/main/ytmusic.json) |

---

## 📋 Direct Copyable Raw Feed URLs

### 🌐 OmniSource Master Feed
```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json
```

### 🎧 SpotiFLAC Mobile
```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/spotiflac.json
```

### ▶️ YTLite
```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytlite.json
```

### ▶️ YTKillerPlus
```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytkp.json
```

### ▶️ YouPro
```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/youpro.json
```

### ▶️ YouMod
```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/youmod.json
```

### ▶️ YTKACE
```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytkace.json
```

### 🎵 YTMusicUltimate
```text
https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytmusic.json
```

---

## 📥 Setup Instructions

### AltStore
1. Tap **Add to AltStore** from the table above.
2. AltStore will open automatically and import the source.

### SideStore / Feather / ESign / LiveContainer / Signulous
1. Copy any feed URL above.
2. Open your sideloading application.
3. Navigate to **Sources / Repositories**.
4. Tap **+ Add Source**.
5. Paste the URL and save.

---

> [!WARNING]
> **YouTube Bundle Identifier Conflicts**
>
> All modified YouTube variants use the same bundle identifier (`com.google.ios.youtube`).
> Completely uninstall any existing YouTube variant before installing another version to avoid update and signing conflicts.

> [!NOTE]
> Missing entitlement warnings may appear depending on your signing environment. Proceed if your sideloading setup supports the required entitlements.

---

## ⚙️ Automation Pipeline

```text
Upstream Feeds
       │
       ▼
GitHub Actions
       │
       ▼
Process & Validate
       │
       ▼
OmniSource Feeds
       │
       ▼
Client Sideloaders
```

### Resources

- 📂 Browse Feed Assets
- ⚙️ View GitHub Workflows
- 📜 View License

---

## 🙌 Credits & Acknowledgments

- 🐧 MountainofPenguin — Repository architecture and structure inspiration.
- 🛡️ HakujouSan — Testing, feedback, and community insights.
- 🛠️ Avieshek — Manifest parsing, debugging, and JSON assistance.
- ⚙️ S M Mahbub Hossain — Core development, automation workflows, and feed infrastructure.

---

## ⚖️ Disclaimer

OmniSource is an independent community project.

All third-party product names, logos, trademarks, and copyrighted materials belong to their respective owners. OmniSource does not host application binaries directly and does not claim ownership of cataloged applications. Users are solely responsible for complying with applicable laws, platform policies, and software license terms.

---

<div align="center">

### 🌐 OmniSource

**Automated • Organized • Unified**

⭐ Star the repository if you find it useful.

</div>

