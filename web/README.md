# OmniSource Web — modern website (Next.js 15 + TypeScript + Tailwind PWA)

The modern companion to the zero-dependency static site at the repository
root (which keeps deploying to GitHub Pages unchanged). This app adds
server rendering, a dynamic REST API, 8-locale i18n and installable-PWA
offline support.

## Routes

| Route | Page |
|---|---|
| `/` | Home (hero, client deep-links, stats, status) |
| `/apps` + `/apps/[id]` | Catalog with category/sort filters + app detail |
| `/sources` + `/sources/[id]` | Source explorer with reputation + health |
| `/collections` | Curated collections |
| `/categories` | Category browser |
| `/trending` | Trending / rising / recently updated |
| `/search` | Fuzzy multi-field search (ranking, filters, sorting) |
| `/status` | Source/download availability board |
| `/security` | Security posture (verdict, findings, dup binaries) |
| `/statistics` | Daily / weekly / monthly analytics windows |
| `/about` | Project overview + pipeline |
| `/api/v3/*` | Dynamic REST API (see `docs/API-V3.md`) |

## Data flow

`prebuild` / `predev` run `scripts/sync-data.mjs`, which copies the
pipeline outputs into `web/`:

- `src/data/*.json` — server-bundled snapshots (`../feeds`, `../data`)
- `public/data/v3/*.json` — client-fetchable API snapshot (search, PWA)

The app therefore builds and runs anywhere without reaching outside its
own directory.

## Develop

```bash
cd web
npm install
npm run dev        # http://localhost:3000
npm run typecheck
npm run lint
npm run build && npm start
```

## API v3 (dynamic)

`src/app/api/v3/[...route]/route.ts` implements the full contract:

- `GET /api/v3/apps?page=2&per_page=20&sort=-versionDate&category=Games&q=youtube`
- `GET /api/v3/apps/{id}`, `/sources`, `/sources/{id}`, `/trending`,
  `/search?q=…`, `/status`, `/security`, `/analytics`, `/releases`
- Pagination envelopes, `sort`/`-sort`, `ETag` + `304` conditional
  responses, `Cache-Control: s-maxage=300, stale-while-revalidate=3600`
  (Next.js compresses gzip/brotli automatically).

## i18n

English, Bangla, Arabic, Spanish, French, German, Japanese, Chinese.
Dictionaries load lazily per locale (`src/i18n/locales/*.ts`), fall back
to English, and render from the `omnisource-lang` cookie on the server so
hydration never mismatches. RTL is enabled automatically for Arabic.

## PWA

`manifest.webmanifest` + `sw.js` (cache-first shell/data, network-first
API) registered in production only (`PwaRegister`).

## Deploy

Any Node host (Vercel, Cloudflare, self-hosted `npm run build && npm start`).
`output: "export"` static hosting is possible but disables the query-string
API semantics (use the pre-rendered `/api/v3/*.json` + `/data/v3/*.json`
snapshots instead).
