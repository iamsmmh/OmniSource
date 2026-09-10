# Sourcing report — RyukSign and Senumy IPA libraries

Sweep date: 2026-09-10. Sources reviewed: [store.ryuksign.com](https://store.ryuksign.com/)
(and its AltStore sources under `source.ryuksign.com`) and
[senumy.com/ipa-library](https://senumy.com/ipa-library/) plus its
jailbreak / emulator / tweaks / third-party-store / IPA-installer sub-pages.

**14 apps were added** (catalog grew from 49 to 63). Everything else on those pages
was skipped; the reasons are below, grouped by cause. This report is the record of
the inclusion rule that was applied.

## Inclusion rule

1. **The release must come from the app's own developer or project** — their GitHub
   Releases, their own AltStore/Feather source, or a clearly-labelled community build
   (`status: "manual"` + `verification.method: "manual-mirror"`). Third-party
   re-uploads, aggregator mirrors and account-gated download pages do not qualify.
2. **The upstream must publish an installable artifact** — a `.ipa` or `.tipa`.
   Cydia/Sileo `.deb` packages, `.tar` installers, App Store listings, macOS-only
   builds and web-based tools are not catalogued.
3. **The app must still be usable**: actively maintained, or, where a project has
   stopped, the final upstream build must still be the canonical tool for the
   firmware it targets (recorded as `status: "unmaintained"`).
4. **The target firmware must overlap what the catalog's install clients support.**
   AltStore needs iOS 12.2 or later, so a tool whose entire range predates those
   clients cannot be installed from an AltStore-family feed.
5. **No duplicates.** When one source publishes several builds of the same product
   with the same or colliding bundle identifiers, the canonical build is included and
   the near-identical variants are folded; where two distinct apps do ship the same
   bundle ID, each declares `alternativeTo`.

## Added

| Slug | App | Found on | Release source |
| --- | --- | --- | --- |
| `ryukgram` | RyukGram | RyukSign | `source.ryuksign.com/plugins` (developer's own AltStore source) |
| `ryukgram-ig410` | RyukGram (IG 410) | RyukSign | `source.ryuksign.com/ig410` |
| `ryukgram-sidebyside` | RyukGram Side by Side | RyukSign | `source.ryuksign.com/duplicate` |
| `dopamine` | Dopamine | Senumy · Jailbreak | `opa334/Dopamine` GitHub Releases |
| `dopamine-roothide` | Dopamine (RootHide) | Senumy · Jailbreak | `roothide/Dopamine2-roothide` |
| `bootstrap` | Bootstrap | Senumy · Jailbreak | `roothide/Bootstrap` |
| `serotonin` | Serotonin | Senumy · Jailbreak | `mineek/Serotonin` (final build, `unmaintained`) |
| `taurine` | Taurine | Senumy · Jailbreak | `Odyssey-Team/Taurine` (final build, `unmaintained`) |
| `odyssey` | Odyssey | Senumy · Jailbreak | `Odyssey-Team/Odyssey` (final build, `unmaintained`) |
| `unc0ver` | unc0ver | Senumy · Jailbreak | `pwn20wndstuff/Undecimus` (final build, `unmaintained`) |
| `sameboy` | SameBoy | Senumy · Emulator | `LIJI32/SameBoy` GitHub Releases |
| `manicemu` | Manic EMU | Senumy · Emulator | `Manic-EMU/ManicEMU` GitHub Releases |
| `xenios` | XeniOS | Senumy · Emulator | `xenios-jp/XeniOS` GitHub Releases |
| `gopeed` | Gopeed (iOS) | Senumy · Tweaks | `GopeedLab/gopeed` GitHub Releases |

The unmaintained jailbreaks are kept deliberately: Taurine (iOS 14.0–14.3), Odyssey
(iOS 13.0–13.7) and unc0ver (iOS 11.0–14.8.1) are the last official builds for
firmware no maintained tool covers, and Serotonin (iOS 16.5.1–16.7 RC / 17.0) covers
part of a range Dopamine releases only partly overlap. Everything else that was added
is on a live release line.

## Skipped

### RyukSign variants folded into the three entries above

* `source.ryuksign.com/` (root) — the same RyukGram build, bundle and IPA URL as
  `/duplicate`; `/duplicate` was catalogued as Side by Side.
* `/noplugins`, `/ig410-noplugins`, `/ig410-duplicate` — the same RyukGram product
  with the plugin loader disabled or on a different Instagram base; identical or
  colliding bundle IDs with the builds already included.
* The `/apt/` repository (`com.faroukbmiled.ryukgram` 1.4.0 and `.legacy` 1.3.3) —
  Cydia/Sileo `.deb` packages for jailbroken devices, not AltStore apps.

### Senumy's own storefront and library list — no official upstream

SenIPA, Velixa, AppleJr, MapleSign, IPA Installer, JBIPAs, Sileem, zJailbreak,
Cydia 2, Redensa, AppleGPT, Safari 3DX, Apple AI Search, Emula, Zentify, CoolStore,
TutuPro, Panda Helper, iOSGods, iOS Ninja, AppValley, Ela Themes, Android on iOS,
ryOS, Scylla, Scarlet, TutuBox. These are third-party stores/tools whose only
downloads are re-uploads on `apps.senumy.com` / `members.senumy.com` behind a free
account — nothing to sync from, and out of scope under rule 1.

### Jailbreak tools without an official installable IPA

* **`.deb` / tool-only:** palera1n (verified: `.deb` only), checkra1n (macOS tool /
  `.deb`), Manticore Web (web-based), Fugu15 Max (superseded by Dopamine); the
  remaining Cydia-era packages (Rootless, OdysseyRa1n, Ra1ncloud, Flux6, Socket)
  ship from third-party repos rather than an app release.
* **Upstream gone or unfindable:** NekoJB, XinaA15, KFDmineek, Cherimoya,
  Meow/MEOWBREK2, Freya15, Relaxin (no release assets), NathanLR (no release assets;
  only an unofficial fork ships a `.tipa`).
* **Superseded or dormant:** u0Launcher (2022 launcher helper), Od1n (official IPA,
  but dormant since 2024-07 and its iOS 15.0–16.6.1 range is covered by the maintained
  Dopamine builds), SaiGon15 (only forks remain), CanYouJB (small unofficial-range
  utility), Xinam1ne (no IPA assets published).
* **Legacy Cydia-Impactor era (iOS ≤ 12):** Electra, Chimera, Meridian, Saigon,
  Yalu102, H3lix, DoubleH3lix, g0blin, Pangu, Kok3shi9, LiberiOS, p0insettia, Phoenix,
  Home Depot, EverPwnage (iOS 7.0–9.3.6) and the rest of the 32-bit line — their
  original download pages are gone and their firmware floor predates the install
  clients this catalog serves (rule 4).

### Emulators without an official IPA, or abandoned

Play!, Flycast, GearBoy, Folium — upstream releases ship no `.ipa`. iPSX2, Limón,
iSSB, GamePad — no official upstream found. GC4iOS (last commit 2018), SNES4iOS
(2012), iDOS (2020) — abandoned, and `litchie/dospad` is the only copy left.
iNDS — official IPA exists, but the project stopped in March 2021 and has no known
compatibility with current firmware. MeloNX — the upstream repository is gone; only a
0-star fork remains. iGBA, GBA Emu, iMAME, Snake '97 — App Store apps with no
sideloadable source. Happy Chick — third-party store.

### Tweaks — `.deb` / dylib-only, paid, or App Store

Watusi, Infuse Plus, CrackerXI+, CyDown, Power Selector, Spotify Plus, Chroma Hue,
iTransmission, StoreControl, Enmity (repository has no release assets), Facebook
(NoAds), Violyn, Instagram Plus, VideoStar++, ScreenshotX, CPU-X (repository gone),
OldOS (repository gone), Countdown-App — as published by their upstreams these are
Cydia/Sileo packages or paid tweaks rather than standalone IPAs, and no official
`.ipa` could be located for them. YouTube Reborn was checked directly: every release
carries only `.deb` assets. AdGuard, Loon, Widgy, Keka — App Store /
macOS products.

### Already in the catalog before this sweep

Delta, Provenance, PPSSPP, UTM, DolphiniOS, iTorrent, Aidoku, SideStore and uYou+
(the `uyouenhanced` entry) appear on the same Senumy pages but were already curated,
from their own upstreams.

### Unresolvable

Misaka (listed in the Senumy library) — the upstream repository is a static product
site with no releases or IPA, and no authoritative bundle identifier could be
established, so the entry cannot be authored from an official source.

## Notes on the two sites

* **RyukSign** is one developer's AltStore source hub. Three of its seven feed
  variants were catalogued; the rest are near-identical builds of the same app. All
  three entries resolve from `source.ryuksign.com` itself, and the catalog keeps a
  `manualRelease` snapshot so the apps stay installable when the source is down.
* **Senumy** is a directory of IPA stores, not a publisher. None of its cards link to
  an upstream release; every download routes through Senumy's own account-gated
  mirrors. Nothing was taken from those mirrors — the 11 Senumy-found apps were
  re-sourced from each project's own GitHub releases, and everything without such a
  source was skipped.
