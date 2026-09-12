/*
 * Theme module (Phase 7): the light/dark/auto preference, same contract as
 * the legacy bootstrap in js/core.js — `omnisource-theme` in localStorage,
 * `data-theme` on <html>, and a matching `meta#themeColor`.
 *
 * Pages that still load js/core.js keep owning the toggle (core binds
 * #themeButton first); this module is the entry point for module-only pages
 * and exports the primitives for everything else. It never adds globals —
 * state lives in this module's closure.
 */

const KEY = 'omnisource-theme';
export const THEMES = Object.freeze(['light', 'dark', 'auto']);

const listeners = new Set();

function readRaw() {
  try {
    return localStorage.getItem(KEY);
  } catch (err) {
    return null;
  }
}

export function currentTheme() {
  const value = readRaw();
  return THEMES.indexOf(value) === -1 ? 'auto' : value;
}

function prefersDark() {
  return typeof matchMedia === 'function' && matchMedia('(prefers-color-scheme: dark)').matches;
}

export function isDark() {
  const theme = currentTheme();
  return theme === 'dark' || (theme === 'auto' && prefersDark());
}

/** Apply `theme` (light|dark|auto) to the document and notify listeners. */
export function applyTheme(theme) {
  const value = THEMES.indexOf(theme) === -1 ? 'auto' : theme;
  try {
    if (value === 'auto') localStorage.removeItem(KEY);
    else localStorage.setItem(KEY, value);
  } catch (err) {
    /* private mode: the toggle still works for this page load */
  }
  document.documentElement.dataset.theme = value;
  const color = value === 'light' ? '#e8eef8' : '#07070f';
  const meta = document.querySelector('meta#themeColor');
  if (meta) meta.setAttribute('content', color);
  for (const listener of listeners) {
    try {
      listener(value);
    } catch (err) {
      /* one bad listener must not break the others */
    }
  }
  return value;
}

export function nextTheme() {
  const order = ['auto', 'light', 'dark'];
  return order[(order.indexOf(currentTheme()) + 1) % order.length];
}

/** Subscribe to theme changes; returns the unsubscribe function. */
export function onThemeChange(listener) {
  listeners.add(listener);
  return function unsubscribe() {
    listeners.delete(listener);
  };
}

/**
 * Bind the `#themeButton` toggle — only when no other script has claimed it.
 * js/core.js binds first (classic scripts run before modules) and marks the
 * element with `data-theme-claimed`; without that mark this module owns the
 * button, so there is never a double-toggle.
 */
export function initThemeToggle() {
  const button = document.getElementById('themeButton');
  if (!button || button.dataset.themeClaimed === '1' || button.dataset.bound === '1') return;
  button.dataset.bound = '1';
  const label = function () {
    const theme = currentTheme();
    const text = 'Theme: ' + theme;
    button.title = text;
    button.setAttribute('aria-label', text);
  };
  button.addEventListener('click', function () {
    label();
  });
  onThemeChange(label);
  label();
  if (typeof matchMedia === 'function') {
    const media = matchMedia('(prefers-color-scheme: dark)');
    const change = function () {
      if (currentTheme() === 'auto') applyTheme('auto');
    };
    if (media.addEventListener) media.addEventListener('change', change);
  }
}

// Module entry point (loaded with type="module" on pages that want it).
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initThemeToggle);
  } else {
    initThemeToggle();
  }
}
