# App Catalog

Live versions, sizes and link-health are in the [README table](../README.md#catalog) and on the
[website](https://iamsmmh.github.io/OmniSource/#/catalog). This page documents what each entry *is*,
who maintains it upstream, and how OmniSource obtains the build.

| App | Slug | Bundle ID | Upstream project | How OmniSource gets the build |
| --- | --- | --- | --- | --- |
| SpotiFLAC Mobile | `spotiflac` | `com.zarzet.spotiflac` | [spotiflacapp/SpotiFLAC-Mobile](https://github.com/spotiflacapp/SpotiFLAC-Mobile) | Newest published release asset |
| uYouEnhanced | `uyouenhanced` | `com.google.ios.youtube` | [arichornlover/uYouEnhanced](https://github.com/arichornlover/uYouEnhanced) | Built in-repo by the *Build uYouEnhanced* workflow |
| YouTubePlus (YTLite) | `ytlite` | `com.google.ios.youtube` | [Dayanch96/YTLite](https://github.com/Dayanch96/YTLite) | `ytl-ipa*` tags in mrdrvt99/YouProEXTRA |
| YouPro | `youpro` | `com.google.ios.youtube` | [Alibusut/YouPro](https://github.com/Alibusut/YouPro) | `youproextra-ipa*` tags in mrdrvt99/YouProEXTRA |
| YTKillerPlus | `ytkp` | `com.google.ios.youtube` | [IKillerApp/YTKillerPlus](https://github.com/IKillerApp/YTKillerPlus) | `ytkp-ipa*` tags in mrdrvt99/YouProEXTRA |
| YTKACE | `ytkace` | `com.google.ios.youtube` | [itzzace/YTKACE](https://github.com/itzzace/YTKACE) | `ytkace-ipa*` tags in mrdrvt99/YouProEXTRA |
| YouMod | `youmod` | `com.google.ios.youtube` | [mrdrvt99/YouMod](https://github.com/mrdrvt99/YouMod) | `youmod-ipa*` tags in mrdrvt99/YouProEXTRA |
| YTMusicUltimate | `ytmusic` | `com.google.ios.youtubemusic` | [Dayanch96/YTMusicUltimate](https://github.com/Dayanch96/YTMusicUltimate) | Newest published release asset |
| UTM | `utm` | `com.utmapp.UTM` | [utmapp/UTM](https://github.com/utmapp/UTM) | Newest published release asset (`UTM.ipa`, universal build) |

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

> **Note:** the uYouEnhanced entry currently resolves through a `tinyurl.com` shortener. Its
> `upstream` block points at this repository's own `uyouenhanced-v*` releases, so the first
> successful *Build uYouEnhanced* run replaces the shortener with a first-party URL automatically.

## Shared apps note

Five YouTube mods share the bundle identifier `com.google.ios.youtube`. iOS treats bundle IDs as
unique per device, so **you can only have one of them installed at a time** unless your client
rewrites the bundle ID (Feather and LiveContainer can; AltStore and SideStore cannot by default).

## Credits

| Project | Maintainers |
| --- | --- |
| SpotiFLAC Mobile | [@spotiflacapp](https://github.com/spotiflacapp) |
| uYouEnhanced | [@arichornlover](https://github.com/arichornlover), [@MiRO92](https://github.com/MiRO92), [@qnblackcat](https://github.com/qnblackcat) |
| YTLite / YTMusicUltimate | [@Dayanch96](https://github.com/Dayanch96) |
| YTKACE | [@itzzace](https://github.com/itzzace) |
| YouPro | [@Alibusut](https://github.com/Alibusut) |
| YTKillerPlus | [@IKillerApp](https://github.com/IKillerApp) |
| YouMod / release mirroring | [@mrdrvt99](https://github.com/mrdrvt99) |

OmniSource maintenance: [@iamsmmh](https://github.com/iamsmmh). Thanks to
[@MountainofPenguin](https://github.com/MountainofPenguin), [@HakujouSan](https://github.com/HakujouSan)
and [@Avieshek](https://github.com/Avieshek) for architecture input, testing and manifest work.
