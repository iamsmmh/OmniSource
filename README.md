<div align="center">

<img src="assets/OmniSource.png" width="120" alt="">

# OmniSource

**A curated iOS application repository and distribution platform.**

[Website](https://iamsmmh.github.io/OmniSource/) ·
[Install](docs/INSTALLATION.md) ·
[Catalog](docs/CATALOG.md) ·
[Compatibility](docs/COMPATIBILITY.md) ·
[Contribute](docs/CONTRIBUTING.md)

</div>

---

OmniSource tracks upstream iOS app releases, verifies every download link, and publishes a single
AltStore-compatible feed that works across every major sideloading client.

## Add the source

```
https://iamsmmh.github.io/OmniSource/apps.json
```

<a href="altstore://source?url=https://iamsmmh.github.io/OmniSource/apps.json">Add to AltStore</a> ·
<a href="sidestore://source?url=https://iamsmmh.github.io/OmniSource/apps.json">Add to SideStore</a> ·
<a href="feather://source/iamsmmh.github.io/OmniSource/apps.json">Add to Feather</a>

Per-app feeds are listed in the table below. Full walkthroughs for every client live in the
[Installation Guide](docs/INSTALLATION.md).

## Supported clients

| Client | Status | Notes |
| --- | --- | --- |
| **AltStore** | Supported | Reference client; the feed targets its schema |
| **SideStore** | Supported | Same schema, on-device refresh |
| **Feather** | Supported | Sign-on-device with your own certificate |
| **ESign** | Supported | Add as a source, then sign manually |
| **LiveContainer** | Supported | Run IPAs without consuming an app slot |

## Catalog

<!-- omnisource:catalog:start -->

_Catalogue last changed 2026-09-01 · 8 apps · 8/8 downloads reachable._

| App | Version | Updated | Status | Download | Feed URL |
| --- | --- | --- | --- | --- | --- |
| **SpotiFLAC Mobile** | `4.9.5` | 2026-09-01 | 🟢 stable | ✅ | `https://iamsmmh.github.io/OmniSource/spotiflac.json` |
| **uYouEnhanced** | `21.14.4` | 2026-08-22 | 🔵 manual | ✅ | `https://iamsmmh.github.io/OmniSource/uyouenhanced.json` |
| **YouTubePlus** | `21.24.3` | 2026-09-01 | 🟢 stable | ✅ | `https://iamsmmh.github.io/OmniSource/ytlite.json` |
| **YouPro** | `21.24.3` | 2026-08-16 | 🟢 stable | ✅ | `https://iamsmmh.github.io/OmniSource/youpro.json` |
| **YTKillerPlus** | `21.35.3` | 2026-08-30 | 🟢 stable | ✅ | `https://iamsmmh.github.io/OmniSource/ytkp.json` |
| **YTKACE** | `21.35.3` | 2026-09-01 | 🟢 stable | ✅ | `https://iamsmmh.github.io/OmniSource/ytkace.json` |
| **YouMod** | `21.35.3` | 2026-08-30 | 🟢 stable | ✅ | `https://iamsmmh.github.io/OmniSource/youmod.json` |
| **YTMusicUltimate** | `9.35.2` | 2026-09-01 | 🟢 stable | ✅ | `https://iamsmmh.github.io/OmniSource/ytmusic.json` |

<!-- omnisource:catalog:end -->

Status legend: 🟢 stable · 🟡 beta · 🔵 manually published · 🔴 unmaintained.
Download column reflects the last automated reachability probe.

## How it works

```
catalog.json ──▶ scripts/omnisource.py ──▶ feeds/*.json ──▶ GitHub Pages ──▶ your client
   (edited)          (every 6 hours)         (generated)
```

`catalog.json` is the only hand-edited file. Everything else — the master feed, the per-app feeds,
the root-level compatibility mirrors, the health snapshot and the table above — is generated.
See the [Architecture Guide](docs/ARCHITECTURE.md).

## Repository layout

| Path | Purpose |
| --- | --- |
| `catalog.json` | Source of truth: apps, upstream repositories, metadata |
| `feeds/` | Generated AltStore feeds + `health.json` + pipeline state |
| `*.json` (root) | Generated mirrors that keep historical feed URLs working |
| `assets/` | App and client icons served over Pages |
| `scripts/` | `omnisource.py` (build) and `validate.py` (checks) |
| `website/` | Static GitHub Pages site |
| `docs/` | Installation, catalog, compatibility, contributing, architecture |

> [!IMPORTANT]
> The refactored workflows are staged in [`.github/workflows-pending/`](.github/workflows-pending/README.md)
> and need one command to activate — the automation account that opened this branch cannot write to
> `.github/workflows/`.

## Contributing

Adding an app is a one-file change to `catalog.json`. Read the
[Contribution Guide](docs/CONTRIBUTING.md), then run:

```bash
python3 scripts/omnisource.py   # sync + rebuild every feed
python3 scripts/validate.py     # offline structural checks
```

Both scripts use only the Python standard library — no virtualenv, no dependencies.

## Disclaimer

OmniSource is an independent community project. It aggregates and redistributes third-party
releases; all apps, code and trademarks belong to their respective owners. Availability may change
without notice, and you are responsible for complying with applicable laws and terms of service.

Credits to upstream maintainers are listed in [docs/CATALOG.md](docs/CATALOG.md).

## License

See [LICENSE](LICENSE).
