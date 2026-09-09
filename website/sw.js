/* OmniSource service worker — offline-first for the live catalog. */
'use strict';

const VERSION = 'omnisource-v1';
const CORE_CACHE = `${VERSION}-core`;
const DATA_CACHE = `${VERSION}-data`;

const CORE_ASSETS = [
  './',
  './index.html',
  './css/styles.css',
  './js/app.js',
  './manifest.webmanifest',
  './assets/OmniSource.png'
];

const DATA_URLS = [
  './apps.json',
  './catalog.json',
  './feeds/health.json',
  './feeds/updates.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CORE_CACHE).then(cache => cache.addAll(CORE_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key !== CORE_CACHE && key !== DATA_CACHE).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const { request } = event;
  if (request.method !== 'GET' || !request.url.startsWith(self.location.origin)) return;

  const url = new URL(request.url);

  // App icons and screenshots: cache-first, then network.
  if (url.pathname.startsWith('/assets/')) {
    event.respondWith(
      caches.match(request).then(cached => cached || fetch(request).then(response => {
        const copy = response.clone();
        caches.open(DATA_CACHE).then(cache => cache.put(request, copy)).catch(() => {});
        return response;
      }))
    );
    return;
  }

  // Live catalog data: stale-while-revalidate keeps the UI instant offline.
  if (DATA_URLS.includes(url.pathname) || DATA_URLS.includes(`${url.pathname}/`)) {
    event.respondWith(
      caches.open(DATA_CACHE).then(async cache => {
        const cached = await cache.match(request);
        const refresh = fetch(request).then(response => {
          if (response.ok) cache.put(request, response.clone());
          return response;
        }).catch(() => cached);
        return cached || refresh;
      })
    );
    return;
  }

  // Navigations: network first, fall back to the cached shell.
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).then(response => {
        const copy = response.clone();
        caches.open(CORE_CACHE).then(cache => cache.put('./index.html', copy)).catch(() => {});
        return response;
      }).catch(() => caches.match('./index.html'))
    );
    return;
  }

  // Everything else (CSS/JS/fonts/feeds): cache-first with background refresh.
  event.respondWith(
    caches.match(request).then(cached => {
      const refresh = fetch(request).then(response => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(DATA_CACHE).then(cache => cache.put(request, copy)).catch(() => {});
        }
        return response;
      }).catch(() => cached);
      return cached || refresh;
    })
  );
});
