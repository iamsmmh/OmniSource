/* OmniSource service worker v3 — offline-first for the full site.
 *
 * Cache strategy is split into three rings:
 *
 *   CORE_CACHE   – the application shell (every page, CSS, JS, logo).
 *                  Pre-cached on install, versioned so old caches die.
 *   DATA_CACHE   – every JSON feed / generated app page.
 *                  Stale-while-revalidate: instant paint, background refresh.
 *   ASSET_CACHE  – icons and screenshots. Cache-first with background
 *                  revalidation.
 *
 * v3 changes (design-system era):
 *   • the shell now covers the new page set: /, /compare/, /status/,
 *     /analytics/, /install/, /search/ plus the design-system stylesheets;
 *   • per-app pages (apps/<slug>/) are still captured on first visit so the
 *     whole catalog stays browsable offline;
 *   • skipWaiting + clients.claim + the update message protocol are kept,
 *     which powers the “new version ready” toast in js/core.js.
 *
 * v4 changes (sub-path deploy fix):
 *   • the site is served from a sub-path (/OmniSource/), so every pathname
 *     check is base-agnostic: asset / data / per-app matching works under
 *     any base instead of assuming the domain root.
 */
'use strict';

const VERSION = 'omnisource-v5';
const CORE_CACHE = `${VERSION}-core`;
const DATA_CACHE = `${VERSION}-data`;
const ASSET_CACHE = `${VERSION}-assets`;

const CORE_ASSETS = [
  './',
  './index.html',
  './compare.html',
  './compare/index.html',
  './status/index.html',
  './analytics/index.html',
  './install/index.html',
  './search/index.html',
  './manifest.webmanifest',
  './assets/design-system/tokens.css',
  './assets/design-system/utilities.css',
  './assets/design-system/animations.css',
  './assets/design-system/components.css',
  './js/core.js',
  './js/site.js',
  './assets/OmniSource.png'
];

const DATA_URLS = [
  './apps.json',
  './catalog.json',
  './discovery.json',
  './feeds/health.json',
  './feeds/updates.json',
  './feeds/analytics.json',
  './feeds/verification.json',
  './feeds/status.json',
  './feeds/duplicates.json',
  './feeds/sources.json',
  './feeds/trending.json',
  './feeds/related.json',
  './feeds/reputation.json',
  './feeds/download-intelligence.json',
  './feeds/community.json',
  './feeds/install.json',
  './feeds/search-index.json',
  './feeds/compare.json',
  './feeds/screenshots.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CORE_CACHE)
      .then(cache => cache.addAll(CORE_ASSETS).catch(() => undefined))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => !key.startsWith(VERSION)).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
      .then(() => notifyClientsOfUpdate())
  );
});

function notifyClientsOfUpdate() {
  // Tell every open client that a new SW took over so the page can show
  // the “update available” toast and reload.
  self.clients.matchAll({ includeUncontrolled: true }).then(clients => {
    for (const client of clients) {
      client.postMessage({ type: 'omnisource-sw-updated', version: VERSION });
    }
  });
}

// DATA_URLS is written root-relative; strip the './' so it can be matched as
// a suffix against pathnames under any deploy base (e.g. '/OmniSource/').
const DATA_SUFFIXES = DATA_URLS.map(entry => '/' + entry.replace(/^\.\//, ''));

function isAssetPath(pathname) {
  return (
    pathname.includes('/assets/') ||
    pathname.endsWith('.png') ||
    pathname.endsWith('.webp') ||
    pathname.endsWith('.svg') ||
    pathname.endsWith('.woff2') ||
    pathname.endsWith('.woff') ||
    pathname.endsWith('.ico')
  );
}

function isDataPath(pathname) {
  if (DATA_SUFFIXES.some(suffix => pathname === suffix || pathname.endsWith(suffix))) return true;
  if (pathname.endsWith('.json')) return true;
  if (/\/apps\/[^/]+\/?$/.test(pathname)) return true; // per-app pages
  if (/\/apps\/[^/]+\/index\.html$/.test(pathname)) return true;
  return false;
}

self.addEventListener('fetch', event => {
  const { request } = event;
  if (request.method !== 'GET' || !request.url.startsWith(self.location.origin)) return;

  const url = new URL(request.url);

  if (isAssetPath(url.pathname)) {
    event.respondWith(cacheFirst(ASSET_CACHE, request));
    return;
  }

  if (isDataPath(url.pathname)) {
    event.respondWith(staleWhileRevalidate(DATA_CACHE, request));
    return;
  }

  if (request.mode === 'navigate') {
    event.respondWith(networkFirstNavigation(request));
    return;
  }

  // CSS / JS / other same-origin GETs: cache-first with background refresh.
  event.respondWith(cacheFirst(DATA_CACHE, request));
});

function cacheFirst(cacheName, request) {
  return caches.open(cacheName).then(async cache => {
    const cached = await cache.match(request);
    if (cached) {
      // Refresh in the background; do not block the response.
      fetch(request).then(response => {
        if (response && response.ok) cache.put(request, response.clone()).catch(() => undefined);
      }).catch(() => undefined);
      return cached;
    }
    try {
      const response = await fetch(request);
      if (response && response.ok) cache.put(request, response.clone()).catch(() => undefined);
      return response;
    } catch (error) {
      return new Response('Offline', { status: 504, statusText: 'Offline' });
    }
  });
}

function staleWhileRevalidate(cacheName, request) {
  return caches.open(cacheName).then(async cache => {
    const cached = await cache.match(request);
    const network = fetch(request).then(response => {
      if (response && response.ok) cache.put(request, response.clone()).catch(() => undefined);
      return response;
    }).catch(() => cached);
    return cached || network;
  });
}

function networkFirstNavigation(request) {
  return fetch(request).then(response => {
    const copy = response.clone();
    caches.open(CORE_CACHE).then(cache => cache.put(request, copy)).catch(() => undefined);
    return response;
  }).catch(async () => {
    // Fall back to the cached copy of this URL, then the cached shell.
    const cache = await caches.open(CORE_CACHE);
    return (await cache.match(request)) || (await cache.match('./index.html')) ||
      new Response('Offline', { status: 504, statusText: 'Offline' });
  });
}

self.addEventListener('message', event => {
  // Let the page ask the SW to skip waiting (paired with the update toast).
  if (event.data && event.data.type === 'omnisource-skip-waiting') {
    self.skipWaiting();
  }
});
