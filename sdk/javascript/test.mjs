/**
 * Smoke tests for the OmniSource JavaScript SDK.
 *
 * The test suite uses a tiny in-memory fetch implementation so it can run
 * offline against fixtures. The fixtures are loaded from the live ``feeds/``
 * directory of the repository; if the directory is not present the tests
 * are skipped so the suite never blocks CI.
 */
import OmniSource from './omnisource.mjs';
import OmniSourceCJS from './omnisource.cjs';
import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..', '..');
const feedsDir = join(repoRoot, 'feeds');

if (!existsSync(feedsDir)) {
  console.log('SKIP: no feeds/ directory available; run scripts/omnisource.py first.');
  process.exit(0);
}

function makeFixtureFetch() {
  const cache = new Map();
  for (const file of readdirSync(feedsDir)) {
    if (file.endsWith('.json')) {
      try {
        cache.set(`/feeds/${file}`, JSON.parse(readFileSync(join(feedsDir, file), 'utf8')));
      } catch { /* ignore */ }
    }
  }
  // /discovery.json may live at the repo root (Pages deployment) or inside feeds/.
  for (const candidate of [join(repoRoot, 'discovery.json'), join(feedsDir, 'discovery.json')]) {
    if (existsSync(candidate)) {
      try {
        cache.set('/discovery.json', JSON.parse(readFileSync(candidate, 'utf8')));
        break;
      } catch { /* ignore */ }
    }
  }
  return url => {
    // Recover the path component by stripping the SDK's baseURL.
    const base = 'https://example.test/OmniSource';
    let path = url;
    if (path.startsWith(base)) path = path.slice(base.length);
    if (!path.startsWith('/')) path = '/' + path;
    if (cache.has(path)) return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(cache.get(path)) });
    return Promise.resolve({ ok: false, status: 404, text: () => Promise.resolve('') });
  };
}

const fetcher = makeFixtureFetch();
const client = new OmniSource({ baseURL: 'https://example.test/OmniSource', fetch: fetcher });
const cjsClient = new OmniSourceCJS({ baseURL: 'https://example.test/OmniSource', fetch: fetcher });

const cases = [];
function test(name, fn) { cases.push([name, fn]); }

test('search returns results for a real slug', async () => {
  const results = await client.search('youtube');
  if (!results.length) throw new Error('expected at least one result');
});

test('getApp returns a known app', async () => {
  const app = await client.getApp('uyouenhanced');
  if (!app || !app.slug) throw new Error('expected uyouenhanced');
});

test('getTrending returns a board', async () => {
  const trending = await client.getTrending();
  if (!Array.isArray(trending.trending)) throw new Error('expected array');
});

test('getRelated returns an array', async () => {
  const related = await client.getRelated('uyouenhanced');
  if (!Array.isArray(related)) throw new Error('expected array');
});

test('getReputation returns sources', async () => {
  const rep = await client.getReputation();
  if (!Array.isArray(rep.sources)) throw new Error('expected array');
});

test('getHealth returns summary', async () => {
  const health = await client.getHealth();
  if (!health.summary) throw new Error('expected summary');
});

test('CJS build exposes the same methods', async () => {
  const trending = await cjsClient.getTrending();
  if (!trending.trending) throw new Error('CJS getTrending failed');
});

(async () => {
  let passed = 0;
  let failed = 0;
  for (const [name, fn] of cases) {
    try {
      await fn();
      console.log(`  ok  ${name}`);
      passed++;
    } catch (error) {
      console.log(`  fail ${name}: ${error.message}`);
      failed++;
    }
  }
  console.log(`\n${passed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})();
