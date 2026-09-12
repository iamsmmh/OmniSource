/*
 * Favorites module (Phase 7): the read side of the favorites store for
 * module pages, plus a count badge. Mutations keep happening in
 * js/features.js (OS.Favorites) on the catalog — this module writes the same
 * canonical key so a toggle is visible from either path.
 */

import { on, read, write } from './store.js';

export const FAVORITES_KEY = 'omnisource-favorites';
const MIRROR_KEY = 'os:favorites'; // legacy namespaced copy (features.js)

export function favoritesList() {
  const value = read(FAVORITES_KEY, read(MIRROR_KEY, []));
  return Array.isArray(value) ? value : [];
}

export function isFavorite(slug) {
  return favoritesList().indexOf(String(slug)) !== -1;
}

function persist(list) {
  write(FAVORITES_KEY, list);
  write(MIRROR_KEY, list); // keep the legacy mirror in step
}

/** Toggle `slug`; returns the new membership. */
export function toggleFavorite(slug) {
  const value = String(slug);
  const list = favoritesList();
  const index = list.indexOf(value);
  if (index === -1) list.push(value);
  else list.splice(index, 1);
  persist(list);
  document.dispatchEvent(new CustomEvent('os:favorites-changed', { detail: { slug: value, favorite: index === -1 } }));
  return index === -1;
}

export function onFavoritesChange(listener) {
  return on(FAVORITES_KEY, function (value) {
    listener(Array.isArray(value) ? value : []);
  });
}

/** Update a `#favCount` badge (when the page carries one) on every change. */
function bindBadge() {
  const badge = document.getElementById('favCount');
  if (!badge) return;
  const paint = function () {
    const count = favoritesList().length;
    badge.textContent = String(count);
    badge.hidden = count === 0;
  };
  onFavoritesChange(paint);
  paint();
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bindBadge);
  else bindBadge();
}
