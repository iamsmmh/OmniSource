/*
 * Client-side store (Phase 7): one localStorage contract shared by the
 * modules and the legacy js/features.js store — the canonical
 * `omnisource-favorites` key plus the namespaced `os:favorites` mirror it
 * already dual-writes. Both stay byte-compatible so no data is lost when a
 * visitor moves between the two code paths.
 */

const listeners = new Map();

function readRaw(key) {
  try {
    return localStorage.getItem(key);
  } catch (err) {
    return null;
  }
}

function writeRaw(key, value) {
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
    return true;
  } catch (err) {
    return false;
  }
}

export function read(key, fallback) {
  const raw = readRaw(key);
  if (raw === null) return fallback;
  try {
    return JSON.parse(raw);
  } catch (err) {
    return raw; // non-JSON values are surfaced as-is
  }
}

export function write(key, value) {
  const stored = writeRaw(key, value === undefined ? null : JSON.stringify(value));
  emit(key);
  return stored;
}

/** Subscribe to writes of one key; returns the unsubscribe function. */
export function on(key, listener) {
  if (!listeners.has(key)) listeners.set(key, new Set());
  listeners.get(key).add(listener);
  return function () {
    listeners.get(key).delete(listener);
  };
}

function emit(key) {
  const set = listeners.get(key);
  if (!set) return;
  for (const listener of set) {
    try {
      listener(read(key, null));
    } catch (err) {
      /* a broken subscriber must not break persistence */
    }
  }
}

/** Other tabs write straight to localStorage — re-broadcast through on(). */
if (typeof window !== 'undefined') {
  window.addEventListener('storage', function (event) {
    if (event.key) emit(event.key);
  });
}
