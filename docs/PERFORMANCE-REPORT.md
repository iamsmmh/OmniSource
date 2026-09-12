# Performance Report — OmniSource 3.2.0

Targets: **1,000+ sources / 10,000+ applications** with minimal API usage.

## Architecture for scale

| Layer | Mechanism |
|---|---|
| Sync | Incremental mode (`--incremental` skips pagination when the newest asset URL is unchanged) + `.cache/omnisource` HTTP cache shared across runs |
| Probing | Thread-pool concurrency (default 16–32 workers), HEAD-first with GET fallback, 3xx-without-follow for release hosts (no IPA streaming into the runner) |
| Bulk fetch | `src/omnisource/async_http.py` — asyncio + optional `aiohttp` connection pooling (keep-alive, DNS cache, bounded connector); stdlib `to_thread` fallback with semaphore when aiohttp is absent |
| Payload caps | 2 MB feed cap, 1 MB HTML cap, 4 KB probe reads — a hostile host cannot exhaust the runner |
| Writes | Content-stable writers (`write_json_stable`) — unchanged documents are not rewritten, so scheduled runs don't churn git or CDN caches |
| API | Static pre-render + `s-maxage`/`stale-while-revalidate`, ETag/`304`, per-document checksums for conditional refresh |

## Measured (2026-09-12, this checkout)

- Full unit suite: **328 tests in ~6 s**.
- Offline rebuild reproducibility: **697 files stable**.
- Derived rebuilds (`make derived`): **< 2 s** total (canonical 83 apps,
  ledger 96 releases, enrichment 94, reputation 78, 5 client feeds,
  181 API v3 docs).
- `next build`: **186 pages in ~25 s**; first-load JS **~103 kB** shared.
- Root smoke test: **134 URLs green**.

## API budget

- Scheduled syncs are incremental; discovery sleeps between code-search
  pages and degrades to empty on rate-limit instead of retry-storming.
- Monitoring probes are HEAD-first (no body transfer) and anonymous.
- GitHub API calls scale with *changed* upstreams, not catalog size.

## Scaling guidance

1. Past ~1,000 sources, run discovery/monitoring through
   `async_http.fetch_many()` (`limit=32`, `timeout=15`) instead of the
   thread pools — same result shape, pooled connections.
2. Raise `--workers` for probes before raising timeouts; latency, not
   bandwidth, dominates.
3. Keep `max_bytes` caps tight; feeds are KB-scale — anything larger is
   abuse or misconfiguration.
4. Prefer the static API snapshots + CDN caching for read-heavy clients;
   reserve dynamic routes for filtered/paginated queries.

## Known ceilings

- Single-runner GitHub Actions (no distributed queue) — acceptable to
  the 10k-app target given incremental sync + caching.
- `api/v3` static detail docs grow linearly with apps (~2 KB each) —
  negligible for git/Pages at this scale.
