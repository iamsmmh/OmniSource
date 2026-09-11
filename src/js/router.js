/* =============================================================================
 * OmniSource Client-Side Router
 * -----------------------------------------------------------------------------
 * Lightweight History-API router so URLs like /compare?app1=x&app2=y, /app/{slug},
 * /discover, /graph and /status share one shell and lazy-load their engines.
 * Static legacy pages (/apps/<slug>/index.html) keep working as direct URLs
 * (they're real files on disk). The router only intercepts in-page navigation
 * on the modern single-page surfaces and on the home page.
 * ============================================================================= */
(function (global) {
  'use strict';

  var routes = [];
  var notFound = null;

  function parsePath(pathname) {
    // Strip the GitHub Pages base path if served under /OmniSource/.
    var base = (document.querySelector('base[href]') && document.querySelector('base[href]').getAttribute('href')) || '/';
    var basePath = base.replace(/^https?:\/\/[^/]+/, '').replace(/\/[^/]*$/, '/');
    var path = pathname || location.pathname;
    if (basePath !== '/' && path.indexOf(basePath) === 0) path = path.slice(basePath.length - 1);
    if (path.charAt(0) !== '/') path = '/' + path;
    return path.replace(/\/+$/, '') || '/';
  }

  function match(path) {
    for (var i = 0; i < routes.length; i++) {
      var r = routes[i];
      var m = path.match(r.pattern);
      if (m) return { route: r, params: r.keys ? extractParams(r, m) : m.slice(1) };
    }
    return null;
  }

  function extractParams(route, match) {
    var params = {};
    for (var i = 0; i < route.keys.length; i++) {
      params[route.keys[i]] = decodeURIComponent(match[i + 1] || '');
    }
    return params;
  }

  function compile(pattern) {
    // Simple :param segments
    var keys = [];
    var regex = pattern.replace(/:([a-zA-Z_]+)/g, function (_, k) {
      keys.push(k);
      return '([^/]+)';
    });
    return { pattern: new RegExp('^' + regex + '$'), keys: keys };
  }

  var Router = {
    registered: false,
    current: null,

    on: function (pattern, handler) {
      var compiled = compile(pattern);
      routes.push({ pattern: compiled.pattern, keys: compiled.keys, handler: handler, raw: pattern });
      return this;
    },

    otherwise: function (handler) { notFound = handler; return this; },

    start: function () {
      var self = this;
      if (this.registered) return;
      this.registered = true;
      window.addEventListener('popstate', function () { self.handle(); });
      // Intercept in-app <a> clicks that match a route.
      document.addEventListener('click', function (e) {
        if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        var a = e.target.closest('a');
        if (!a) return;
        var href = a.getAttribute('href');
        if (!href || href.charAt(0) === '#' || a.target === '_blank' || a.hasAttribute('download')) return;
        if (/^[a-z][a-z0-9+.-]*:/i.test(href) && href.indexOf(location.origin) !== 0) return;
        var url = new URL(href, location.href);
        if (url.origin !== location.origin) return;
        var path = parsePath(url.pathname);
        var m = match(path);
        if (m) {
          e.preventDefault();
          history.pushState(null, '', url.pathname + url.search + url.hash);
          self.handle();
        }
      });
      self.handle();
    },

    handle: function () {
      var path = parsePath(location.pathname);
      var m = match(path);
      if (m) {
        this.current = { path: path, params: m.params };
        try { m.route.handler({ params: m.params, path: path, search: location.search }); }
        catch (err) { console.error('[router] handler error', err); }
      } else if (notFound) {
        notFound({ path: path });
      }
    },

    navigate: function (url, replace) {
      if (replace) history.replaceState(null, '', url);
      else history.pushState(null, '', url);
      this.handle();
    },
  };

  // Helper: parse query params like ?app1=x&app2=y.
  Router.query = function (search) {
    return new URLSearchParams(search || location.search);
  };

  Router.parsePath = parsePath;
  global.OmniRouter = Router;
})(window);
