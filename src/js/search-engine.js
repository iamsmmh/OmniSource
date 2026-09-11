/* =============================================================================
 * OmniSource Search Engine
 * -----------------------------------------------------------------------------
 * Built-in fuzzy search (no external dependencies) that mirrors Fuse.js-style
 * scoring. Supports:
 *   • Exact matches (highest rank)
 *   • Alias matches (e.g. "yt" → YouTube family)
 *   • Prefix/substring matches
 *   • Typo tolerance (Levenshtein distance ≤ 2 for tokens ≥ 4 chars)
 *   • Tag/category/developer/bundle-ID matching
 *   • Field-weighted scoring (name > bundleId > developer > tags > description)
 *
 * Ranking order:
 *   1. Exact match              (bonus 1000)
 *   2. Prefix / startsWith      (bonus 400)
 *   3. Alias match              (bonus 300)
 *   4. Tag / category match     (bonus 200)
 *   5. Developer match          (bonus 150)
 *   6. Bundle ID match          (bonus 250)
 *   7. Fuzzy similarity         (0-100 based on Levenshtein)
 *   + recency boost (recently updated) + trending boost + verification boost
 * ============================================================================= */
(function (global) {
  'use strict';

  // Levenshtein distance (iterative, O(n·m)). Only called on short strings.
  function levenshtein(a, b, cap) {
    if (a === b) return 0;
    if (!a.length) return b.length;
    if (!b.length) return a.length;
    cap = cap || Math.max(a.length, b.length);
    var prev = new Array(b.length + 1);
    var curr = new Array(b.length + 1);
    for (var j = 0; j <= b.length; j++) prev[j] = j;
    for (var i = 1; i <= a.length; i++) {
      curr[0] = i;
      var minRow = curr[0];
      for (var j2 = 1; j2 <= b.length; j2++) {
        var cost = a.charCodeAt(i - 1) === b.charCodeAt(j2 - 1) ? 0 : 1;
        curr[j2] = Math.min(curr[j2 - 1] + 1, prev[j2] + 1, prev[j2 - 1] + cost);
        if (curr[j2] < minRow) minRow = curr[j2];
      }
      if (minRow > cap) return cap + 1;
      var tmp = prev; prev = curr; curr = tmp;
    }
    return prev[b.length];
  }

  // Tokenizer: lowercase, split on non-alnum, keep alphanumerics.
  function tokenize(s) {
    return String(s || '').toLowerCase()
      .replace(/[^a-z0-9+]+/g, ' ')
      .split(/\s+/)
      .filter(Boolean);
  }

  // Normalize for comparison (strip non-alnum, lowercase, collapse +).
  function norm(s) {
    return String(s || '').toLowerCase().replace(/[^a-z0-9+]/g, '');
  }

  // Compute a per-field fuzzy score (0-100). 100 = perfect.
  function fieldScore(query, fieldValue, maxDist) {
    var q = norm(query);
    var f = norm(fieldValue);
    if (!q || !f) return 0;
    if (f === q) return 100;
    if (f.indexOf(q) === 0) return 85;
    if (f.indexOf(q) !== -1) return 70;
    if (q.length < 3) return 0;
    var best = 0;
    // Slide over "words" within the field to allow matching within longer strings.
    var words = String(fieldValue).toLowerCase().split(/[^a-z0-9+]+/).filter(Boolean);
    for (var i = 0; i < words.length; i++) {
      var w = words[i];
      if (w === q) { best = Math.max(best, 100); continue; }
      if (w.indexOf(q) === 0) { best = Math.max(best, 82); continue; }
      if (w.indexOf(q) !== -1) { best = Math.max(best, 65); continue; }
      if (w.length >= q.length && q.length >= 3) {
        var d = levenshtein(q, w, maxDist || 2);
        if (d <= (maxDist || 2)) {
          var sc = Math.round(100 - (d * 20) - Math.abs(w.length - q.length) * 3);
          best = Math.max(best, sc);
        }
      }
    }
    return best;
  }

  // Field weights (tuned for "youtube music" prioritizing YT Music over uYou).
  var WEIGHTS = {
    name: 1.0,
    bundleId: 0.9,
    developerName: 0.55,
    category: 0.5,
    tags: 0.7,
    subtitle: 0.4,
    description: 0.1,
  };

  function daysSince(iso) {
    if (!iso) return 365;
    var t = Date.parse(iso);
    if (isNaN(t)) return 365;
    return Math.max(0, (Date.now() - t) / 86400000);
  }

  function SearchEngine() {
    this.ready = false;
    this.apps = [];
    this.aliases = { list: {}, reverse: {} };
  }

  SearchEngine.prototype.boot = function () {
    var self = this;
    return (global.OmniData ? global.OmniData.ready() : Promise.reject(new Error('OmniData not loaded')))
      .then(function () {
        self.apps = global.OmniData.getApps();
        self.aliases = global.OmniData.getAliases();
        self.ready = true;
        return self;
      });
  };

  // Core search. Returns results sorted by composite score.
  SearchEngine.prototype.search = function (rawQuery, opts) {
    if (!this.ready) return [];
    var opts_ = opts || {};
    var q = String(rawQuery || '').trim();
    if (!q) return opts_.returnAll ? this.apps.slice() : [];
    var qNorm = norm(q);
    var qLow = q.toLowerCase();
    var qTokens = tokenize(q);
    var maxDist = q.length >= 6 ? 2 : (q.length >= 4 ? 1 : 0);
    var aliases = this.aliases.reverse || {};

    var results = [];
    for (var i = 0; i < this.apps.length; i++) {
      var app = this.apps[i];
      var score = 0;
      var matches = [];

      // --- Field matching ---
      var fields = {
        name: app.name,
        bundleId: app.bundleId,
        developerName: app.developerName,
        category: app.category,
        tags: (app.tags || []).join(' '),
        subtitle: app.subtitle || app.shortDescription || '',
        description: app.description || '',
      };
      for (var key in WEIGHTS) {
        var fs = fieldScore(q, fields[key] || '', maxDist);
        if (fs > 0) {
          score += fs * WEIGHTS[key];
          matches.push(key);
        }
      }

      // --- Exact / prefix bonuses ---
      var nameNorm = norm(app.name);
      if (nameNorm === qNorm) score += 1000;
      else if (nameNorm.indexOf(qNorm) === 0) score += 400;
      var bundleNorm = norm(app.bundleId || '');
      if (bundleNorm === qNorm) score += 600;
      else if (bundleNorm.indexOf(qNorm) !== -1) score += 250;

      // --- Alias match ---
      var aliasHit = aliases[qLow] || aliases[qNorm];
      if (aliasHit && aliasHit.indexOf(app.slug) !== -1) {
        score += 300;
        matches.push('alias');
      }

      // --- Multi-token: every token must match at least one field, add token scores ---
      if (qTokens.length > 1) {
        var allHit = true;
        var tokenScore = 0;
        for (var t = 0; t < qTokens.length; t++) {
          var tok = qTokens[t];
          var tokBest = 0;
          for (var k in WEIGHTS) {
            var fv = String(fields[k] || '');
            if (norm(fv).indexOf(tok) !== -1) tokBest = Math.max(tokBest, 80 * WEIGHTS[k]);
            else tokBest = Math.max(tokBest, fieldScore(tok, fv, 1) * WEIGHTS[k]);
          }
          // alias check per token
          var aliasTok = aliases[tok];
          if (aliasTok && aliasTok.indexOf(app.slug) !== -1) tokBest = Math.max(tokBest, 300);
          if (tokBest < 20) { allHit = false; break; }
          tokenScore += tokBest;
        }
        if (allHit) score += tokenScore + 200;
        else score -= 100; // missing-token penalty
      }

      // --- Tag / category / developer exact bonuses ---
      var tagStr = (app.tags || []).join(' ').toLowerCase();
      var catStr = (app.category || '').toLowerCase();
      var devNorm = norm(app.developerName);
      if (tagStr.indexOf(qLow) !== -1) { score += 200; matches.push('tag'); }
      if (catStr === qLow || catStr.indexOf(qLow) === 0) { score += 180; matches.push('category'); }
      if (devNorm === qNorm || devNorm.indexOf(qNorm) !== -1) { score += 150; matches.push('developer'); }

      if (score <= 0) continue;

      // --- Boosts ---
      var verLevel = (app.verificationLevel || app.verification || '').toUpperCase();
      if (verLevel.indexOf('VERIFIED') !== -1) score += 30;
      var health = app.health || {};
      if (health.downloadReachable === false || health.reachable === false) score -= 80;
      if (app.featured) score += 20;

      // Recency boost — last 30 days gets up to +40.
      var days = daysSince(app.releaseDate);
      if (days < 30) score += Math.round(40 * (1 - days / 30));

      results.push({ app: app, score: score, matches: matches });
    }

    results.sort(function (a, b) { return b.score - a.score; });
    return results;
  };

  // Suggest completions for a prefix (for the search palette).
  SearchEngine.prototype.suggest = function (q, limit) {
    var limit_ = limit || 8;
    var res = this.search(q);
    var out = [];
    var seen = Object.create(null);
    for (var i = 0; i < res.length && out.length < limit_; i++) {
      var app = res[i].app;
      if (seen[app.slug]) continue;
      seen[app.slug] = 1;
      out.push(app);
    }
    return out;
  };

  global.OmniSearch = new SearchEngine();

  // Auto-boot after data layer.
  if (global.OmniData) {
    global.OmniData.ready().then(function () { return global.OmniSearch.boot(); }).catch(function (e) {
      console.warn('[search] boot failed', e);
    });
  }
})(window);
