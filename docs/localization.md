# Localization

OmniSource uses static JSON locales and the dependency-free runtime at `src/js/i18n.js`; no server or framework is required. English (`locales/en.json`) is canonical.

## Adding a locale

1. Copy `locales/en.json` to `<language>.json` and translate every value.
2. Add the language to `supported` in `src/js/i18n.js` and, if RTL, to `RTL`.
3. Run `node scripts/validate-translations.js`. It writes `api/translation-status.json` and fails on invalid JSON, duplicate keys, empty values, or missing canonical keys.

Locale URLs are resolved under `/OmniSource` on GitHub Pages and relative to the origin elsewhere. The service worker precaches the locale files for offline/PWA use. The runtime persists the selected language in `localStorage` under `language`, then uses the browser language and English as fallbacks. Missing keys warn in development and return the key rather than rendering an empty label.

Use `data-i18n="nav.compare"` and `data-i18n-placeholder="common.search"` for new visible strings. Use `window.OmniI18n.t(key)` for dynamic UI. RTL is applied automatically with `dir="rtl"`.

## Audit (2026-09-11)

The repository had an inline, partial English/Spanish dictionary in `js/features.js`, with no locale directory, validation gate, coverage artifact, or sub-path-aware locale fetch. The canonical catalog now contains eight locales (English, Spanish, French, German, Arabic, Bengali, Chinese, and Japanese), all at 100% coverage. The runtime and service worker use the GitHub Pages base path and retain the existing static/PWA architecture.
