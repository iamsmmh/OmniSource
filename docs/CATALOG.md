# App Catalog

Live versions, sizes and link-health are in the [README table](../README.md#catalog) and on the
[website](https://iamsmmh.github.io/OmniSource/#/catalog). This page documents what each entry *is*,
who maintains it upstream, and how OmniSource obtains the build.

| App | Slug | Bundle ID | Upstream project | How OmniSource gets the build |
| --- | --- | --- | --- | --- |
| SpotiFLAC Mobile | `spotiflac` | `com.zarzet.spotiflac` | [spotiflacapp/SpotiFLAC-Mobile](https://github.com/spotiflacapp/SpotiFLAC-Mobile) | Newest published release asset |
| uYouEnhanced | `uyouenhanced` | `com.google.ios.youtube` | [arichornlover/uYouEnhanced](https://github.com/arichornlover/uYouEnhanced) | archive.org mirror of the upstream build; replaced by in-repo *Build uYouEnhanced* releases once they exist |
| YouTubePlus (YTLite) | `ytlite` | `com.google.ios.youtube` | [Dayanch96/YTLite](https://github.com/Dayanch96/YTLite) | `ytl-ipa*` tags in mrdrvt99/YouProEXTRA |
| YouPro | `youpro` | `com.google.ios.youtube` | [mrdrvt99/YouProEXTRA](https://github.com/mrdrvt99/YouProEXTRA) (original repo [deleted]; authored by [@Alibusut](https://github.com/alibusut)) | `youproextra-ipa*` tags in mrdrvt99/YouProEXTRA |
| YTKillerPlus | `ytkp` | `com.google.ios.youtube` | [iKarwan/YTKillerPlus](https://github.com/iKarwan/YTKillerPlus) | Developer's own AltStore source `repo.ikghd.me/repo.json`; the `ytkp-ipa*` build in mrdrvt99/YouProEXTRA stays configured as a mirror |
| YTKACE | `ytkace` | `com.google.ios.youtube` | [itzzace/ytkace](https://github.com/itzzace/ytkace) | Newest official release asset (`YTKACE_<version>_YouTube_<youtube>.ipa`); the separate `_iOS16_` build is filtered out |
| YouMod | `youmod` | `com.google.ios.youtube` | [mrdrvt99/YouMod](https://github.com/mrdrvt99/YouMod) | `youmod-ipa*` tags in mrdrvt99/YouProEXTRA |
| MaxTube | `maxtube` | `com.google.ios.youtube` | [Mark02-2012/YTPlusM](https://github.com/Mark02-2012/YTPlusM) | `YTPlusM_*` assets in Ashreq/ashstore-repo (GitHub mirror of the TubeVault build; upstream removed its own release assets) |
| YTMusicUltimate | `ytmusic` | `com.google.ios.youtubemusic` | [Dayanch96/YTMusicUltimate](https://github.com/Dayanch96/YTMusicUltimate) | Newest published release asset |
| MaxMusic | `maxmusic` | `com.google.ios.youtubemusic` | [Mark02-2012/YTMUltimatePLUS](https://github.com/Mark02-2012/YTMUltimatePLUS) | `MaxMusic_*` tags, full build (the `no_YMP` variant is filtered out) |
| UTM | `utm` | `com.utmapp.UTM` | [utmapp/UTM](https://github.com/utmapp/UTM) | Newest published release asset (`UTM.ipa`, universal build) |
| iNKillerPlus | `inkillerplus` | `com.burbn.instagram` | [iKarwan/iNKillerPlus](https://github.com/iKarwan/iNKillerPlus) | Developer's own AltStore source `repo.ikghd.me/repo.json` |
| TTKillerPlus | `ttkillerplus` | `com.zhiliaoapp.musically` | [iKarwan/TTKillerPlus](https://github.com/iKarwan/TTKillerPlus) | Developer's own AltStore source `repo.ikghd.me/repo.json` |
| Winston | `winston` | `lo.cafe.winston` | [lo-cafe/winston](https://github.com/lo-cafe/winston) | Newest published release asset (`winston.ipa`) |
| iTorrent | `itorrent` | `com.xitrix.iTorrent2` | [XITRIX/iTorrent](https://github.com/XITRIX/iTorrent) | Newest published release asset (`iTorrent.ipa`) |
| StikDebug | `stikdebug` | `com.stik.stikdebug` | [StikDebug/StikDebug](https://github.com/StikDebug/StikDebug) | Newest published release asset (`StikDebug-<version>.ipa`) |
| BHTwitter | `bhtwitter` | `com.atebits.Tweetie2` | [BandarHL/BHTwitter](https://github.com/BandarHL/BHTwitter) | Newest release asset ending in `-sideloaded.ipa` (the TrollStore `.tipa` is skipped) |
| LiveContainer | `livecontainer` | `com.kdt.livecontainer` | [LiveContainer/LiveContainer](https://github.com/LiveContainer/LiveContainer) | Newest stable `LiveContainer.ipa` (the `+SideStore` bundle and the rolling `nightly` pre-release are skipped) |
| Feather | `feather` | `thewonderofyou.Feather` | [claration/Feather](https://github.com/claration/Feather) | Newest published release asset (`Feather.ipa`) |
| SideStore | `sidestore` | `com.SideStore.SideStore` | [SideStore/SideStore](https://github.com/SideStore/SideStore) | Newest stable release asset (`SideStore.ipa`); the `nightly`/`alpha` tags are pre-releases and are skipped |
| Aidoku | `aidoku` | `app.aidoku.Aidoku` | [Aidoku/Aidoku](https://github.com/Aidoku/Aidoku) | Newest published release asset (`Aidoku.ipa`) |
| Provenance | `provenance` | `org.provenance-emu.provenance` | [Provenance-Emu/Provenance](https://github.com/Provenance-Emu/Provenance) | Newest stable release asset ending in `-iOS.ipa` (tvOS build and the rolling `alpha` pre-release are skipped) |

## Status labels

| Label | Meaning |
| --- | --- |
| `stable` | Tracked automatically, upstream is actively releasing |
| `beta` | Tracked, but upstream marks the build as experimental |
| `manual` | Published by a maintainer rather than resolved from an upstream release |
| `unmaintained` | Upstream has stopped releasing; kept for existing users |
| `deprecated` | Scheduled for removal; do not install |

## Verification methods

| Method | Meaning |
| --- | --- |
| `github-release` | The IPA is served straight from the upstream project's GitHub release asset |
| `self-built` | Compiled by an OmniSource workflow; the release notes publish a SHA-256 |
| `altstore` | Resolved from the developer's own AltStore-compatible source document |
| `json-feed` / `feather` | Resolved from another publisher-controlled JSON feed |
| `manual-mirror` | A maintainer-hosted mirror; least verifiable, used only as a fallback |

Nothing is pre-signed. `codeSigned: false` on every entry means you sign with your own certificate.

## Fallback mirrors

Apps whose primary host is a shortener or a third-party mirror can declare one or more
`fallbackDownloadURLs` in `catalog.json`:

```json
{
  "slug": "example",
  "name": "Example App",
  "downloadURL": "https://primary.example.com/example.ipa",
  "fallbackDownloadURLs": [
    "https://mirror.example.com/example.ipa"
  ]
}
```

Mirrors are ordered — the first reachable one wins. They are probed by
`scripts/health_check.py` (and the daily `health-check.yml` workflow) and surfaced on the website as
alternative download links, so an app stays installable when its primary link goes down. A
`manualRelease` may declare its own mirrors to override the app-level list for a specific build.

> **Note:** the uYouEnhanced entry currently resolves directly through the archive.org mirror of
> the upstream build (no shortener in the chain). Its `upstream` block points at this repository's
> own `uyouenhanced-v*` releases, so the first successful *Build uYouEnhanced* run swaps in a
> first-party URL automatically.

## Why some entries are not resolved from the upstream project

Every entry is pointed at the most authoritative source that actually publishes an installable IPA.
For several YouTube tweaks that is *not* the upstream repository, because the developer only ships
the jailbreak `.deb` (or nothing at all) and a third party does the sideload build:

| App | Upstream publishes | Where OmniSource has to look instead |
| --- | --- | --- |
| YouTubePlus (YTLite) | `.deb` only — Dayanch96 removes IPAs for legal reasons | `ytl-ipa*` builds in mrdrvt99/YouProEXTRA |
| YTMusicUltimate | `.deb` only (Dayanch96/YTMusicUltimate) | mrdrvt99/YTMusicUltimate IPA builds |
| MaxTube (YTPlusM) | Releases deleted upstream (`NO_MORE_RELEASE_HERE`) | `YTPlusM_*` assets in Ashreq/ashstore-repo |
| uYouEnhanced | Nothing — IPAs were pulled after DMCA takedowns, upstream is DIY-build only | this repository's own `Build uYouEnhanced` workflow, with an archive.org mirror until the first run |
| YouPro | Upstream repository deleted | `youproextra-ipa*` builds by mrdrvt99 |
| YouMod | `youmod-ipa3` (behind: YouTube 21.24.3) | `youmod-ipa*` builds in mrdrvt99/YouProEXTRA by the same author, kept current |

If any of these projects starts publishing IPAs itself, switching is a one-line change to the
`upstream` block in `catalog.json`.

## Large downloads

`provenance` ships every emulator core in one IPA, so the download is roughly 1 GB. Sign and install it
over Wi-Fi, and expect on-device signing (Feather, SideStore, ESign) to take several minutes.

## Shared apps note

Seven YouTube mods share the bundle identifier `com.google.ios.youtube`. iOS treats bundle IDs as
unique per device, so **you can only have one of them installed at a time** unless your client
rewrites the bundle ID (Feather and LiveContainer can; AltStore and SideStore cannot by default).
The same applies to the two YouTube Music mods (`com.google.ios.youtubemusic`): MaxMusic and
YTMusicUltimate cannot coexist.

## Credits

| Project | Maintainers |
| --- | --- |
| SpotiFLAC Mobile | [@spotiflacapp](https://github.com/spotiflacapp) |
| uYouEnhanced | [@arichornlover](https://github.com/arichornlover), [@MiRO92](https://github.com/MiRO92), [@qnblackcat](https://github.com/qnblackcat) |
| YTLite / YTMusicUltimate | [@Dayanch96](https://github.com/Dayanch96) |
| YTKACE | [@itzzace](https://github.com/itzzace) |
| YouPro | [@Alibusut](https://github.com/alibusut) (repo deleted; builds via [@mrdrvt99](https://github.com/mrdrvt99)) |
| YouMod / release mirroring | [@mrdrvt99](https://github.com/mrdrvt99) |
| MaxTube / MaxMusic | [@Mark02-2012](https://github.com/Mark02-2012) |
| YTKillerPlus / iNKillerPlus / TTKillerPlus | [@iKarwan](https://github.com/iKarwan) |
| Winston | [@lo-cafe](https://github.com/lo-cafe) ([@Kinark](https://github.com/Kinark)) |
| iTorrent | [@XITRIX](https://github.com/XITRIX) |
| StikDebug | [@StikDebug](https://github.com/StikDebug) ([@StephenDev0](https://github.com/StephenDev0)) |
| BHTwitter | [@BandarHL](https://github.com/BandarHL) |
| LiveContainer | [@khanhduytran0](https://github.com/khanhduytran0) and the LiveContainer team |
| Feather | [@khcrysalis](https://github.com/khcrysalis) / Samara |
| SideStore | [SideStore team](https://github.com/SideStore) |
| Aidoku | [@Skittyblock](https://github.com/Skittyblock) |
| Provenance | [Provenance-Emu team](https://github.com/Provenance-Emu) |

OmniSource maintenance: [@iamsmmh](https://github.com/iamsmmh). Thanks to
[@MountainofPenguin](https://github.com/MountainofPenguin), [@HakujouSan](https://github.com/HakujouSan)
and [@Avieshek](https://github.com/Avieshek) for architecture input, testing and manifest work.
