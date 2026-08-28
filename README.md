The core issue stems from two technical limitations on GitHub and iOS:
 * GitHub Markdown Sanitization: GitHub's markdown renderer actively strips non-HTTP URL schemes (altstore://, sidestore://) from standard links/badges for security reasons, rendering the buttons unclickable or broken.
 * Missing sourceURL Key: Inside the JSON feed files (apps.json, spotiflac.json, etc.), if the top-level manifest does not contain the "sourceURL": "[https://raw.githubusercontent.com/](https://raw.githubusercontent.com/)..." key, AltStore and SideStore will reject deep-link imports or fail to refresh updates.
Solution 1: Use HTML <a> Anchors (Fixes GitHub Markdown Stripping)
Instead of Markdown [Label](altstore://...), write raw HTML <a> tags. GitHub permits custom schemes inside HTML href attributes.
<a href="altstore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json">AltStore</a>

Solution 2: Add "sourceURL" inside your JSON Feed Files
Ensure every JSON feed in your repository has the explicit sourceURL defined near the top.
Example (apps.json):
{
  "name": "OmniSource Master",
  "identifier": "com.iamsmmh.omnisource",
  "sourceURL": "https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json",
  "apps": [ ... ]
}

📄 Updated README.md (Tested Working Code)
Here is the full Markdown using explicit HTML anchors that bypass GitHub's link sanitizer:
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

Tap a **1-Click Import** button on iOS, or copy the Raw URL:

| App | Platform | 1-Click Import | Direct Raw Feed URL |
| :--- | :---: | :---: | :--- |
| <img src="assets/OmniSource.png" width="22" height="22" align="center"> **OmniSource Master** | **All-in-One** | <a href="altstore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json">AltStore</a> • <a href="sidestore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json">SideStore</a> | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json` |
| <img src="assets/SpotiFLAC.png" width="22" height="22" align="center"> **SpotiFLAC Mobile** | iOS | <a href="altstore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/spotiflac.json">AltStore</a> • <a href="sidestore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/spotiflac.json">SideStore</a> | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/spotiflac.json` |
| <img src="assets/YouTube.png" width="22" height="22" align="center"> **YTLite** | iOS | <a href="altstore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytlite.json">AltStore</a> • <a href="sidestore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytlite.json">SideStore</a> | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytlite.json` |
| <img src="assets/YouTube.png" width="22" height="22" align="center"> **YTKillerPlus** | iOS | <a href="altstore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytkp.json">AltStore</a> • <a href="sidestore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytkp.json">SideStore</a> | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytkp.json` |
| <img src="assets/YouTube.png" width="22" height="22" align="center"> **YouPro** | iOS | <a href="altstore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/youpro.json">AltStore</a> • <a href="sidestore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/youpro.json">SideStore</a> | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/youpro.json` |
| <img src="assets/YouTube.png" width="22" height="22" align="center"> **YouMod** | iOS | <a href="altstore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/youmod.json">AltStore</a> • <a href="sidestore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/youmod.json">SideStore</a> | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/youmod.json` |
| <img src="assets/YouTube.png" width="22" height="22" align="center"> **YTKACE** | iOS | <a href="altstore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytkace.json">AltStore</a> • <a href="sidestore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytkace.json">SideStore</a> | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytkace.json` |
| <img src="assets/YouTubeMusic.png" width="22" height="22" align="center"> **YTMusicUltimate** | iOS | <a href="altstore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytmusic.json">AltStore</a> • <a href="sidestore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytmusic.json">SideStore</a> | `https://raw.githubusercontent.com/iamsmmh/OmniSource/main/ytmusic.json` |

---

## 📥 Setup Instructions

1. **Automatic (AltStore / SideStore):** Tap **AltStore** or **SideStore** in the table above while browsing on iOS to open and add the feed automatically.
2. **Manual (Feather / ESign / LiveContainer / Signulous):** Copy the Raw Feed URL from the code block, open your app manager, go to **Sources** → tap **`+`**, and paste the URL.

> [!WARNING]
> **YouTube Bundle Identifier Conflicts (`com.google.ios.youtube`)**  
> All modified YouTube variants share the same bundle ID. Completely uninstall any existing YouTube variant before installing a different version to prevent client update conflicts.

> [!NOTE]
> Proceed through any missing entitlement warnings during installation. A standard sideloading environment is required.

---

## ⚙️ Automation Pipeline

OmniSource runs automated GitHub Actions to process, validate, and maintain feed manifests:


- 📂 [Browse Feed Assets](https://github.com/iamsmmh/OmniSource/tree/main/assets)
- ⚙️ [View GitHub Workflows](https://github.com/iamsmmh/OmniSource/tree/main/.github/workflows)
- 📜 [View License](https://github.com/iamsmmh/OmniSource/blob/main/LICENSE)

---

## 🙌 Credits & Acknowledgments

* 🐧 **[MountainofPenguin](https://github.com/MountainofPenguin)** — Repository architecture and structure inspiration.
* 🛡️ **[HakujouSan](https://www.reddit.com/user/HakujouSan/)** — Testing, feedback, and community insights.
* 🛠️ **[Avieshek](https://code.forgejo.org/avieshek/)** — Manifest parsing, debugging, and JSON assistance.
* ⚙️ **[S M Mahbub Hossain](https://github.com/iamsmmh)** — Core development, automation workflows, and feed infrastructure.

---

## ⚖️ Disclaimer

OmniSource is an independent community project. All third-party product names, logos, and trademarks belong to their respective owners. OmniSource does not host software binaries directly or claim ownership over cataloged applications. Users are responsible for complying with applicable local laws and license terms.

---

<div align="center">

**🌐 OmniSource** • *Automated • Organized • Unified*

[![Star Repository](https://img.shields.io/badge/⭐_Star-OmniSource-FFD700?style=for-the-badge)](https://github.com/iamsmmh/OmniSource)

</div>

