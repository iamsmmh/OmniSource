<div align="center">
  <a href="https://github.com/iamsmmh/OmniSource">
    <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/OmniSource.png" width="120" alt="OmniSource Logo">
  </a>

  # <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/OmniSource.png" width="28" valign="middle" alt="logo"> OmniSource

  ### Automated iOS Sideloading Feed Repository

  [![Build](https://img.shields.io/github/actions/workflow/status/iamsmmh/OmniSource/update.yml?style=flat-square&logo=github-actions)](https://github.com/iamsmmh/OmniSource/actions)
  [![License](https://img.shields.io/github/license/iamsmmh/OmniSource?style=flat-square)](LICENSE)
  [![Stars](https://img.shields.io/github/stars/iamsmmh/OmniSource?style=flat-square)](https://github.com/iamsmmh/OmniSource/stargazers)

  **Unified • Automated • Organized**

  A centralized collection of iOS application feeds and manifests, automatically maintained through GitHub Actions and distributed via GitHub Pages.
</div>

---

## <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/OmniSource.png" width="22" valign="middle" alt="logo"> Master Feed

<div align="center">

<a href="https://iamsmmh.github.io/OmniSource/apps.json">
  <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/OmniSource.png" width="48" alt="OmniSource Master Feed">
</a>

**OmniSource Master Source**

```
https://iamsmmh.github.io/OmniSource/apps.json
```

[Add to AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/apps.json) · [Add to SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/apps.json)

The Master Feed provides the complete OmniSource collection.

</div>

---

## 📦 Sources

<div align="center">

| Icon | Source | Feed |
|:---:|:---|:---:|
| <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/SpotiFLAC.png" width="32"> | [SpotiFLAC Mobile](https://github.com/spotiflacapp) | [Feed](https://iamsmmh.github.io/OmniSource/spotiflac.json) |
| <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/YouTube.png" width="32"> | [uYouEnhanced](https://github.com/arichornlover/uYouEnhanced) | [Master](https://iamsmmh.github.io/OmniSource/uyouenhanced.json) |
| <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/YouTube.png" width="32"> | [YTKACE](https://github.com/itzzace/YTKACE) | [Feed](https://iamsmmh.github.io/OmniSource/ytkace.json) |
| <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/YouTube.png" width="32"> | [YouPro](https://github.com/Alibusut/YouPro) | [Feed](https://iamsmmh.github.io/OmniSource/youpro.json) |
| <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/YouTube.png" width="32"> | [YTLite](https://github.com/Dayanch96/YTLite) | [Feed](https://iamsmmh.github.io/OmniSource/ytlite.json) |
| <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/YouTube.png" width="32"> | [YTKillerPlus](https://github.com/IKillerApp/YTKillerPlus) | [Feed](https://iamsmmh.github.io/OmniSource/ytkillerplus.json) |
| <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/YouTube.png" width="32"> | [YouMod](https://github.com/mrdrvt99/YouMod) | [Feed](https://iamsmmh.github.io/OmniSource/youmod.json) |
| <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/YouTubeMusic.png" width="32"> | [YTMusicUltimate](https://github.com/Dayanch96/YTMusicUltimate) | [Feed](https://iamsmmh.github.io/OmniSource/ytmusicultimate.json) |

</div>

---

## 📱 Supported Clients

<div align="center">

<a href="https://altstore.io"><img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/AltStore.png" width="48" alt="AltStore"><br>AltStore</a>&nbsp;&nbsp;&nbsp;
<a href="https://sidestore.io"><img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/SideStore.png" width="48" alt="SideStore"><br>SideStore</a>&nbsp;&nbsp;&nbsp;
<a href="https://github.com/khcrysalis/Feather"><img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/Feather.png" width="48" alt="Feather"><br>Feather</a>&nbsp;&nbsp;&nbsp;
<a href="https://github.com/LiveContainer/LiveContainer"><img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/LiveContainer.png" width="48" alt="LiveContainer"><br>LiveContainer</a>&nbsp;&nbsp;&nbsp;
<a href="https://github.com/QuarkEsign/Esign"><img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/E-Sign.png" width="48" alt="E-Sign"><br>E-Sign</a>&nbsp;&nbsp;&nbsp;
<a href="https://signulous.com"><img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/Signulous.png" width="48" alt="Signulous"><br>Signulous</a>

</div>

OmniSource uses the AltStore-compatible source/manifest format. Compatibility depends on the client and signing environment.

---

## 📲 Installation

**AltStore / SideStore**

Use the one-tap links above or manually add:

```
https://iamsmmh.github.io/OmniSource/apps.json
```

**Feather · LiveContainer · E-Sign · Signulous**

Copy any feed URL from the [Sources](#-sources) section and add it through the client's source/repository section.

---

## ⚙️ Automation

OmniSource uses [GitHub Actions](https://github.com/iamsmmh/OmniSource/actions) for automated feed updates and validation.

<div align="center">

| Workflow | Purpose |
|:---|:---:|
| [`update.yml`](https://github.com/iamsmmh/OmniSource/blob/main/.github/workflows/update.yml) | Feed updates |
| [`updatex.yml`](https://github.com/iamsmmh/OmniSource/blob/main/.github/workflows/updatex.yml) | Additional updates |
| [`lint-action.yml`](https://github.com/iamsmmh/OmniSource/blob/main/.github/workflows/lint-action.yml) | Workflow validation |
| [`delete-old-workflows-run.yml`](https://github.com/iamsmmh/OmniSource/blob/main/.github/workflows/delete-old-workflows-run.yml) | Run cleanup |

</div>

<div align="center">

```
Upstream Sources
      ↓
GitHub Actions
      ↓
Update & Validate
      ↓
JSON Feeds
      ↓
GitHub Pages
```

</div>

---

## 📂 Repository

<div align="center">

- [OmniSource Repository](https://github.com/iamsmmh/OmniSource)
- 📦 [Master Feed](https://iamsmmh.github.io/OmniSource/apps.json)
- 🖼️ [Assets](https://github.com/iamsmmh/OmniSource/tree/main/assets)
- ⚙️ [Actions](https://github.com/iamsmmh/OmniSource/actions)
- 🚀 [Releases](https://github.com/iamsmmh/OmniSource/releases)
- 🐛 [Issues](https://github.com/iamsmmh/OmniSource/issues)
- 📜 [License](https://github.com/iamsmmh/OmniSource/blob/main/LICENSE)

</div>

---

## 🙌 Credits

**Upstream Projects**

<div align="center">

| Project | Author(s) |
|:---|:---:|
| [SpotiFLAC Mobile](https://github.com/spotiflacapp) | [spotiflacapp](https://github.com/spotiflacapp) |
| [uYouEnhanced](https://github.com/arichornlover/uYouEnhanced) | [arichornlover](https://github.com/arichornlover) & [MiRO92](https://github.com/MiRO92) |
| [YTKACE](https://github.com/itzzace/YTKACE) | [itzzace](https://github.com/itzzace) & [mrdrvt99](https://github.com/mrdrvt99) |
| [YouPro](https://github.com/Alibusut/YouPro) | [Alibusut](https://github.com/Alibusut) & [mrdrvt99](https://github.com/mrdrvt99) |
| [YTLite](https://github.com/Dayanch96/YTLite) | [Dayanch96](https://github.com/Dayanch96) & [mrdrvt99](https://github.com/mrdrvt99) |
| [YTKillerPlus](https://github.com/IKillerApp/YTKillerPlus) | [IKillerApp](https://github.com/IKillerApp) & [mrdrvt99](https://github.com/mrdrvt99) |
| [YouMod](https://github.com/mrdrvt99/YouMod) | [mrdrvt99](https://github.com/mrdrvt99) |
| [YTMusicUltimate](https://github.com/Dayanch96/YTMusicUltimate) | [Dayanch96](https://github.com/Dayanch96) & [mrdrvt99](https://github.com/mrdrvt99) |

</div>

**OmniSource**

<div align="center">

| Contributor | Role |
|:---|:---:|
| [S M Mahbub Hossain](https://github.com/iamsmmh) | Development, feed infrastructure & automation |
| [MountainofPenguin](https://github.com/MountainofPenguin) | Architecture inspiration |
| [HakujouSan](https://github.com/HakujouSan) | Testing & feedback |
| [Avieshek](https://github.com/Avieshek) | Manifest & JSON assistance |

</div>

---

## ⚖️ Disclaimer

OmniSource is an independent community project.

Third-party applications, source code, trademarks, logos, modifications, and releases belong to their respective owners.

OmniSource provides feed aggregation, indexing, and distribution and does not claim ownership of third-party projects.

Availability and compatibility may change without notice. Users are responsible for complying with applicable laws, licenses, and service terms.

---

<div align="center">
  <a href="https://github.com/iamsmmh/OmniSource">
    <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/OmniSource.png" width="64" alt="OmniSource Logo">
  </a>

  <br>

  <b>🌐 <a href="https://github.com/iamsmmh/OmniSource">OmniSource</a> · ⭐ <a href="https://github.com/iamsmmh/OmniSource/stargazers">Star Repository</a></b>
</div>
