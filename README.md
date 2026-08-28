<div align="center">

<a href="https://github.com/iamsmmh/OmniSource">
  <img src="assets/OmniSource.png" width="120" alt="OmniSource Logo">
</a>

# 🌐 OmniSource

**Automated iOS Sideloading Feed Repository**

[![Build Status](https://img.shields.io/github/actions/workflow/status/iamsmmh/OmniSource/main.yml?style=flat-square&logo=github-actions&logoColor=white)](https://github.com/iamsmmh/OmniSource/actions)
[![License](https://img.shields.io/github/license/iamsmmh/OmniSource?style=flat-square)](https://github.com/iamsmmh/OmniSource/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/iamsmmh/OmniSource?style=flat-square&color=FFD700)](https://github.com/iamsmmh/OmniSource/stargazers)
[![Issues](https://img.shields.io/github/issues/iamsmmh/OmniSource?style=flat-square&color=FF6B6B)](https://github.com/iamsmmh/OmniSource/issues)

A centralized, automatically maintained collection of application feeds and manifests powered by GitHub Actions.

</div>

---

## 🚀 Feeds & Direct Installation

Copy the **Raw Source** URL for your preferred app (or the **OmniSource Master** feed for everything) and add it to your sideloader.

| App | Platform | Source Feed (JSON) | Direct Raw Source |
| :--- | :---: | :---: | :---: |
| <img src="assets/OmniSource.png" width="24" height="24" align="center"> **OmniSource Master (All Apps)** | **Unified** | [`apps.json`](https://github.com/iamsmmh/OmniSource/blob/main/apps.json) | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json` |
| <img src="assets/SpotiFLAC.png" width="24" height="24" align="center"> **SpotiFLAC Mobile** | iOS | [`spotiflac.json`](https://github.com/iamsmmh/OmniSource/blob/main/spotiflac.json) | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/spotiflac.json` |
| <img src="assets/YouTube.png" width="24" height="24" align="center"> **YTLite** | iOS | [`ytlite.json`](https://github.com/iamsmmh/OmniSource/blob/main/ytlite.json) | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytlite.json` |
| <img src="assets/YouTube.png" width="24" height="24" align="center"> **YTKillerPlus** | iOS | [`ytkp.json`](https://github.com/iamsmmh/OmniSource/blob/main/ytkp.json) | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytkp.json` |
| <img src="assets/YouTube.png" width="24" height="24" align="center"> **YouPro** | iOS | [`youpro.json`](https://github.com/iamsmmh/OmniSource/blob/main/youpro.json) | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/youpro.json` |
| <img src="assets/YouTube.png" width="24" height="24" align="center"> **YouMod** | iOS | [`youmod.json`](https://github.com/iamsmmh/OmniSource/blob/main/youmod.json) | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/youmod.json` |
| <img src="assets/YouTube.png" width="24" height="24" align="center"> **YTKACE** | iOS | [`ytkace.json`](https://github.com/iamsmmh/OmniSource/blob/main/ytkace.json) | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytkace.json` |
| <img src="assets/YouTubeMusic.png" width="24" height="24" align="center"> **YTMusicUltimate** | iOS | [`ytmusic.json`](https://github.com/iamsmmh/OmniSource/blob/main/ytmusic.json) | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytmusic.json` |

---

## 📥 Quick Setup Guide

1. **Copy** a Raw URL from the table above.
2. Open **AltStore, SideStore, Feather, ESign, LiveContainer, or Signulous**.
3. Go to **Sources / Repositories** → tap **`+`**.
4. Paste the URL, tap **Add**, and refresh your sources.
5. Browse and install your desired app!

> [!WARNING]
> **YouTube Bundle Identifier Conflicts (`com.google.ios.youtube`)**  
> Because modified YouTube variants share the same bundle ID, **completely uninstall any existing YouTube variant** before switching to a different one via OmniSource to avoid client conflicts.

> [!NOTE]
> Proceed through any missing entitlement warnings during installation. A standard sideloading environment/signing method is required.

---

## ⚙️ Automation & Repository Quick Links

OmniSource relies on continuous integration to keep manifests validated and up-to-date automatically.

- 📂 [Browse Feed Assets](https://github.com/iamsmmh/OmniSource/tree/main/assets)
- ⚙️ [View GitHub Actions Workflows](https://github.com/iamsmmh/OmniSource/tree/main/.github/workflows)
- 📜 [View License](https://github.com/iamsmmh/OmniSource/blob/main/LICENSE)

---

## 🙌 Credits & Acknowledgments

* 🐧 **[MountainofPenguin](https://github.com/MountainofPenguin)** — Repository architecture and structure inspiration.
* 🛡️ **[HakujouSan](https://www.reddit.com/user/HakujouSan/)** — Testing, feedback, and community insights.
* 🛠️ **[Avieshek](https://code.forgejo.org/avieshek/)** — JSON formatting, debugging, and development assistance.
* ⚙️ **[S M Mahbub Hossain](https://github.com/iamsmmh)** — Core development, automation workflows, infrastructure, and optimization.

---

## ⚖️ Disclaimer

OmniSource is an independent community project. All product names, logos, brands, and registered trademarks belong to their respective owners. OmniSource does not host software binaries directly or claim ownership of cataloged third-party applications. Users are responsible for complying with applicable local laws and software license terms.

---

<div align="center">

**🌐 OmniSource** • *Automated • Organized • Unified*

[![Star Repository](https://img.shields.io/badge/⭐_Star-OmniSource-FFD700?style=for-the-badge)](https://github.com/iamsmmh/OmniSource)

</div>

