<div align="center">

<img src="assets/OmniSource.png" width="120" alt="OmniSource">

# OmniSource
**The App Store for sideloaded iOS — one feed, five clients, always current.**

One source URL for **AltStore · SideStore · Feather · ESign · LiveContainer**.

<!-- omnisource:stats:start -->

**77** apps (**66** in the [master source](https://iamsmmh.github.io/OmniSource/apps.json)) · **61** upstream sources · **76** verified · **1** community verified · **77/77** downloads online · last sync **2026-09-11**.

<!-- omnisource:stats:end -->

[![Sync & Publish](https://github.com/iamsmmh/OmniSource/actions/workflows/sync.yml/badge.svg)](https://github.com/iamsmmh/OmniSource/actions/workflows/sync.yml)
[![Validate](https://github.com/iamsmmh/OmniSource/actions/workflows/validate.yml/badge.svg)](https://github.com/iamsmmh/OmniSource/actions/workflows/validate.yml)
[![Website](https://img.shields.io/website?url=https%3A%2F%2Fiamsmmh.github.io%2FOmniSource%2F&label=website)](https://iamsmmh.github.io/OmniSource/)
[![License](https://img.shields.io/github/license/iamsmmh/OmniSource)](LICENSE)

[Add the Source](#-add-the-source) · [Website](https://iamsmmh.github.io/OmniSource/) · [API](#-api) · [Contributing](CONTRIBUTING.md)

</div>

---

## 🚀 Add the Source

**Source URL**

```
https://iamsmmh.github.io/OmniSource/apps.json
```

Tap to add in one go:

| Client | Link |
|---|---|
| **AltStore** | [➕ Add to AltStore](altstore://source?url=https://iamsmmh.github.io/OmniSource/apps.json) |
| **SideStore** | [➕ Add to SideStore](sidestore://source?url=https://iamsmmh.github.io/OmniSource/apps.json) |
| **Feather** | [➕ Add to Feather](feather://source/iamsmmh.github.io/OmniSource/apps.json) |
| **ESign** | [➕ Add to ESign](esign://addsource?url=https://iamsmmh.github.io/OmniSource/apps.json) |
| **LiveContainer** | [➕ Add to LiveContainer](livecontainer://sources?url=https://iamsmmh.github.io/OmniSource/apps.json) |

> **Tip:** YouTube tweaks share a bundle ID and overwrite each other. Use a single-app feed at `feeds/<slug>.json` — each app page has a **Copy source link** button.

Full guides, QR codes and per-app links: **[Installation Center](https://iamsmmh.github.io/OmniSource/install/)**

---

## ✨ Why OmniSource?

- **Official upstreams only** — every release resolves from the developer's own GitHub Releases or AltStore feed. Community-built IPAs are clearly labeled *Community build*.
- **Verified & health-checked** — SHA-256, verification labels and automated probes keep every download installable.
- **Fresh every 6 hours** — pipeline syncs releases, rebuilds feeds and redeploys the site automatically.
- **A real PWA, not just JSON** — search (⌘K), compare, health, analytics, favorites, collections and offline support — zero frameworks, zero build step.

---

## 🌐 Website

[Home](https://iamsmmh.github.io/OmniSource/) · [Apps](https://iamsmmh.github.io/OmniSource/#catalog) · [Collections](https://iamsmmh.github.io/OmniSource/collections/) · [Sources](https://iamsmmh.github.io/OmniSource/sources/) · [Status](https://iamsmmh.github.io/OmniSource/status/) · [Docs](https://iamsmmh.github.io/OmniSource/docs/) — plus [Compare](https://iamsmmh.github.io/OmniSource/compare/), [Analytics](https://iamsmmh.github.io/OmniSource/analytics/), [Install](https://iamsmmh.github.io/OmniSource/install/), [Search](https://iamsmmh.github.io/OmniSource/search/), [Favorites](https://iamsmmh.github.io/OmniSource/favorites/), [Discover](https://iamsmmh.github.io/OmniSource/discover/) and [Community](https://iamsmmh.github.io/OmniSource/api/community.json) under “More”.

The site is an installable **PWA** with offline shell and "new version available" prompt. The
[Source Explorer](https://iamsmmh.github.io/OmniSource/sources/) gives every upstream a page of
its own — maintainer, feed URL, app count, update cadence, health, verification and a reputation
status (`Verified / Community Verified / Maintained / Warning / Inactive / Deprecated`).

---

## 📚 Catalog

<!-- omnisource:catalog:start -->

Browse the full **77-app catalog** on the [website](https://iamsmmh.github.io/OmniSource/#catalog) — all installable with one tap.

- Combined feeds: [`feeds/apps.json`](./feeds/apps.json), [`feeds/feed.xml`](./feeds/feed.xml), [`catalog.json`](./catalog.json)
- Substrate docs: [`feeds/sources.json`](./feeds/sources.json), [`feeds/discovery.json`](./feeds/discovery.json), [`feeds/health.json`](./feeds/health.json), [`feeds/updates.json`](./feeds/updates.json), [`feeds/verification.json`](./feeds/verification.json)
- Per-app feeds at `feeds/<slug>.json` and `feeds/<slug>.xml` — e.g. [`feeds/esign.json`](./feeds/esign.json)
- Apps in a bundle-ID collision group ship as **single-app sources** (11 app(s)): the master source carries the recommended member of each group, because a client cannot install two apps that share a bundle ID side by side.

_Last sync 2026-09-12 · 77/77 downloads reachable._

<!-- omnisource:catalog:end -->

---

## ⚙️ How It Works

```
catalog.json → scripts/omnisource.py (src/omnisource/, stdlib only)
            → feeds/*.json + apps/<slug>/ + api/*
            → scripts/build_site.py → _site/ → GitHub Pages
```

1. **Sync** — resolve newest release from declared upstream (GitHub / developer feed)
2. **Health** — probe every download URL
3. **Build** — render feeds, RSS, badges, intelligence docs and app pages
4. **Validate** — `ruff` + `scripts/validate.py` + `check_reproducible.py`
5. **Publish** — refresh `apps.json`, `/api/` and deploy

```bash
make build      # sync + health + build
make serve      # preview at http://localhost:8000
make check      # validate + tests
python3 scripts/omnisource.py --no-sync   # offline rebuild
```

Key paths: `catalog.json` source of truth · `src/omnisource/` pipeline · `scripts/` CLIs · `feeds/` output · `js/` + `assets/design-system/` frontend

---

## 🔌 API

Every build publishes `/api/` — `apps.json`, `catalog.json`, `health.json`, `analytics.json`, `install.json`, `search-index.json`, `sources.json` (Source Explorer contract v2: slug, page, status, reputation, health, cadence) and more, each with `.gz` and listed in `api/index.json`. Clients: [`sdk/javascript/`](sdk/javascript/) (install with
`npm i github:iamsmmh/OmniSource/sdk/javascript` — see its `package.json`) ·
[`sdk/python/`](sdk/python/) (`python3 -m pip install ./sdk/python`) — [API docs](docs/API.md)

Source-level data lives in [`feeds/sources.json`](feeds/sources.json) (schema v2: slug, page,
status, reputation, health, cadence per upstream) and is published as static pages under
[`sources/`](sources/) — generated by the build, so nothing there is hand-edited.

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Edit **`catalog.json`** only — never generated files. Run `python3 scripts/omnisource.py` and commit regenerated output.

[Request an app](https://github.com/iamsmmh/OmniSource/issues/new?template=01-app-request.yml) · [Broken upstream](https://github.com/iamsmmh/OmniSource/issues/new?template=02-broken-upstream.yml) · [Bug report](https://github.com/iamsmmh/OmniSource/issues/new?template=03-bug-report.yml) · [Feature idea](https://github.com/iamsmmh/OmniSource/issues/new?template=04-feature-idea.yml)

---

## ❓ FAQ

**Can I install two YouTube apps side by side?**
No — they share a bundle ID. Add only the one you want via its single-app feed. The [compare page](https://iamsmmh.github.io/OmniSource/compare/) helps you choose.

**How do updates work?**
Refresh sources in your client — upstreams sync every 6h. Or subscribe to `feeds/<slug>.xml`.

**What do the badges mean?**
Per app: 🟢 stable · 🟡 beta · 🔵 manual · 🔴 unmaintained — plus *Official* / *Community* build and ✅/⚠️ reachability.
Per source: **Verified** (valid feed, reachable, updated <180 days ago) · **Community Verified** · **Maintained** · **Warning** (broken entries/links/probes) · **Inactive** (no release in a year) · **Deprecated** (archived).

**Is this safe?**
Metadata only, every entry discloses provenance and hash. Sideloading trusts the app's developer — OmniSource just makes it transparent.

---

## ⚖️ License

Independent community project. Apps and trademarks belong to their owners. [GPL-3.0](LICENSE)

<div align="center">

⭐ **Star this repo if it makes sideloading easier** ⭐

[🌐 Website](https://iamsmmh.github.io/OmniSource/) · [📲 Install](https://iamsmmh.github.io/OmniSource/install/) · [🔌 API](docs/API.md)

</div>
