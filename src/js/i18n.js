/* OmniSource runtime localization. Works from GitHub Pages sub-paths and offline.
 *
 * Markup contract (see locales/en.json for the canonical key set):
 *   data-i18n="dotted.key"                 -> textContent
 *   data-i18n-placeholder="dotted.key"     -> placeholder attribute
 *   data-i18n-aria-label="dotted.key"      -> aria-label attribute
 *   data-i18n-alt="dotted.key"             -> alt attribute
 *   data-i18n-title="dotted.key"           -> title attribute
 *
 * English is the fallback locale: a missing key in the active language
 * resolves to the English string, and a key missing everywhere renders as
 * the key itself (plus a console warning) so gaps are visible in CI logs
 * instead of blanking the UI. tests/test_translations.py additionally
 * asserts every data-i18n* key used by any page exists in en.json.
 */
(function (root) {
  'use strict';
  var RTL = { ar: 1, fa: 1, ur: 1 };
  var supported = ['en', 'es', 'fr', 'de', 'ar', 'bn', 'zh', 'ja'];
  // Suffix match (not substring): a host like evil-github.io.example.com
  // must not be mistaken for GitHub Pages.
  var base = /\.github\.io$/.test(location.hostname) ? '/OmniSource' : '';
  var cache = {};
  var lang = 'en';
  var loading = {};

  function storage() { try { return localStorage; } catch (_) { return null; } }

  function get(obj, key) {
    if (!obj) return undefined;
    var parts = String(key).split('.');
    var value = obj;
    for (var i = 0; i < parts.length; i++) {
      if (value == null || typeof value !== 'object') return undefined;
      value = value[parts[i]];
    }
    return value;
  }

  function loaded(code) { return Boolean(cache[code]) && !loading[code]; }

  function load(code) {
    if (cache[code]) return Promise.resolve(cache[code]);
    if (loading[code]) return loading[code];
    loading[code] = fetch(base + '/locales/' + code + '.json').then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    }).then(function (doc) {
      cache[code] = doc;
      loading[code] = null;
      return doc;
    }).catch(function (err) {
      console.warn('Locale unavailable:', code, err);
      loading[code] = null;
      if (code === 'en') { cache.en = cache.en || {}; return cache.en; }
      return load('en');
    });
    return loading[code];
  }

  function format(template, params) {
    return String(template).replace(/\$\{(\w+)\}/g, function (_, key) {
      return params && params[key] != null ? params[key] : '${' + key + '}';
    });
  }

  function t(key, params) {
    var value = get(cache[lang], key);
    if (value == null) value = get(cache.en, key);
    if (value == null) {
      if (typeof console !== 'undefined' && console.warn) console.warn('[MISSING TRANSLATION]', key);
      return key;
    }
    return format(value, params);
  }

  function apply() {
    if (typeof document === 'undefined') return;
    document.documentElement.lang = lang;
    document.documentElement.dir = RTL[lang] ? 'rtl' : 'ltr';
    var nodes = document.querySelectorAll('[data-i18n]');
    for (var i = 0; i < nodes.length; i++) nodes[i].textContent = t(nodes[i].getAttribute('data-i18n'));
    var holders = document.querySelectorAll('[data-i18n-placeholder]');
    for (var p = 0; p < holders.length; p++) {
      holders[p].setAttribute('placeholder', t(holders[p].getAttribute('data-i18n-placeholder')));
    }
    var labels = document.querySelectorAll('[data-i18n-aria-label]');
    for (var a = 0; a < labels.length; a++) {
      labels[a].setAttribute('aria-label', t(labels[a].getAttribute('data-i18n-aria-label')));
    }
    var titles = document.querySelectorAll('[data-i18n-title]');
    for (var x = 0; x < titles.length; x++) {
      titles[x].setAttribute('title', t(titles[x].getAttribute('data-i18n-title')));
    }
    var alts = document.querySelectorAll('[data-i18n-alt]');
    for (var g = 0; g < alts.length; g++) {
      alts[g].setAttribute('alt', t(alts[g].getAttribute('data-i18n-alt')));
    }
    root.dispatchEvent(new CustomEvent('i18n:changed', { detail: { language: lang } }));
  }

  function setLanguage(code) {
    code = String(code || '').toLowerCase().split('-')[0];
    if (supported.indexOf(code) === -1) code = 'en';
    lang = code;
    var store = storage();
    try { if (store) store.setItem('language', code); } catch (_) { /* private mode */ }
    return load(code).then(function () { apply(); return code; });
  }

  function init() {
    var store = storage();
    var saved = store && store.getItem('language');
    var browser = ((root.navigator && root.navigator.language) || 'en').split('-')[0];
    lang = supported.indexOf(saved) !== -1 ? saved : (supported.indexOf(browser) !== -1 ? browser : 'en');
    return Promise.all([load('en'), load(lang)]).then(function () { apply(); });
  }

  root.OmniI18n = {
    t: t,
    setLanguage: setLanguage,
    init: init,
    load: load,
    loaded: loaded,
    apply: apply,
    cache: cache,
    supported: supported,
    get language() { return lang; },
    base: base
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})(window);
