/* ============================================================================
 * OmniSource — website/assets/AssetManager.js
 * ----------------------------------------------------------------------------
 * Central asset manager for the website: fallback icons, broken-image
 * detection and missing-logo replacement.
 *
 * Behaviour
 *   1. Resolves every app icon through feeds/asset-manifest.json when it is
 *      available (missing icons map to the branded placeholder, so the page
 *      never shows a broken image).
 *   2. Installs a capture-phase error listener that swaps any <img> which
 *      fails to load to the placeholder for its data-asset-kind
 *      (app | category | banner). Each image is retried exactly once, so a
 *      missing placeholder can never loop.
 *   3. Exposes window.AssetManager.resolve(kind, url) for renderers that
 *      build <img> markup (js/site.js, app pages).
 *
 * Dependency-free classic script (the site has no build step): load with a
 * plain deferred <script> tag after js/core.js. Safe to load twice and safe
 * to import in non-DOM environments (the DOM wiring is skipped there).
 * ========================================================================== */
(function (root) {
  'use strict';

  /** @type {Record<string, string>} */
  var PLACEHOLDERS = {
    app: 'assets/placeholders/app.svg',
    category: 'assets/placeholders/category.svg',
    banner: 'assets/placeholders/banner.svg'
  };

  /**
   * Resolve the site root the same way js/core.js does, without depending
   * on it (AssetManager must keep working when core.js fails to load).
   * @returns {string} Root-relative base path, e.g. '/OmniSource/' or '/'.
   */
  function detectRoot() {
    try {
      var scripts = document.getElementsByTagName('script');
      for (var i = scripts.length - 1; i >= 0; i--) {
        var src = scripts[i].getAttribute('src') || '';
        var match = src.match(/^(.*\/)(?:website\/assets\/AssetManager\.js|js\/(?:core|site|features)\.js|src\/js\/[^/]+\.js)$/);
        if (match) return match[1] || '/';
      }
      if (root.OS && root.OS.ROOT) return root.OS.ROOT;
    } catch (e) { /* fall through to location-derived base */ }
    try {
      var path = root.location ? root.location.pathname : '/';
      return path.indexOf('/OmniSource/') === 0 ? '/OmniSource/' : '/';
    } catch (e2) { return '/'; }
  }

  /**
   * @param {string} kind Placeholder kind (app | category | banner).
   * @returns {string} Root-relative URL of the placeholder artwork.
   */
  function placeholder(kind) {
    var file = PLACEHOLDERS[kind] || PLACEHOLDERS.app;
    var base = detectRoot();
    if (base.charAt(base.length - 1) !== '/') base += '/';
    return base + file;
  }

  /**
   * Resolve an icon URL, falling back to the placeholder when the source
   * is empty or known-missing.
   * @param {string} kind Placeholder kind used when url is unusable.
   * @param {string} url Declared icon URL (absolute, root-relative or bare).
   * @returns {string} Usable image URL (never empty, never whitespace).
   */
  function resolve(kind, url) {
    var value = String(url == null ? '' : url).trim();
    if (!value || value === '#' || /^(data:)?\s*$/.test(value)) return placeholder(kind);
    return value;
  }

  /**
   * Swap a failed <img> to its placeholder. Retried images carry
   * data-asset-fallback="1" so a missing placeholder cannot loop.
   * @param {HTMLImageElement} img The failed image element.
   * @returns {boolean} True when a fallback was applied.
   */
  function fallback(img) {
    if (!img || img.nodeName !== 'IMG') return false;
    if (img.getAttribute('data-asset-fallback') === '1') return false;
    var kind = img.getAttribute('data-asset-kind') || 'app';
    img.setAttribute('data-asset-fallback', '1');
    img.src = placeholder(kind);
    if (img.srcset) img.removeAttribute('srcset');
    return true;
  }

  var installed = false;

  function install() {
    if (installed) return;
    installed = true;
    if (typeof document === 'undefined' || !document.addEventListener) return;
    // Capture phase: <img> error events do not bubble.
    document.addEventListener('error', function (event) {
      var target = event && event.target;
      if (target && target.nodeName === 'IMG') fallback(target);
    }, true);
  }

  /**
   * Proactively replace icons the build flagged as missing (from
   * feeds/asset-manifest.json) instead of waiting for 404s.
   */
  function prefetchManifest() {
    if (typeof fetch === 'undefined' || typeof document === 'undefined') return;
    var base = detectRoot();
    if (base.charAt(base.length - 1) !== '/') base += '/';
    fetch(base + 'feeds/asset-manifest.json', { headers: { Accept: 'application/json' } })
      .then(function (res) { return res.ok ? res.json() : null; })
      .then(function (doc) {
        if (!doc || !doc.missing || !doc.missing.length) return;
        var missing = {};
        doc.missing.forEach(function (slug) { missing[slug] = true; });
        Array.prototype.forEach.call(document.querySelectorAll('img[data-app]'), function (img) {
          if (missing[img.getAttribute('data-app')]) fallback(img);
        });
      })
      .catch(function () { /* offline: the error listener still covers us */ });
  }

  function init() {
    install();
    if (typeof document === 'undefined') return;
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', prefetchManifest);
    } else {
      prefetchManifest();
    }
  }

  var AssetManager = {
    VERSION: 1,
    placeholder: placeholder,
    resolve: resolve,
    fallback: fallback,
    install: install,
    init: init
  };

  root.AssetManager = AssetManager;
  try {
    if (typeof module !== 'undefined' && module.exports) module.exports = AssetManager;
  } catch (e) { /* browser: no module system */ }

  init();
})(typeof globalThis !== 'undefined' ? globalThis : this);
