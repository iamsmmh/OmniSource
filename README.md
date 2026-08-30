<div align="center">
  <a href="https://github.com/iamsmmh/OmniSource">
    <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/OmniSource.png" width="110" alt="OmniSource">
  </a>

  # OmniSource
  ### Automated iOS Sideloading Feed Repository

  [![Build](https://img.shields.io/github/actions/workflow/status/iamsmmh/OmniSource/update.yml?style=flat-square&logo=github-actions)](https://github.com/iamsmmh/OmniSource/actions)
  [![License](https://img.shields.io/github/license/iamsmmh/OmniSource?style=flat-square)](LICENSE)
  [![Stars](https://img.shields.io/github/stars/iamsmmh/OmniSource?style=flat-square)](https://github.com/iamsmmh/OmniSource/stargazers)

  A centralized, auto-updating collection of iOS app feeds — validated by GitHub Actions and served via GitHub Pages.
</div>

---

## ⚡ Master Feed

```
https://iamsmmh.github.io/OmniSource/apps.json
```

Add this URL to any AltStore-compatible client to get the full OmniSource collection in one source.

---

## 📦 Sources

| | Source | Feed |
|:---:|:---|:---:|
| <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/SpotiFLAC.png" width="28"> | SpotiFLAC Mobile | [Feed](https://iamsmmh.github.io/OmniSource/spotiflac.json) |
| <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/YouTube.png" width="28"> | uYouEnhanced | [Feed](https://iamsmmh.github.io/OmniSource/uyouenhanced.json) |
| <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/YouTube.png" width="28"> | YTKACE | [Feed](https://iamsmmh.github.io/OmniSource/ytkace.json) |
| <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/YouTube.png" width="28"> | YouPro | [Feed](https://iamsmmh.github.io/OmniSource/youpro.json) |
| <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/YouTube.png" width="28"> | YTLite | [Feed](https://iamsmmh.github.io/OmniSource/ytlite.json) |
| <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/YouTube.png" width="28"> | YTKillerPlus | [Feed](https://iamsmmh.github.io/OmniSource/ytkillerplus.json) |
| <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/YouTube.png" width="28"> | YouMod | [Feed](https://iamsmmh.github.io/OmniSource/youmod.json) |
| <img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/YouTubeMusic.png" width="28"> | YTMusicUltimate | [Feed](https://iamsmmh.github.io/OmniSource/ytmusicultimate.json) |

<details>
<summary><b>📋 Direct feed links (click to expand)</b></summary>

**SpotiFLAC Mobile**
```
https://iamsmmh.github.io/OmniSource/spotiflac.json
```

**uYouEnhanced**
```
https://iamsmmh.github.io/OmniSource/uyouenhanced.json
```

**YTKACE**
```
https://iamsmmh.github.io/OmniSource/ytkace.json
```

**YouPro**
```
https://iamsmmh.github.io/OmniSource/youpro.json
```

**YTLite**
```
https://iamsmmh.github.io/OmniSource/ytlite.json
```

**YTKillerPlus**
```
https://iamsmmh.github.io/OmniSource/ytkillerplus.json
```

**YouMod**
```
https://iamsmmh.github.io/OmniSource/youmod.json
```

**YTMusicUltimate**
```
https://iamsmmh.github.io/OmniSource/ytmusicultimate.json
```

</details>

---

## 📱 Supported Clients

<p align="center">
<img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/AltStore.png" width="40"> &nbsp;
<img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/SideStore.png" width="40"> &nbsp;
<img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/Feather.png" width="40"> &nbsp;
<img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/LiveContainer.png" width="40"> &nbsp;
<img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/E-Sign.png" width="40"> &nbsp;
<img src="https://raw.githubusercontent.com/iamsmmh/OmniSource/main/assets/Signulous.png" width="40">
</p>

<p align="center">AltStore · SideStore · Feather · LiveContainer · E-Sign · Signulous</p>

Copy any feed URL above and add it through your client's source/repository section. Uses the AltStore-compatible manifest format; compatibility depends on the client and signing environment.

---

## ⚙️ Automation

| Workflow | Purpose |
|:---|:---|
| `update.yml` | Feed updates |
| `updatex.yml` | Additional updates |
| `lint-action.yml` | Workflow validation |
| `delete-old-workflows-run.yml` | Run cleanup |

```
Upstream Sources → GitHub Actions → Validate → JSON Feeds → GitHub Pages
```

---

## 🙌 Credits

**Upstream projects**

| Project | Author(s) |
|:---|:---|
| [SpotiFLAC Mobile](https://github.com/spotiflacapp) | [spotiflacapp](https://github.com/spotiflacapp) |
| [uYouEnhanced](https://github.com/arichornlover/uYouEnhanced) | [arichornlover](https://github.com/arichornlover) & [MiRO92](https://github.com/MiRO92) |
| [YTKACE](https://github.com/itzzace/YTKACE) | [itzzace](https://github.com/itzzace) & [mrdrvt99](https://github.com/mrdrvt99) |
| [YouPro](https://github.com/Alibusut/YouPro) | [Alibusut](https://github.com/Alibusut) & [mrdrvt99](https://github.com/mrdrvt99) |
| [YTLite](https://github.com/Dayanch96/YTLite) | [Dayanch96](https://github.com/Dayanch96) & [mrdrvt99](https://github.com/mrdrvt99) |
| [YTKillerPlus](https://github.com/IKillerApp/YTKillerPlus) | [IKillerApp](https://github.com/IKillerApp) & [mrdrvt99](https://github.com/mrdrvt99) |
| [YouMod](https://github.com/mrdrvt99/YouMod) | [mrdrvt99](https://github.com/mrdrvt99) |
| [YTMusicUltimate](https://github.com/Dayanch96/YTMusicUltimate) | [Dayanch96](https://github.com/Dayanch96) & [mrdrvt99](https://github.com/mrdrvt99) |

**OmniSource team**

| Contributor | Role |
|:---|:---|
| [S M Mahbub Hossain](https://github.com/iamsmmh) | Development & automation |
| [MountainofPenguin](https://github.com/MountainofPenguin) | Architecture |
| [HakujouSan](https://github.com/HakujouSan) | Testing |
| [Avieshek](https://github.com/Avieshek) | Manifest assistance |

---

## ⚖️ Disclaimer

OmniSource is an independent community project. Third-party apps, code, trademarks, and releases belong to their respective owners. OmniSource only aggregates and distributes feeds — it claims no ownership of third-party projects. Availability may change without notice; users are responsible for complying with applicable laws and terms.

---

<div align="center">
  <sub>🌐 <a href="https://github.com/iamsmmh/OmniSource">OmniSource</a> · ⭐ <a href="https://github.com/iamsmmh/OmniSource/stargazers">Star this repo</a></sub>
</div>
