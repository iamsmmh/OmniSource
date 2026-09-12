/*
 * Collections module (Phase 7): the shared collection-card renderer used by
 * /collections/ pages. It hydrates `#collectionGrid` only when the legacy
 * OS.Collections renderer has not already populated it, and keeps a URL
 * contract (`?c=<slug>`) for deep links from home rails and search.
 */

import { esc, fetchJSON, localize } from './utils.js';
import { search } from './search.js';

export function collectionFields() {
  return [
    { get: function (item) { return item.title || item.name; }, weight: 1.4 },
    { get: function (item) { return item.description; }, weight: 0.8 },
    { get: function (item) { return (item.tags || []).join(' '); }, weight: 0.9 },
  ];
}

export function cardHtml(collection) {
  const slug = collection.slug || collection.id;
  const count = (collection.apps || []).length;
  return (
    '<a class="collection-card panel" href="' + esc(String(slug)) + '/">' +
    '<h3>' + esc(collection.title || collection.name) + '</h3>' +
    '<p class="text-muted">' + esc(collection.description || '') + '</p>' +
    '<span class="badge blue">' + esc(String(count) + ' apps') + '</span></a>'
  );
}

export async function loadCollections() {
  const doc = await fetchJSON('feeds/collections.json');
  return doc && Array.isArray(doc.collections) ? doc.collections : [];
}

async function init() {
  const grid = document.getElementById('collectionGrid');
  if (!grid || grid.children.length) return; // legacy renderer owns it
  const collections = await loadCollections();
  if (!collections.length) return;
  const params = new URLSearchParams(location.search);
  const query = params.get('q') || '';
  const items = query ? search(query, collections, collectionFields()) : collections;
  grid.innerHTML = items.map(cardHtml).join('');
  localize(grid);
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
}
