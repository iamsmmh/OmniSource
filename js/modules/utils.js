/*
 * Shared helpers for the modular page controllers (js/modules/*).
 *
 * Rules for this layer (modernization Phase 7):
 *  - ES modules only: every value crosses boundaries through `export`/
 *    `import`; nothing here writes to `window` or reads implicit globals.
 *  - The legacy `window.OS` facade (js/core.js, loaded first on every page)
 *    may be *consumed* for helpers it already owns (OS.url) so relative URLs
 *    keep resolving from any depth — but a module must stay fully usable
 *    when OS is absent (falling back to relative paths).
 */

const jsonCache = new Map();

/** Escape a string for safe interpolation into HTML text/attributes. */
export function esc(value) {
  if (value === null || value === undefined) return '';
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/** Resolve a site-root-relative path through the legacy OS.url helper. */
export function siteUrl(path) {
  const clean = String(path || '').replace(/^\.\//, '');
  const root = typeof window !== 'undefined' ? window.OS : null;
  if (root && typeof root.url === 'function') return root.url(clean);
  return '/' + clean.replace(/^\//, '');
}

/**
 * Fetch and parse JSON with one in-flight/deduped request per URL per page
 * load (mirrors core.js jsonMemo for the module layer). Never throws on
 * network/parse failure — callers get `null` and decide what to render.
 */
export function fetchJSON(url, options = {}) {
  const resolved = url.startsWith('http') ? url : siteUrl(url);
  if (!options.force && jsonCache.has(resolved)) return jsonCache.get(resolved);
  const pending = fetch(resolved, { credentials: 'omit' })
    .then(function (response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    })
    .catch(function () {
      jsonCache.delete(resolved); // allow a later retry on focus/online
      return null;
    });
  jsonCache.set(resolved, pending);
  return pending;
}

/** Debounce that also exposes `.cancel()` for teardown in tests. */
export function debounce(fn, wait) {
  let timer = 0;
  const wrapped = function () {
    const args = arguments;
    clearTimeout(timer);
    timer = setTimeout(function () {
      fn.apply(null, args);
    }, wait);
  };
  wrapped.cancel = function () {
    clearTimeout(timer);
  };
  return wrapped;
}

/** Localized relative day ("3d ago", "yesterday") via the legacy i18n or en. */
export function relDays(value) {
  if (!value) return '—';
  const then = new Date(value + (value.length === 10 ? 'T00:00:00' : ''));
  if (isNaN(then.getTime())) return String(value);
  const days = Math.floor((Date.now() - then.getTime()) / 86400000);
  const t = translate;
  if (days <= 0) return t('common.today', 'today');
  if (days === 1) return t('common.yesterday', 'yesterday');
  if (days < 60) return t('common.daysAgo', days + 'd ago').replace('${count}', days);
  if (days < 730) return t('common.monthsAgo', Math.round(days / 30) + 'mo ago').replace('${count}', Math.round(days / 30));
  return t('common.yearsAgo', (days / 365).toFixed(1) + 'y ago').replace('${count}', Math.floor(days / 365));
}

/** Look up a locale string through the shared i18n layer, with fallback. */
export function translate(key, fallback, params) {
  let text = fallback;
  const root = typeof window !== 'undefined' ? window : null;
  if (root && root.OmniI18n && typeof root.OmniI18n.t === 'function') {
    const value = root.OmniI18n.t(key);
    if (value && value !== key) text = value;
  }
  if (params) {
    for (const name of Object.keys(params)) {
      text = text.split('${' + name + '}').join(String(params[name]));
    }
  }
  return text;
}

/**
 * Translate freshly rendered markup and announce it to the i18n layer.
 * `data-i18n` attributes carry English fallback text, so untranslated
 * strings still read correctly; coverage lives in locales/*.json.
 */
export function localize(scope) {
  const root = typeof window !== 'undefined' ? window : null;
  if (root && root.OmniI18n && typeof root.OmniI18n.apply === 'function') {
    try {
      root.OmniI18n.apply(scope || document);
      return;
    } catch (err) {
      /* fall through to the manual pass below */
    }
  }
  (scope || document).querySelectorAll('[data-i18n]').forEach(function (node) {
    const value = translate(node.getAttribute('data-i18n'), node.textContent.trim());
    if (value) node.textContent = value;
  });
}

/** Count-up animation for `data-count` stat values (honors reduced motion). */
export function countUp(node, target, duration) {
  const to = Number(target) || 0;
  const reduce =
    typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce || to <= 1) {
    node.textContent = String(to);
    return;
  }
  const ms = duration || 900;
  const started = performance.now();
  function frame(now) {
    const progress = Math.min(1, (now - started) / ms);
    const eased = 1 - Math.pow(1 - progress, 3);
    node.textContent = String(Math.round(to * eased));
    if (progress < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}
