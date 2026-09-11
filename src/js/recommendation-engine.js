/* =============================================================================
 * OmniSource Recommendation Engine
 * -----------------------------------------------------------------------------
 * Client-side recommendation complement to the server-generated feeds/trending.json
 * and feeds/related.json. Provides:
 *   • Related apps  (same category, developer, source, tags, bundle family)
 *   • Alternatives  (same category + high score; for "if you like X, try …")
 *   • Trending      (uses pre-computed scores from feeds/trending.json)
 *   • "Also from"   (same developer)
 *
 * The server already emits a solid related.json; this engine fills in any
 * missing context at runtime (e.g. after client-side filtering) and adds the
 * alternatives logic that the static feeds don't precompute for every slug.
 * ============================================================================= */
(function (global) {
  'use strict';

  var jaccard = function (a, b) {
    if (!a || !b || !a.length || !b.length) return 0;
    var A = new Set(a); var B = new Set(b);
    var inter = 0;
    A.forEach(function (x) { if (B.has(x)) inter++; });
    return inter / (A.size + B.size - inter);
  };

  var RecEngine = {
    ready: false,
    apps: [],
    bySlug: new Map(),
    byCategory: new Map(),
    byDeveloper: new Map(),
    byTag: new Map(),
    relatedCache: null,
    trendingCache: null,
  };

  RecEngine.boot = function () {
    var self = this;
    return (global.OmniData ? global.OmniData.ready() : Promise.reject(new Error('no data layer')))
      .then(function () {
        self.apps = global.OmniData.getApps();
        self.apps.forEach(function (app) {
          self.bySlug.set(app.slug, app);
          var cat = (app.category || 'other').toLowerCase();
          if (!self.byCategory.has(cat)) self.byCategory.set(cat, []);
          self.byCategory.get(cat).push(app);
          var dev = (app.developerName || '').toLowerCase();
          if (dev) {
            if (!self.byDeveloper.has(dev)) self.byDeveloper.set(dev, []);
            self.byDeveloper.get(dev).push(app);
          }
          (app.tags || []).forEach(function (t) {
            var k = t.toLowerCase();
            if (!self.byTag.has(k)) self.byTag.set(k, []);
            self.byTag.get(k).push(app);
          });
        });
        self.relatedCache = global.OmniData.getRelated();
        self.trendingCache = global.OmniData.getTrending();
        self.ready = true;
        return self;
      });
  };

  // Compute related apps for a given slug.
  RecEngine.related = function (slug, limit) {
    if (!this.ready) return [];
    var me = this.bySlug.get(slug);
    if (!me) return [];
    var limit_ = limit || 8;

    // Prefer server-side related.json when available (it uses richer data).
    var serverRelated = this.relatedCache && this.relatedCache.related && this.relatedCache.related[slug];
    if (Array.isArray(serverRelated) && serverRelated.length) {
      var out = [];
      for (var i = 0; i < serverRelated.length && out.length < limit_; i++) {
        var s = typeof serverRelated[i] === 'string' ? serverRelated[i] : (serverRelated[i].slug || serverRelated[i].id);
        var a = this.bySlug.get(s);
        if (a && a.slug !== slug) out.push(a);
      }
      if (out.length) return out;
    }

    // Fall back to computing client-side.
    var scored = [];
    var myTags = (me.tags || []).map(function (t) { return t.toLowerCase(); });
    var myDev = (me.developerName || '').toLowerCase();
    var myCat = (me.category || '').toLowerCase();
    var myBundle = (me.bundleId || '').split('.').slice(0, 3).join('.'); // e.g. com.google.ios

    this.apps.forEach(function (other) {
      if (other.slug === slug) return;
      var score = 0;
      // Same category
      if ((other.category || '').toLowerCase() === myCat) score += 2;
      // Same developer
      if ((other.developerName || '').toLowerCase() === myDev && myDev) score += 5;
      // Shared tags (Jaccard)
      var theirTags = (other.tags || []).map(function (t) { return t.toLowerCase(); });
      score += jaccard(myTags, theirTags) * 8;
      // Shared bundle prefix (fork/tweak family)
      var theirBundle = (other.bundleId || '').split('.').slice(0, 3).join('.');
      if (theirBundle && theirBundle === myBundle) score += 6;
      // Name overlap (e.g. YouTube, YTLite, uYouEnhanced)
      var theirName = other.name.toLowerCase();
      var myName = me.name.toLowerCase();
      // Partial word overlap
      var myWords = myName.split(/[^a-z0-9+]/).filter(function (w) { return w.length >= 4; });
      for (var w = 0; w < myWords.length; w++) {
        if (theirName.indexOf(myWords[w]) !== -1) { score += 3; break; }
      }
      if (score <= 0.5) return;
      scored.push({ app: other, score: score });
    });

    scored.sort(function (a, b) { return b.score - a.score; });
    return scored.slice(0, limit_).map(function (x) { return x.app; });
  };

  // Alternative apps: same category + different developer (competitors), high score.
  RecEngine.alternatives = function (slug, limit) {
    if (!this.ready) return [];
    var me = this.bySlug.get(slug);
    if (!me) return [];
    var limit_ = limit || 6;
    var myCat = (me.category || '').toLowerCase();
    var scored = [];
    var myTags = (me.tags || []).map(function (t) { return t.toLowerCase(); });

    this.apps.forEach(function (other) {
      if (other.slug === slug) return;
      var score = 0;
      if ((other.category || '').toLowerCase() === myCat) score += 3;
      var theirTags = (other.tags || []).map(function (t) { return t.toLowerCase(); });
      score += jaccard(myTags, theirTags) * 6;
      // Bonus for apps that share name/keyword tokens (same ecosystem).
      var theirName = other.name.toLowerCase();
      var myWords = me.name.toLowerCase().split(/[^a-z0-9+]/).filter(function (w) { return w.length >= 4; });
      for (var w = 0; w < myWords.length; w++) {
        if (theirName.indexOf(myWords[w]) !== -1) score += 2;
      }
      // Penalise same-developer (those go in "also from").
      if ((other.developerName || '').toLowerCase() === (me.developerName || '').toLowerCase()) score -= 4;
      if (score <= 1) return;
      // Verification boost
      var v = (other.verificationLevel || '').toUpperCase();
      if (v.indexOf('VERIFIED') !== -1) score += 2;
      scored.push({ app: other, score: score });
    });

    scored.sort(function (a, b) { return b.score - a.score; });
    return scored.slice(0, limit_).map(function (x) { return x.app; });
  };

  // "Also from X developer"
  RecEngine.alsoFromDeveloper = function (slug, limit) {
    if (!this.ready) return [];
    var me = this.bySlug.get(slug);
    if (!me) return [];
    var dev = (me.developerName || '').toLowerCase();
    if (!dev) return [];
    var list = (this.byDeveloper.get(dev) || []).filter(function (a) { return a.slug !== slug; });
    return list.slice(0, limit || 4);
  };

  // Trending: prefer server-calculated scores.
  RecEngine.trending = function (limit) {
    var limit_ = limit || 10;
    var t = this.trendingCache;
    if (t && Array.isArray(t.trending) && t.trending.length) {
      var out = [];
      for (var i = 0; i < t.trending.length && out.length < limit_; i++) {
        var slug = t.trending[i].slug;
        var app = this.bySlug.get(slug);
        if (app) out.push(app);
      }
      return out;
    }
    // Fallback: sort by release date (newest first).
    return this.apps
      .slice()
      .sort(function (a, b) { return String(b.releaseDate || '').localeCompare(String(a.releaseDate || '')); })
      .slice(0, limit_);
  };

  RecEngine.recentlyUpdated = function (limit) {
    var limit_ = limit || 10;
    var t = this.trendingCache;
    if (t && Array.isArray(t.recentlyUpdated)) {
      var out = [];
      for (var i = 0; i < t.recentlyUpdated.length && out.length < limit_; i++) {
        var app = this.bySlug.get(t.recentlyUpdated[i].slug);
        if (app) out.push(app);
      }
      if (out.length) return out;
    }
    return this.apps
      .slice()
      .sort(function (a, b) { return String(b.releaseDate || '').localeCompare(String(a.releaseDate || '')); })
      .slice(0, limit_);
  };

  global.OmniRecs = RecEngine;

  if (global.OmniData) {
    global.OmniData.ready().then(function () { return RecEngine.boot(); }).catch(function (e) {
      console.warn('[recs] boot failed', e);
    });
  }
})(window);
