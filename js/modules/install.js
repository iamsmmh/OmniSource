/*
 * Install helpers (Phase 7): build per-client install URLs and expose a
 * copy helper used by module pages. The legacy clipboard delegation in
 * js/core.js stays the implementation for data-copy buttons, so this module
 * only fills in behaviour where no legacy script runs (standalone embeds).
 */

import { esc, siteUrl, translate } from './utils.js';

export const CLIENT_SCHEMES = Object.freeze({
  altstore: 'altstore://add-source',
  sidestore: 'sidestore://addSource?url=',
  feather: 'feather://addSource?url=',
  delta: 'delta://addSource?url=',
  walle: 'walle://addSource?url=',
});

/** The canonical subscribable feed URL for this deployment. */
export function sourceFeedUrl() {
  return siteUrl('apps.json');
}

/** Install URL for one client (falls back to the plain feed URL). */
export function installUrlFor(client, feedUrl) {
  const url = feedUrl || sourceFeedUrl();
  const scheme = CLIENT_SCHEMES[String(client || '').toLowerCase()];
  if (!scheme) return url;
  if (scheme.endsWith('=')) return scheme + encodeURIComponent(url);
  return scheme + '?url=' + encodeURIComponent(url);
}

/** Copy text to the clipboard with the pre-async fallback core.js uses. */
export async function copyText(text) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch (err) {
    /* fall through to the legacy path */
  }
  try {
    const area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand('copy');
    area.remove();
    return ok;
  } catch (err) {
    return false;
  }
}

/** Render a copy of the install box for embeds that ship no legacy JS. */
export function renderInstallBox(container) {
  if (!container) return;
  const feed = sourceFeedUrl();
  container.innerHTML =
    '<div class="panel install-embed">' +
    '<code>' + esc(feed) + '</code>' +
    '<button class="button small" type="button" data-copy="' + esc(feed) + '">' +
    esc(translate('hero.copySource', 'Copy')) +
    '</button></div>';
  const button = container.querySelector('[data-copy]');
  if (button) {
    button.addEventListener('click', async function () {
      const ok = await copyText(feed);
      button.textContent = ok
        ? translate('common.copied', 'Copied!')
        : translate('hero.copySource', 'Copy');
      setTimeout(function () {
        button.textContent = translate('hero.copySource', 'Copy');
      }, 1600);
    });
  }
}
