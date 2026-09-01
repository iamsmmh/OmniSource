# Installation Guide

OmniSource publishes an AltStore-compatible feed. Any client that understands that format can
subscribe to it.

## Master feed

```
https://iamsmmh.github.io/OmniSource/apps.json
```

One-tap links:

- AltStore — `altstore://source?url=https://iamsmmh.github.io/OmniSource/apps.json`
- SideStore — `sidestore://source?url=https://iamsmmh.github.io/OmniSource/apps.json`
- Feather — `feather://source/iamsmmh.github.io/OmniSource/apps.json`

Prefer a single app? Every app also publishes its own feed at
`https://iamsmmh.github.io/OmniSource/<slug>.json` — the slugs are listed in the README table and on
the [website](https://iamsmmh.github.io/OmniSource/#/install).

## AltStore

1. Install AltStore on your device using AltServer on a Mac or PC.
2. Open AltStore → **Browse** → **Sources**.
3. Tap **+**, paste the master feed URL, confirm.
4. Open the source and tap **FREE** next to any app.

Free Apple IDs are limited to three sideloaded apps and a seven-day signature. AltStore refreshes
apps while AltServer is reachable on the same network.

## SideStore

1. Pair SideStore with your device and confirm your anisette server is reachable.
2. Open **Browse** → **Sources** → **Add Source**.
3. Paste the master feed URL.
4. Install any app; SideStore can refresh in the background over Wi-Fi.

## Feather

1. Open Feather → **Sources**.
2. Tap **+** and paste the master feed URL.
3. Choose an app, then **Sign and Install** using your own certificate.

Feather requires a valid signing certificate. Developer and enterprise certificates both work;
free Apple IDs are subject to the same three-app limit.

## ESign

1. Open ESign → **Sources** → **Add**.
2. Paste the master feed URL.
3. Download the IPA, sign it with your certificate, then install.

## LiveContainer

1. Download the IPA from the app page (or from another client that added the source).
2. In LiveContainer tap **+** and select the IPA.
3. Launch the app inside LiveContainer — it does not consume a separate app slot.

LiveContainer works best with apps that do not require entitlements the container cannot provide.
Check the app's **Compatibility** panel on the website before installing.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Source adds but shows no apps | Client cached an old response | Pull to refresh, or remove and re-add the source |
| "Unable to download app" | Upstream release asset moved or was deleted | Check the [health dashboard](https://iamsmmh.github.io/OmniSource/#/health); open an issue if it stays red |
| App installs then crashes on launch | Tweak incompatible with your iOS version | Compare `minOSVersion` on the app page with your device |
| "Maximum number of apps installed" | Free Apple ID three-app limit | Remove a sideloaded app, or use a paid developer account |
| Signature expired after 7 days | Free Apple ID certificate lifetime | Refresh in your client before day seven |

Nothing in this repository is pre-signed. You always sign with your own certificate or Apple ID —
see each app's **Verification** panel for how its build is sourced.
