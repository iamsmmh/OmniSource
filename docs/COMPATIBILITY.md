# Compatibility Guide

Compatibility is declared per app in `catalog.json` under `compatibility` and rendered as a live
matrix on the [website](https://iamsmmh.github.io/OmniSource/#/compatibility).

```json
"compatibility": {
  "minOSVersion": "16.0",
  "maxOSVersion": null,
  "devices": ["iphone", "ipad"],
  "clients": ["altstore", "sidestore", "feather", "esign", "livecontainer"],
  "notes": ""
}
```

| Field | Meaning |
| --- | --- |
| `minOSVersion` | Lowest iOS version the build runs on. Mirrored into every `versions[]` entry. |
| `maxOSVersion` | `null` when there is no known ceiling; set when a tweak breaks on newer iOS. |
| `devices` | `iphone`, `ipad`, or both. Apple Silicon Macs follow the iPad entry. |
| `clients` | Client IDs the build is confirmed to work with. Absence means *untested*, not *broken*. |
| `notes` | Free text shown on the app page — use it for caveats. |

## Client capabilities

| Capability | AltStore | SideStore | Feather | ESign | LiveContainer |
| --- | :-: | :-: | :-: | :-: | :-: |
| Reads AltStore feeds | ✅ | ✅ | ✅ | ✅ | ➖ |
| Signs on device | ➖ | ✅ | ✅ | ✅ | ➖ |
| Needs a desktop helper | ✅ | ➖ | ➖ | ➖ | ➖ |
| Background refresh | ✅ | ✅ | ➖ | ➖ | ➖ |
| Bundle-ID rewriting | ➖ | ➖ | ✅ | ✅ | ✅ |
| Runs without an app slot | ➖ | ➖ | ➖ | ➖ | ✅ |

➖ = not applicable or not provided by the client.

## Practical limits

- **Free Apple ID:** three sideloaded apps, seven-day signature, no push notifications or
  app-group entitlements. All YouTube mods here request app groups, so some features degrade.
- **Paid developer account:** ten apps, one-year certificate.
- **Duplicate bundle IDs:** the seven YouTube mods all use `com.google.ios.youtube`, and MaxMusic
  shares `com.google.ios.youtubemusic` with YTMusicUltimate. Install one of each family at
  a time, or use a client that rewrites bundle IDs.
- **Entitlements:** entries list what the IPA requests under `appPermissions`. A client that cannot
  grant an entitlement will strip it, and the corresponding feature stops working.

## Reporting a result

Compatibility data is community-sourced. If you confirm or disprove a combination, open an issue
with your device, iOS version, client, app and version. Confirmed results are merged into
`catalog.json` and appear in the matrix on the next build.
