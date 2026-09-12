# Localization

OmniSource uses static JSON locales and the dependency-free runtime at `src/js/i18n.js`; no server or framework is required. English (`locales/en.json`) is canonical.

## Adding a locale

1. Copy `locales/en.json` to `<language>.json` and translate every value.
2. Add the language to `supported` in `src/js/i18n.js` and, if RTL, to `RTL`.
3. Rebuild the generated documents (`python3 scripts/omnisource.py --no-sync --no-health`) and commit `feeds/translation-status.json` plus its `api/` mirror — the build owns that document; CI never writes it.
4. Run `node scripts/validate-translations.js`. It verifies the committed coverage document still matches the locale state and fails on invalid JSON, duplicate keys, empty values, or missing canonical keys.

Locale URLs are resolved under `/OmniSource` on GitHub Pages and relative to the origin elsewhere. The service worker precaches the locale files for offline/PWA use. The runtime persists the selected language in `localStorage` under `language`, then uses the browser language and English as fallbacks. Missing keys warn in development and return the key rather than rendering an empty label.

Use `data-i18n="nav.compare"` and `data-i18n-placeholder="common.search"` for new visible strings. Use `window.OmniI18n.t(key)` for dynamic UI. RTL is applied automatically with `dir="rtl"`.

## Coverage contracts (enforced by `tests/test_translations.py`)

1. **Parity:** every locale carries exactly the key set of `en.json` (11 groups, 100%), and
   `${placeholder}` sets must match per key. `scripts/validate-translations.js` checks the same
   in CI; `feeds/translation-status.json` publishes the numbers and is owned by the build.
2. **Live usage:** every key referenced by a page must exist in `en.json`, and every key in
   `en.json` must be referenced. The scanner reads `data-i18n*` attributes, `t()`/`translate()`
   calls in `js/*.js`, `js/modules/*.js`, `src/js/*.js` and inline page scripts, plus
   `<!-- i18n-keys: a.b, c.d -->` markers.
3. **Markers:** strings that only *generated* or *module-rendered* markup shows (nav links in
   `apps/**`, `sources/**`, sparkline labels) declare their keys with an `i18n-keys` comment on
   the page or generator, so nothing can become a dead key by moving markup between layers.
4. **Navigation:** the header IA (Home · Apps · Collections · Sources · Status · Docs, with
   Analytics · Compare · Favorites · Discover · Community · … behind "More") is translated in
   all eight locales on *every* hand-maintained and generated page, so switching language
   localizes the entire chrome, not just the home page.

## Audit (2026-09-11)

The repository had an inline, partial English/Spanish dictionary in `js/features.js`, with no locale directory, validation gate, coverage artifact, or sub-path-aware locale fetch. The canonical catalog now contains eight locales (English, Spanish, French, German, Arabic, Bengali, Chinese, and Japanese), all at 100% coverage. The runtime and service worker use the GitHub Pages base path and retain the existing static/PWA architecture.
