/**
 * OmniSource JavaScript SDK — CommonJS build.
 *
 * Mirrors omnisource.mjs so the SDK can be consumed from Node CJS projects
 * (older build pipelines, AWS Lambda, etc.). The implementation lives in a
 * single closure that exposes the same public API as the ESM build.
 */
'use strict';

class OmniSourceError extends Error {
  constructor(message, info) {
    super(message);
    this.name = 'OmniSourceError';
    if (info) {
      this.status = info.status;
      this.url = info.url;
      this.body = info.body;
    }
  }
}

const DEFAULT_BASE_URL = 'https://iamsmmh.github.io/OmniSource';
const DEFAULT_TIMEOUT = 8000;

class OmniSource {
  constructor(options) {
    options = options || {};
    this.baseURL = (options.baseURL || DEFAULT_BASE_URL).replace(/\/+$/, '');
    this.timeout = options.timeout || DEFAULT_TIMEOUT;
    this.lastError = null;
    this.fetch = options.fetch || ((url, init) => {
      if (typeof fetch === 'function') return fetch(url, init);
      return Promise.reject(new Error('No fetch implementation available'));
    });
  }

  _get(path) {
    const url = `${this.baseURL}/${path.replace(/^\/+/, '')}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);
    const self = this;
    return this.fetch(url, { signal: controller.signal, headers: { Accept: 'application/json' } })
      .then(res => {
        if (!res.ok) {
          return res.text().then(body => {
            self.lastError = new OmniSourceError(`Request failed (${res.status})`, { status: res.status, url, body });
            throw self.lastError;
          });
        }
        self.lastError = null;
        return res.json();
      })
      .catch(err => {
        if (!(err instanceof OmniSourceError)) {
          self.lastError = new OmniSourceError(err.message || 'Network error', { url });
        }
        throw self.lastError;
      })
      .finally(() => clearTimeout(timer));
  }

  _safe(path, fallback) {
    return this._get(path).catch(() => fallback);
  }

  _fuzzy(q, value) {
    if (!value) return 0;
    if (value === q) return 1;
    if (value.startsWith(q)) return 0.85;
    if (value.includes(q)) return 0.65;
    const tokens = q.split(/\s+/).filter(Boolean);
    const hits = tokens.filter(t => value.includes(t)).length;
    if (!hits) return 0;
    return 0.45 * (hits / tokens.length);
  }

  search(query, options) {
    options = options || {};
    const limit = options.limit || 12;
    const verifiedOnly = !!options.verifiedOnly;
    return this._safe('feeds/search-index.json', { documents: [], fuse: { keys: [] } })
      .then(data => {
        const keys = (data.fuse && data.fuse.keys) || [];
        const q = String(query || '').toLowerCase().trim();
        if (q.length < 2) return [];
        const results = [];
        for (const doc of data.documents || []) {
          let score = 0;
          for (const key of keys) {
            const field = doc[key.name];
            if (Array.isArray(field)) {
              for (const v of field) score += key.weight * this._fuzzy(q, String(v).toLowerCase());
            } else {
              score += key.weight * this._fuzzy(q, String(field || '').toLowerCase());
            }
          }
          if (score >= 0.4) results.push({ doc, score });
        }
        results.sort((a, b) => b.score - a.score);
        let out = results.slice(0, limit).map(item => item.doc);
        if (verifiedOnly) out = out.filter(d => d.verificationLevel === 'VERIFIED');
        return out;
      });
  }

  getApp(slug) {
    return Promise.all([
      this._safe('discovery.json', { apps: [] }),
      this._safe('feeds/install.json', { apps: [] })
    ]).then(([discovery, install]) => {
      const meta = (discovery.apps || []).find(app => (app.slug || app.id) === slug);
      if (!meta) return null;
      const installCard = (install.apps || []).find(card => card.slug === slug);
      return { ...meta, install: installCard ? installCard.cards : [] };
    });
  }

  listApps(options) {
    options = options || {};
    return this._safe('discovery.json', { apps: [] }).then(data =>
      (data.apps || []).filter(app => {
        if (options.category && app.category !== options.category) return false;
        if (options.status && app.status !== options.status) return false;
        return true;
      })
    );
  }

  getTrending() { return this._safe('feeds/trending.json', { trending: [], rising: [], recentlyUpdated: [] }); }
  getRelated(slug) {
    return this._safe('feeds/related.json', { related: {} }).then(data =>
      data.related && data.related[slug] ? data.related[slug] : []
    );
  }
  getReputation() { return this._safe('feeds/reputation.json', { sources: [] }); }
  getHealth() { return this._safe('feeds/download-intelligence.json', { apps: [], summary: {} }); }
  getAnalytics() { return this._safe('feeds/analytics.json', { totals: {} }); }
  getCommunity() { return this._safe('feeds/community.json', { popular: [], recentlyAdded: [], rising: [], requested: [] }); }
  getInstall(slug) {
    return this._safe('feeds/install.json', { apps: [], master: { cards: [] } }).then(data => {
      if (!slug) return data.master;
      const entry = (data.apps || []).find(item => item.slug === slug);
      return entry ? entry.cards : [];
    });
  }
  getCompare(left, right) {
    return this._safe('feeds/compare.json', { pairs: [] }).then(data =>
      (data.pairs || []).find(p =>
        (p.left.slug === left && p.right.slug === right) ||
        (p.left.slug === right && p.right.slug === left)
      )
    );
  }
  getSearchIndex() { return this._safe('feeds/search-index.json', { documents: [] }); }
}

module.exports = OmniSource;
module.exports.OmniSource = OmniSource;
module.exports.OmniSourceError = OmniSourceError;
module.exports.default = OmniSource;
