// Copy pipeline outputs into web/ so the app builds and runs anywhere
// (Vercel / Cloudflare / self-hosted) without reaching outside its dir.
// Runs automatically via the `prebuild` / `predev` npm hooks.
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const web = join(here, "..");
const root = join(web, "..");

function copy(relSrc, relDst) {
  const src = join(root, relSrc);
  const dst = join(web, relDst);
  if (!existsSync(src)) {
    console.warn(`sync-data: missing ${relSrc} (skipped)`);
    return false;
  }
  mkdirSync(dirname(dst), { recursive: true });
  copyFileSync(src, dst);
  return true;
}

// Server-bundled snapshots (imported by src/lib/data.ts).
const serverDocs = [
  "apps.json",
  "discovery.json",
  "sources.json",
  "collections.json",
  "trending.json",
  "status.json",
  "analytics.json",
  "search-index.json",
  "reputation.json",
];
for (const name of serverDocs) copy(join("feeds", name), join("src", "data", name));
for (const name of ["security.json", "source_reputation.json", "analytics_rollup.json", "canonical_apps.json"]) {
  copy(join("data", name), join("src", "data", name));
}
copy("catalog.json", "src/data/catalog.json");

// Client-fetchable API snapshot (powers /search offline + PWA caching).
copy("api/v3/apps.json", "public/data/v3/apps.json");
copy("api/v3/search-index.json", "public/data/v3/search-index.json");
copy("api/v3/status.json", "public/data/v3/status.json");
copy("api/v3/trending.json", "public/data/v3/trending.json");

// Build stamp for the footer / diagnostics.
const stamp = { syncedAt: new Date().toISOString(), root: "OmniSource" };
mkdirSync(join(web, "src", "data"), { recursive: true });
writeFileSync(join(web, "src", "data", "_sync.json"), JSON.stringify(stamp, null, 2) + "\n");

// Sanity: the catalog snapshot must exist or the build cannot render.
const appsRaw = readFileSync(join(web, "src", "data", "apps.json"), "utf8");
const apps = JSON.parse(appsRaw).apps ?? [];
console.log(`sync-data: ${apps.length} apps synced into web/`);
