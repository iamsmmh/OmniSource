# Performance report

**Assessment date:** 2026-09-12
**Target:** at least 1,000 monitored sources, 10,000 applications, and
100,000 requests/day without rebuilding unchanged catalog records.

## Design

- Provider HTTP uses retries with exponential backoff, conditional cache
  headers, capped response bodies, and host-scoped connection policy.
- `src/omnisource/async_http.py` exposes one async API. It uses an
  `aiohttp` `TCPConnector` pool when available and a bounded stdlib thread
  fallback otherwise.
- Monitoring uses bounded concurrency and probes HEAD first, falling back to a
  one-byte/ranged GET rather than downloading IPA payloads.
- JSON output uses stable serialization and content comparison; volatile
  timestamps do not create empty commits.
- Release history is append-only, but feeds are projected from changed app
  records. Static API snapshots are paginated in v3 and cacheable with ETags.
- Search builds a field-weighted index once and performs bounded fuzzy ranking;
  the client supports source/developer/category/tag filters.
- Images and feeds have cacheable static URLs, gzip twins, PWA caching, and
  lazy locale loading.

## Build complexity

| Stage | Current approach | Scale behavior |
|---|---|---|
| Discovery | bounded pages per search term + dedupe by URL | shard terms/pages at high rate limits |
| Validation | linear records, bounded app checks | O(sources + apps) |
| Canonicalization | indexed identity keys with union-like grouping | O(records × identity signals) |
| Release history | append/merge by release key | O(releases) per changed app |
| Monitoring | bounded concurrent source/download probes | O(targets / workers) wall time |
| Search | prebuilt tokens + weighted fuzzy candidates | bounded by index candidates and limit |
| Website | static snapshots + server-rendered Next.js routes | CDN/cache friendly |

## Measurement procedure

Run the offline suite and inspect generated report sizes:

```bash
python3 -m unittest discover -s tests
python3 scripts/audit.py --only perf
python3 scripts/check_reproducible.py --diff
```

The audit writes raw/gzip JSON weights, image sizes, service-worker cache
coverage, script loading, and budget observations to `reports/performance.md`.
Live latency and uptime are intentionally recorded by `data/status.json` and
not fabricated in this document.

## Operational limits

- GitHub API rate limits are the first likely ceiling for discovery. Use a
  token only for GitHub API hosts and respect `Retry-After`.
- The stdlib fallback has no shared HTTP connection pool; install the optional
  async HTTP dependency for high-volume monitoring deployments.
- GitHub Pages is a static origin. Dynamic API filtering is available on a
  Node deployment; Pages clients use generated v3 snapshots.
- IPA binary verification is intentionally opt-in because it consumes network,
  disk, and runner time. Regular monitoring probes do not fetch payloads.
- The checked-in catalog is small today, so benchmark results at 10,000 apps
  must be measured in the target deployment rather than inferred from the
  current checkout.
