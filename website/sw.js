/* OmniSource service worker — offline-first for the live catalog.
 *
 * The cache strategy is split into three rings:
 *
 *   CORE_CACHE   – the application shell. Pre-cached on install.
 *   DATA_CACHE   – every JSON feed / app page. Stale-while-revalidate so the
 *                  page renders instantly even when the network is down.
 *   ASSET_CACHE  – icons, screenshots, fonts. Cache-first, falls back to the
 *                  network on miss.
 *
 * The new strategy also:
 *   • caches per-app pages the first time a user opens one (so offline
 *     browsing of the full catalog works after a single visit);
 *   • uses a network-first strategy for navigations, with the shell as a
 *     fallback so the home page always loads;
 *   • exposes ``skipWaiting`` + ``clients.claim`` so a new SW activates
 *     immediately after install, which the front-end pairs with the
 *     "new version available" toast in the page.
 */
'use strict';

const VERSION = 'omnisource-v2';
const CORE_CACHE = `${VERSION}-core`;
const DATA_CACHE = `${VERSION}-data`;
const ASSET_CACHE = `${VERSION}-assets`;

const CORE_ASSETS = [
  './',
  './index.html',
  './compare.html',
  './manifest.webmanifest',
  './css/styles.css',
  './css/app-page.css',
  './js/app.js',
  './js/compare.js',
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
  // Inform every open client that a new SW has taken over so the page can
  // show an "update available" toast and reload.
  self.clients.matchAll({ includeUncontrolled: true }).then(clients => {
    for (const client of clients) {
      client.postMessage({ type: 'omnisource-sw-updated', version: VERSION });
    }
  });
}

function isAssetPath(pathname) {
  return (
    pathname.startsWith('/assets/') ||
    pathname.endsWith('.png') ||
    pathname.endsWith('.webp') ||
    pathname.endsWith('.svg') ||
    pathname.endsWith('.woff2') ||
    pathname.endsWith('.woff') ||
    pathname.endsWith('.ico')
  );
}

function isDataPath(pathname) {
  if (DATA_URLS.includes(pathname) || DATA_URLS.includes(`${pathname}/`)) return true;
  if (pathname.endsWith('.json')) return true;
  if (/^\/apps\/[^/]+\/?$/.test(pathname)) return true; // per-app pages
  if (/^\/apps\/[^/]+\/index\.html$/.test(pathname)) return true;
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
      // Last resort: a cached shell or a simple 504.
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
    // Fall back to the cached shell, then the cached home page.
    const cache = await caches.open(CORE_CACHE);
    return (await cache.match(request)) || (await cache.match('./index.html')) ||
      new Response('Offline', { status: 504, statusText: 'Offline' });
  });
}

self.addEventListener('message', event => {
  // Allow the page to ask the SW to skip waiting (used by the "update"
  // toast). The caller is responsible for reloading after activation.
  if (event.data && event.data.type === 'omnisource-skip-waiting') {
    self.skipWaiting();
  }
});
