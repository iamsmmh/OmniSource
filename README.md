<div align="center">

# 🚀 OmniSource Repository

An automated repository engine for iOS sideloading & Android Magisk modules. Pre-patched IPAs, customized YouTube mods, and system extensions are automatically compiled and updated via GitHub Actions.

![AltStore Compatible](https://img.shields.io/badge/AltStore-Compatible-00C9A7?style=for-the-badge&logo=altstore&logoColor=white)
![SideStore Compatible](https://img.shields.io/badge/SideStore-Compatible-845EC2?style=for-the-badge&logo=apple&logoColor=white)
![GitHub Actions Automated](https://img.shields.io/badge/GitHub_Actions-Automated-D65DB1?style=for-the-badge&logo=githubactions&logoColor=white)
![Maintained](https://img.shields.io/badge/Maintained%3F-Yes-FF6F91?style=for-the-badge)

</div>

---

## ⚡ Quick Add Source

Copy and paste the raw manifest URL into **AltStore**, **SideStore**, or **TrollStore**:

```text
[https://raw.githubusercontent.com/iamsmmh/revanced-magisk-module/main/apps.json](https://raw.githubusercontent.com/iamsmmh/revanced-magisk-module/main/apps.json)

Direct One-Tap Import Links:
 * ▶ Add to AltStore
 * ▶ Add to SideStore
🚀 Featured Applications & Modules
| App / Mod | Platform | Features | Status |
|---|---|---|---|
| uYouEnhanced
(YouTube iOS Mod) | iOS (.ipa) | • OLED Pure Black Theme
• Integrated SponsorBlock & RYD
• Background Playback & PiP
• Media Downloader |  |
| YouTube ReVanced
(Extended Engine) | Android / Magisk | • Return YouTube Dislike (RYD)
• Custom Material You Themes
• Video & Audio Adblocking
• GMS Core Support |  |
| YTLitePlus
(Lite Edition) | iOS (.ipa) | • Ultra-lightweight footprint
• Custom Navigation Bar Layout
• Miniplayer gesture overrides
• Native quality auto-select |  |
🛠️ Installation & Setup Workflow
 * Prerequisite: Ensure AltStore, SideStore, or LiveContainer is installed on your iOS device.
 * Add Source: Open your sideload manager \rightarrow Go to Sources \rightarrow Tap + \rightarrow Paste:
   [https://raw.githubusercontent.com/iamsmmh/revanced-magisk-module/main/apps.json](https://raw.githubusercontent.com/iamsmmh/revanced-magisk-module/main/apps.json)

 * Install & Enjoy: Select your preferred application build and tap Install.
⚙️ Automated Pipeline Architecture
graph LR
    A[Upstream Releases] -->|Cron Trigger| B[GitHub Actions Engine]
    B -->|Fetch IPAs & Modules| C[Checksum Verification]
    C -->|Generate Manifest| D[apps.json]
    D -->|Serve| E[AltStore / SideStore / Magisk]

<div align="center">
<sub>Designed & Maintained with GitHub Actions automation.</sub>

<sub><strong>Disclaimer:</strong> This project functions exclusively as an automated indexing system. All brand assets belong to their respective owners.</sub>
</div>

