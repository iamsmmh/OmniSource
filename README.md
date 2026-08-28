<div align="center">
<img src="assets/OmniSource.png" width="120" alt="OmniSource">

🌐 OmniSource

🚀 Automated Sideloading & Module Feed Engine

One Repository • Multiple Feeds • Automated Distribution

OmniSource is an automated repository engine for iOS sideloading and Android modules, designed to collect, process, validate, organize, and distribute supported application feeds through a centralized architecture powered by GitHub Actions.

<p align="center">
  <img src="https://img.shields.io/badge/AltStore-Compatible-00C9A7?style=for-the-badge&logo=altstore&logoColor=white" alt="AltStore Compatible">
  <img src="https://img.shields.io/badge/SideStore-Compatible-845EC2?style=for-the-badge&logo=apple&logoColor=white" alt="SideStore Compatible">
  <img src="https://img.shields.io/badge/ESign-Compatible-FF9F43?style=for-the-badge&logo=ios&logoColor=white" alt="ESign Compatible">
  <img src="https://img.shields.io/badge/Feather-Compatible-007AFF?style=for-the-badge&logo=swift&logoColor=white" alt="Feather Compatible">
  <img src="https://img.shields.io/badge/LiveContainer-Compatible-5E60CE?style=for-the-badge&logo=apple&logoColor=white" alt="LiveContainer Compatible">
</p>
<p align="center">
  <img src="https://img.shields.io/badge/GitHub_Actions-Automated-D65DB1?style=for-the-badge&logo=githubactions&logoColor=white" alt="GitHub Actions">
  <img src="https://img.shields.io/github/stars/iamsmmh/OmniSource?style=for-the-badge&logo=github" alt="GitHub Stars">
  <img src="https://img.shields.io/github/forks/iamsmmh/OmniSource?style=for-the-badge&logo=github" alt="GitHub Forks">
  <img src="https://img.shields.io/github/issues/iamsmmh/OmniSource?style=for-the-badge&logo=github" alt="GitHub Issues">
</p>
</div>

⸻

⚡ What Is OmniSource?

OmniSource brings supported application feeds together into one organized, automation-focused repository.

Instead of manually managing multiple source repositories, OmniSource provides a centralized feed architecture with automated processing through GitHub Actions.

🤖 Core Workflow

📦 Source Data
      ↓
🤖 GitHub Actions
      ↓
🔍 Processing & Validation
      ↓
🧮 Integrity Checks
      ↓
📄 Manifest Generation
      ↓
🌐 OmniSource Feeds
      ↓
📲 Sideloading / Module Managers

⸻

📊 Repository Highlights

Capability	Status
🤖 GitHub Actions Automation	✅
🌐 Unified Master Feed	✅
📦 Individual JSON Feeds	✅
🔍 Feed / Manifest Processing	✅
🧮 Integrity / Checksum Processing	✅
🍎 iOS Feed Support	✅
🤖 Android Module Ecosystem	✅
📲 AltStore	✅
📲 SideStore	✅
📲 Feather	✅
📲 ESign	✅
📲 LiveContainer	✅

⸻

⚡ Quick Add Source

🌐 Master Feed

Use the Master Feed to access the centralized OmniSource collection:

https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json

📲 One-Tap Import

AltStore

altstore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json

SideStore

sidestore://source?url=https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json

💡 Recommended: Use the Master Feed instead of adding individual feeds when you want the complete OmniSource collection.

⸻

🚀 Available Feeds

Logo	Feed	Platform	Description	Manifest
	YouPro	🍎 iOS	YouTube modification	youpro.json
	YTLite	🍎 iOS	Lightweight YouTube modification	ytlite.json
	YTKillerPlus	🍎 iOS	Enhanced YouTube modification	ytkp.json
	YouMod	🍎 iOS	Custom YouTube modification	youmod.json
	YTKACE	🍎 iOS	Advanced YouTube build	ytkace.json
	YTMusicUltimate	🍎 iOS	YouTube Music modification	ytmusic.json
	SpotiFLAC Mobile	🍎 iOS	SpotiFLAC feed	spotiflac.json
	OmniSource	🌐 Unified	Master feed	apps.json

🖼️ Logo Strategy

OmniSource intentionally uses shared logos where multiple feeds belong to the same application family:

* 🔴 YouPro, YTLite, YTKillerPlus, YouMod, YTKACE → assets/YouTube.png
* 🎵 YTMusicUltimate → assets/YouTubeMusic.png
* 🎵 SpotiFLAC Mobile → assets/SpotiFLAC.png
* 🌐 OmniSource → assets/OmniSource.png

This keeps the repository lightweight while maintaining a consistent visual identity.

⸻

🏗️ Feed Architecture

graph TD
    Master["🌐 OmniSource Master<br/>apps.json"]
    Master --> YouPro["🔴 YouPro"]
    Master --> YTLite["🔴 YTLite"]
    Master --> YTKP["🔴 YTKillerPlus"]
    Master --> YouMod["🔴 YouMod"]
    Master --> YTKACE["🔴 YTKACE"]
    Master --> YTMusic["🎵 YTMusicUltimate"]
    Master --> SpotiFLAC["🎵 SpotiFLAC Mobile"]

The Master Feed provides a centralized entry point while individual JSON manifests remain available for direct use.

⸻

⚙️ Automated Pipeline

graph LR
    A["📦 Upstream Sources"]
    --> B["🤖 GitHub Actions"]
    B --> C["🔍 Process & Validate"]
    C --> D["🧮 Integrity Checks"]
    D --> E["📄 Generate Manifests"]
    E --> F["🌐 Publish OmniSource"]
    F --> G["📲 AltStore"]
    F --> H["📲 SideStore"]
    F --> I["📲 Feather"]
    F --> J["📲 ESign"]
    F --> K["📲 LiveContainer"]
    F --> L["🤖 Android Modules"]

🔄 Processing Flow

1. 📦 Collect supported source information.
2. 🤖 Process source data through GitHub Actions.
3. 🔍 Validate feed and manifest data.
4. 🧮 Perform available integrity checks.
5. 📄 Generate or update manifests.
6. 🌐 Publish updated feeds.
7. 📲 Distribute feeds to compatible clients.

⸻

✨ Features

🤖 Automation

* GitHub Actions-powered processing
* Automated feed generation
* Automated manifest updates
* Scheduled source processing
* Reduced manual maintenance
* Centralized repository management

🌐 Feed Architecture

* Unified Master Feed
* Individual application feeds
* Modular JSON manifests
* Centralized distribution
* Direct raw-feed access
* Expandable architecture

🛡️ Validation

* Feed processing
* JSON manifest validation
* Integrity checking
* Checksum processing where available
* Structured feed organization

📱 Platform Support

🍎 iOS

* AltStore
* SideStore
* Feather
* ESign
* LiveContainer
* IPA-based feeds

🤖 Android

* Android-oriented feed/module support
* Magisk ecosystem support where applicable

Compatibility depends on the individual feed, application, module, operating-system version, signing method, and client implementation.

⸻

🛠️ Installation Guide

1️⃣ Choose Your Sideloading Manager

Open your preferred compatible application:

* 📲 AltStore
* 📲 SideStore
* 📲 Feather
* 📲 ESign
* 📲 LiveContainer

2️⃣ Open Sources / Repositories

Navigate to the application’s source or repository management section.

3️⃣ Add OmniSource

Tap the + button.

4️⃣ Add the Master Feed

https://raw.githubusercontent.com/iamsmmh/OmniSource/main/apps.json

5️⃣ Refresh

Refresh your source list.

6️⃣ Install

Browse the available entries and use your manager’s normal installation process.

💡 A valid signing or sideloading setup may be required depending on your device and installation method.

⸻

🔗 Direct Feed URLs

Feed	Raw JSON
🔴 YouPro	youpro.json
🔴 YTLite	ytlite.json
🔴 YTKillerPlus	ytkp.json
🔴 YouMod	youmod.json
🔴 YTKACE	ytkace.json
🎵 YTMusicUltimate	ytmusic.json
🎵 SpotiFLAC Mobile	spotiflac.json
🌐 OmniSource Master	apps.json

⸻

⚠️ Important Notice for Existing YouTube Users

🚨 Avoid blindly updating between different modified YouTube variants.

Modified YouTube builds may share the native bundle identifier:

com.google.ios.youtube

Because sideloading managers can identify applications using their bundle identifiers, different modified variants may potentially be treated as the same application.

🔄 Recommended Migration

1. 💾 Back up important application data.
2. 🗑️ Remove the existing modified build if switching variants.
3. 🔄 Refresh OmniSource.
4. 📲 Select your preferred variant.
5. ✅ Perform a fresh installation.

This minimizes potential conflicts between different modified builds.

⸻

📁 Repository Structure

OmniSource/
│
├── 📄 apps.json
├── 📄 spotiflac.json
├── 📄 youmod.json
├── 📄 youpro.json
├── 📄 ytkace.json
├── 📄 ytkp.json
├── 📄 ytlite.json
├── 📄 ytmusic.json
│
├── 📁 assets/
│   ├── 🖼️ OmniSource.png
│   ├── 🖼️ SpotiFLAC.png
│   ├── 🖼️ YouTube.png
│   └── 🖼️ YouTubeMusic.png
│
├── 📁 .github/
│   └── 📁 workflows/
│
├── 📄 LICENSE
└── 📄 README.md

⸻

🖼️ Asset Architecture

The repository uses a simple shared-asset model:

assets/
│
├── OmniSource.png
│       └── 🌐 OmniSource branding
│
├── SpotiFLAC.png
│       └── 🎵 SpotiFLAC Mobile
│
├── YouTube.png
│       ├── 🔴 YouPro
│       ├── 🔴 YTLite
│       ├── 🔴 YTKillerPlus
│       ├── 🔴 YouMod
│       └── 🔴 YTKACE
│
└── YouTubeMusic.png
        └── 🎵 YTMusicUltimate

This avoids unnecessary duplication and makes future feed additions easier to maintain.

⸻

❤️ Support

If OmniSource is useful to you:

⭐ Star the repository

🍴 Fork the project

📢 Share OmniSource with the community

🐞 Report broken feeds or bugs

💡 Suggest improvements

⸻

🐛 Issues & Contributions

Found a broken feed, invalid manifest, outdated entry, or repository issue?

Please include:

* 📱 Application / feed name
* 🔢 Version
* ❌ Problem encountered
* 🧾 Error message
* 📲 Sideloading manager
* 📱 iOS / Android version
* 🔗 Relevant feed URL

Clear reports make troubleshooting and automated maintenance easier.

⸻

🙌 Credits & Acknowledgments

OmniSource builds upon ideas, infrastructure concepts, testing, feedback, and community contributions from the wider sideloading ecosystem.

🐧 Framework & Inspiration

MountainofPenguin

* Original repository framework
* Feed architecture inspiration
* Automation concepts
* Community ecosystem contributions

🔗 Altstore-Repository

🛡️ Community Support

HakujouSan

* Community feedback
* Architecture suggestions
* Testing insights

🛠️ Development Assistance

Avieshek

* JSON structuring
* Manifest improvements
* Testing and debugging
* Development assistance

⚙️ OmniSource Engineering

S M Mahbub Hossain

* Repository Owner & Maintainer
* Automation Engineering
* Feed Infrastructure
* GitHub Actions Pipeline
* Manifest Management
* Repository Optimization

⸻

🌟 Project Philosophy

OmniSource follows one simple principle:

Make application feeds easier to discover, maintain, automate, and consume.

The architecture is designed to remain modular so new feeds, applications, platforms, and automation capabilities can be added without rebuilding the entire ecosystem.

🌐 One Repository
       ↓
📦 Multiple Feeds
       ↓
🤖 Automated Processing
       ↓
🔍 Validation
       ↓
📄 Manifests
       ↓
📲 Distribution

⸻

⚖️ Disclaimer

OmniSource is an independent community project.

This repository functions primarily as an indexing, organization, automation, and manifest-distribution layer.

OmniSource does not claim ownership of third-party applications, trademarks, logos, names, or related intellectual property referenced by the feeds.

All trademarks, application names, logos, and intellectual property belong to their respective owners.

Users are responsible for ensuring that their use of any application, modification, module, sideloading method, or signing service complies with applicable laws, licenses, and platform terms of service.

The presence of an application, module, feed, or reference in OmniSource does not constitute endorsement by the original developer or trademark owner.

⸻

🔗 Community Profiles

* 🐧 MountainofPenguin
* 🛡️ HakujouSan
* 🛠️ Avieshek
* ⚙️ S M Mahbub Hossain

⸻

<div align="center">
<img src="assets/OmniSource.png" width="70" alt="OmniSource">

🌐 OmniSource

🤖 Automated • 📦 Organized • ⚡ Unified

Built with ❤️ and GitHub Actions

<br>

⭐ If OmniSource is useful to you, consider starring the repository.

<br>

🌐 Repository •
🐛 Issues •
⭐ Star

</div>
