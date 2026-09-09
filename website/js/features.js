/**
 * OmniSource Features Module
 * Implements P0-P3 features: Favorites, Collections, Webhooks, Compare, QR, Search, Ratings, Charts, Notifications
 * 
 * This is a vanilla JS module that works with the existing core.js and site.js
 */

(function() {
  'use strict';

  // ============================================================================
  // UTILITIES
  // ============================================================================

  const OS = window.OS || {};
  window.OS = OS;

  // Storage utilities with namespace
  const Storage = {
    get: (key, defaultValue = null) => {
      try {
        const item = localStorage.getItem(`os:${key}`);
        return item ? JSON.parse(item) : defaultValue;
      } catch {
        return defaultValue;
      }
    },
    set: (key, value) => {
      try {
        localStorage.setItem(`os:${key}`, JSON.stringify(value));
      } catch (e) {
        console.warn('LocalStorage not available:', e);
      }
    },
    remove: (key) => {
      try {
        localStorage.removeItem(`os:${key}`);
      } catch {}
    }
  };

  // Generate unique IDs
  const generateId = () => {
    return Date.now().toString(36) + Math.random().toString(36).substring(2);
  };

  // Debounce utility
  const debounce = (fn, delay = 200) => {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn(...args), delay);
    };
  };

  // ============================================================================
  // EVENT BUS
  // ============================================================================

  const EventBus = {
    _events: {},
    on: (event, callback) => {
      if (!EventBus._events[event]) {
        EventBus._events[event] = [];
      }
      EventBus._events[event].push(callback);
    },
    off: (event, callback) => {
      const listeners = EventBus._events[event];
      if (listeners) {
        EventBus._events[event] = listeners.filter(l => l !== callback);
      }
    },
    emit: (event, ...args) => {
      const listeners = EventBus._events[event];
      if (listeners) {
        listeners.forEach(l => l(...args));
      }
    }
  };

  OS.on = EventBus.on;
  OS.emit = EventBus.emit;

  // ============================================================================
  // FAVORITES / WATCHLIST (P0)
  // ============================================================================

  const Favorites = {
    STORAGE_KEY: 'favorites',
    
    init() {
      // Ensure favorites exist
      if (!Storage.get(this.STORAGE_KEY)) {
        Storage.set(this.STORAGE_KEY, []);
      }
      this._injectUI();
      this._loadFromURL();
    },

    _injectUI() {
      // Add favorite button to app cards
      const style = document.createElement('style');
      style.textContent = `
        .favorite-btn {
          cursor: pointer;
          border: 0;
          background: none;
          padding: 4px;
          color: var(--faint);
          border-radius: 8px;
          transition: color 0.15s ease, transform 0.15s ease;
        }
        .favorite-btn:hover {
          color: var(--accent);
          transform: scale(1.1);
        }
        .favorite-btn.active {
          color: var(--accent);
        }
        .favorite-btn.active svg {
          fill: currentColor;
        }
        .favorite-btn svg {
          width: 18px;
          height: 18px;
          fill: none;
          stroke: currentColor;
          stroke-width: 1.7;
          stroke-linecap: round;
          stroke-linejoin: round;
        }
        .favorites-count {
          font: 700 10px var(--font-mono);
          background: var(--accent-soft);
          color: var(--accent);
          padding: 2px 8px;
          border-radius: 999px;
          margin-left: 8px;
        }
        .favorites-nav-item {
          position: relative;
        }
        .favorites-nav-item .favorites-count {
          position: absolute;
          top: -4px;
          right: -4px;
        }
      `;
      document.head.appendChild(style);

      // Add favorites nav link
      this._injectNavLink();
    },

    _injectNavLink() {
      const navLinks = document.querySelector('.nav-links');
      if (!navLinks) return;

      const favoritesLink = document.createElement('a');
      favoritesLink.href = '/favorites/';
      favoritesLink.textContent = 'Favorites';
      favoritesLink.className = 'favorites-nav-item';
      favoritesLink.setAttribute('aria-current', 'false');
      favoritesLink.innerHTML = `
        <span>Favorites</span>
        <span class="favorites-count" id="favorites-count">0</span>
      `;

      // Insert before the last nav link (or append)
      const links = navLinks.querySelectorAll('a');
      if (links.length > 0) {
        navLinks.insertBefore(favoritesLink, links[links.length - 1]);
      } else {
        navLinks.appendChild(favoritesLink);
      }

      // Update count on load
      this.updateCount();
    },

    _loadFromURL() {
      // Check if URL has favorite param
      const params = new URLSearchParams(window.location.search);
      if (params.has('favorite')) {
        const appId = params.get('favorite');
        this.toggle(appId, true);
      }
    },

    getAll() {
      return Storage.get(this.STORAGE_KEY, []);
    },

    has(appId) {
      return this.getAll().includes(appId);
    },

    add(appId) {
      const favorites = this.getAll();
      if (!favorites.includes(appId)) {
        favorites.push(appId);
        Storage.set(this.STORAGE_KEY, favorites);
        this.updateCount();
        OS.emit('favorites:updated', this.getAll());
        return true;
      }
      return false;
    },

    remove(appId) {
      const favorites = this.getAll();
      const index = favorites.indexOf(appId);
      if (index > -1) {
        favorites.splice(index, 1);
        Storage.set(this.STORAGE_KEY, favorites);
        this.updateCount();
        OS.emit('favorites:updated', this.getAll());
        return true;
      }
      return false;
    },

    toggle(appId, force) {
      const has = this.has(appId);
      if (force === true && !has) {
        return this.add(appId);
      }
      if (force === false && has) {
        return this.remove(appId);
      }
      return has ? this.remove(appId) : this.add(appId);
    },

    updateCount() {
      const count = this.getAll().length;
      const countEl = document.getElementById('favorites-count');
      if (countEl) {
        countEl.textContent = count;
        countEl.style.display = count > 0 ? 'inline' : 'none';
      }
    },

    injectButtons(container = document) {
      // Add favorite buttons to app cards
      const appCards = container.querySelectorAll('.app-card, .rail-card, .featured-card, .result-row');
      appCards.forEach(card => {
        if (card.querySelector('.favorite-btn')) return;

        const appId = this._getAppId(card);
        if (!appId) return;

        const btn = document.createElement('button');
        btn.className = 'favorite-btn';
        btn.setAttribute('aria-label', 'Add to favorites');
        btn.setAttribute('data-app-id', appId);
        btn.innerHTML = `
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
          </svg>
        `;

        if (this.has(appId)) {
          btn.classList.add('active');
          btn.setAttribute('aria-label', 'Remove from favorites');
        }

        btn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          this.toggle(appId);
          btn.classList.toggle('active');
          const isActive = btn.classList.contains('active');
          btn.setAttribute('aria-label', isActive ? 'Remove from favorites' : 'Add to favorites');
        });

        // Find the best place to insert the button
        const actions = card.querySelector('.card-actions, .actions');
        if (actions) {
          actions.prepend(btn);
        } else {
          // Try to insert near the icon or title
          const icon = card.querySelector('.app-icon, .icon-wrap, img');
          if (icon) {
            icon.after(btn);
          }
        }
      });
    },

    _getAppId(card) {
      // Try to get app ID from various attributes
      const href = card.getAttribute('href');
      if (href && href.includes('/apps/')) {
        const match = href.match(/\/apps\/([^\/]+)/);
        if (match) return match[1];
      }

      // Check for data attributes
      const dataId = card.getAttribute('data-app-id') ||
                    card.getAttribute('data-id') ||
                    card.getAttribute('id');
      if (dataId) return dataId;

      // Try to extract from the card structure
      const title = card.querySelector('h3, h2, .card-identity h3');
      if (title) {
        const text = title.textContent.trim().toLowerCase().replace(/\s+/g, '-');
        return text;
      }

      return null;
    },

    getFavoritesPageHTML() {
      const favorites = this.getAll();
      const appData = this._loadAppData();
      const favoriteApps = appData.filter(app => favorites.includes(app.id));

      return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>My Favorites - OmniSource</title>
          <link rel="stylesheet" href="${OS.asset('css/site.css')}">
          <link rel="stylesheet" href="${OS.asset('css/design-system.css')}">
        </head>
        <body>
          <header class="site-header" id="site-header">
            <div class="nav shell">
              <a href="${OS.asset('/')}" class="brand">
                <img src="${OS.asset('assets/OmniSource.png')}" alt="OmniSource" width="40" height="40">
                <span>OmniSource</span>
              </a>
              <nav class="nav-links">
                <a href="${OS.asset('/')}">Home</a>
                <a href="${OS.asset('/compare/')}">Compare</a>
                <a href="${OS.asset('/status/')}">Status</a>
                <a href="${OS.asset('/analytics/')}">Analytics</a>
                <a href="${OS.asset('/install/')}">Install</a>
                <a href="${OS.asset('/favorites/')}" class="active" aria-current="page">
                  <span>Favorites</span>
                  <span class="favorites-count">${favorites.length}</span>
                </a>
              </nav>
              <div class="nav-controls">
                <button id="themeButton" class="icon-button" aria-label="Toggle theme">
                  <svg class="icon-sun" viewBox="0 0 24 24"><path d="M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10zm0 2a7 7 0 1 1 0-14 7 7 0 0 1 0 14z"/></svg>
                  <svg class="icon-moon" viewBox="0 0 24 24"><path d="M12 3a9 9 0 1 0 9 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 0 1-4.4 2.26 5.403 5.403 0 0 1-3.14-9.8c-.44-.06-.9-.1-1.36-.1z"/></svg>
                </button>
              </div>
            </div>
          </header>
          
          <main class="shell">
            <div class="section">
              <div class="section-heading">
                <h1>My Favorites</h1>
                <p class="lead">${favoriteApps.length} app${favoriteApps.length !== 1 ? 's' : ''} saved</p>
              </div>
              
              ${favoriteApps.length === 0 ? `
                <div class="empty-state">
                  <div class="empty-icon">❤️</div>
                  <h3>No favorites yet</h3>
                  <p>Start adding apps to your favorites by clicking the heart icon on any app card.</p>
                  <a href="${OS.asset('/')}" class="button primary">Browse Apps</a>
                </div>
              ` : `
                <div class="apps-grid">
                  ${favoriteApps.map(app => this._renderAppCard(app)).join('')}
                </div>
              `}
            </div>
          </main>
          
          <footer class="footer">
            <div class="footer-inner shell">
              <div class="footer-brand">
                <img src="${OS.asset('assets/OmniSource.png')}" alt="OmniSource" width="40" height="40">
                <div>
                  <strong>OmniSource</strong>
                  <p>The App Store for sideloaded iOS.</p>
                </div>
              </div>
              <p class="fine-print">
                OmniSource is an independent community project. All apps, code and trademarks belong to their respective owners.
              </p>
            </div>
          </footer>
          
          <script src="${OS.asset('js/core.js')}"></script>
          <script>
            // Initialize favorites on this page
            document.addEventListener('DOMContentLoaded', () => {
              OS.Favorites.injectButtons();
              OS.Favorites.updateCount();
            });
          </script>
        </body>
        </html>
      `;
    },

    _loadAppData() {
      // Load from the catalog or feeds
      // This is a simplified version - in practice, we'd fetch from /api/catalog.json
      try {
        const catalog = window.OS_CATALOG || [];
        return catalog.map(app => ({
          id: app.slug || app.id,
          name: app.name,
          description: app.description,
          icon: app.icon,
          developer: app.developer,
          version: app.version,
          updated: app.updated,
          status: app.status,
          bundleId: app.bundleIdentifier,
          source: app.source
        }));
      } catch {
        return [];
      }
    },

    _renderAppCard(app) {
      return `
        <article class="app-card" data-app-id="${app.id}">
          <div class="card-top">
            <div class="icon-wrap">
              <img src="${OS.asset(app.icon || 'assets/unknown.png')}" alt="${app.name}" class="app-icon" width="58" height="58">
            </div>
            <div class="card-identity">
              <h3><a href="${OS.asset(`/apps/${app.id}/`)}">${app.name}</a></h3>
              <p class="card-dev">${app.developer || 'Unknown'}</p>
            </div>
            <button class="favorite-btn active" aria-label="Remove from favorites" data-app-id="${app.id}">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
              </svg>
            </button>
          </div>
          <p class="app-description">${app.description || 'No description available.'}</p>
          <div class="card-meta">
            <span class="meta-item"><b>${app.version || 'N/A'}</b> version</span>
            <span class="meta-item"><b>${app.status || 'unknown'}</b> status</span>
            <span class="meta-item"><b>${app.source || 'N/A'}</b> source</span>
          </div>
        </article>
      `;
    }
  };

  // ============================================================================
  // APP COLLECTIONS (P0)
  // ============================================================================

  const Collections = {
    STORAGE_KEY: 'collections',

    init() {
      if (!Storage.get(this.STORAGE_KEY)) {
        // Create default collections
        const defaults = [
          { id: 'youtube-mods', name: 'YouTube Mods', description: 'Popular YouTube modifications', apps: [], color: '#ff0000' },
          { id: 'gaming-tools', name: 'Gaming Tools', description: 'Tools for mobile gaming', apps: [], color: '#00ff00' },
          { id: 'productivity', name: 'Productivity', description: 'Productivity apps and utilities', apps: [], color: '#0000ff' },
          { id: 'my-apps', name: 'My Apps', description: 'Apps I use regularly', apps: [], color: '#ff00ff' }
        ];
        Storage.set(this.STORAGE_KEY, defaults);
      }
      this._injectUI();
    },

    _injectUI() {
      const navLinks = document.querySelector('.nav-links');
      if (!navLinks) return;

      const collectionsLink = document.createElement('a');
      collectionsLink.href = '/collections/';
      collectionsLink.textContent = 'Collections';
      collectionsLink.className = 'collections-nav-item';

      const links = navLinks.querySelectorAll('a');
      if (links.length > 0) {
        navLinks.insertBefore(collectionsLink, links[links.length - 1]);
      }
    },

    getAll() {
      return Storage.get(this.STORAGE_KEY, []);
    },

    getById(id) {
      return this.getAll().find(c => c.id === id);
    },

    create(name, description = '', color = '#6d5ef5') {
      const collections = this.getAll();
      const id = generateId();
      const newCollection = { id, name, description, apps: [], color };
      collections.push(newCollection);
      Storage.set(this.STORAGE_KEY, collections);
      OS.emit('collections:updated', collections);
      return newCollection;
    },

    update(id, updates) {
      const collections = this.getAll();
      const index = collections.findIndex(c => c.id === id);
      if (index > -1) {
        collections[index] = { ...collections[index], ...updates };
        Storage.set(this.STORAGE_KEY, collections);
        OS.emit('collections:updated', collections);
        return collections[index];
      }
      return null;
    },

    delete(id) {
      const collections = this.getAll();
      const index = collections.findIndex(c => c.id === id);
      if (index > -1) {
        collections.splice(index, 1);
        Storage.set(this.STORAGE_KEY, collections);
        OS.emit('collections:updated', collections);
        return true;
      }
      return false;
    },

    addApp(collectionId, appId) {
      const collections = this.getAll();
      const index = collections.findIndex(c => c.id === collectionId);
      if (index > -1) {
        if (!collections[index].apps.includes(appId)) {
          collections[index].apps.push(appId);
          Storage.set(this.STORAGE_KEY, collections);
          OS.emit('collections:updated', collections);
          return true;
        }
      }
      return false;
    },

    removeApp(collectionId, appId) {
      const collections = this.getAll();
      const index = collections.findIndex(c => c.id === collectionId);
      if (index > -1) {
        const appIndex = collections[index].apps.indexOf(appId);
        if (appIndex > -1) {
          collections[index].apps.splice(appIndex, 1);
          Storage.set(this.STORAGE_KEY, collections);
          OS.emit('collections:updated', collections);
          return true;
        }
      }
      return false;
    },

    toggleApp(collectionId, appId) {
      const has = this.hasApp(collectionId, appId);
      return has ? this.removeApp(collectionId, appId) : this.addApp(collectionId, appId);
    },

    hasApp(collectionId, appId) {
      const collection = this.getById(collectionId);
      return collection && collection.apps.includes(appId);
    },

    getUserCollections() {
      return this.getAll().filter(c => !c.id.startsWith('default-'));
    },

    getCollectionsForApp(appId) {
      return this.getAll().filter(c => c.apps.includes(appId));
    }
  };

  // ============================================================================
  // BATCH COMPARE (P1)
  // ============================================================================

  const Compare = {
    MAX_APPS: 6,

    init() {
      this._injectUI();
      this._handleURLParams();
    },

    _injectUI() {
      // Add multi-select to compare page
      const comparePage = document.querySelector('.cmp-picker');
      if (comparePage) {
        this._enhanceComparePicker();
      }
    },

    _enhanceComparePicker() {
      const picker = document.querySelector('.cmp-picker');
      if (!picker) return;

      // Add "Add Another" button
      const addBtn = document.createElement('button');
      addBtn.className = 'button secondary';
      addBtn.textContent = '+ Add Another App';
      addBtn.style.marginLeft = '10px';
      addBtn.addEventListener('click', () => this.addComparisonSlot());

      const vsEl = picker.querySelector('.vs');
      if (vsEl) {
        vsEl.after(addBtn);
      } else {
        picker.appendChild(addBtn);
      }
    },

    _handleURLParams() {
      const params = new URLSearchParams(window.location.search);
      const apps = [];
      for (let i = 1; i <= this.MAX_APPS; i++) {
        const app = params.get(`app${i}`);
        if (app) apps.push(app);
      }
      
      if (apps.length > 2) {
        this.updateComparison(apps);
      }
    },

    addComparisonSlot() {
      const picker = document.querySelector('.cmp-picker');
      if (!picker) return;

      const selects = picker.querySelectorAll('select');
      if (selects.length >= this.MAX_APPS) {
        OS.toast('Maximum of ' + this.MAX_APPS + ' apps can be compared');
        return;
      }

      const label = document.createElement('label');
      const select = document.createElement('select');
      const span = document.createElement('span');
      
      span.textContent = 'App ' + (selects.length + 1);
      span.style.fontSize = '10px';
      span.style.color = 'var(--muted)';
      
      select.innerHTML = '<option value="">Select an app...</option>';
      // Populate with app options
      this._populateAppOptions(select);
      
      label.appendChild(span);
      label.appendChild(select);
      
      const lastSelect = selects[selects.length - 1];
      lastSelect.after(label);
    },

    _populateAppOptions(select) {
      // Get app list from catalog
      const apps = window.OS_CATALOG || [];
      apps.forEach(app => {
        const option = document.createElement('option');
        option.value = app.slug || app.id;
        option.textContent = app.name;
        select.appendChild(option);
      });
    },

    updateComparison(appIds) {
      const params = new URLSearchParams();
      appIds.slice(0, this.MAX_APPS).forEach((id, i) => {
        params.set(`app${i + 1}`, id);
      });
      
      const newUrl = window.location.pathname + '?' + params.toString();
      window.history.pushState({}, '', newUrl);
      
      // Reload comparison
      this.renderComparison(appIds);
    },

    renderComparison(appIds) {
      const container = document.querySelector('.cmp-result');
      if (!container) return;

      if (appIds.length < 2) {
        container.innerHTML = '<p>Select at least 2 apps to compare.</p>';
        return;
      }

      const apps = this._getAppData(appIds);
      container.innerHTML = this._renderComparisonTable(apps);
    },

    _getAppData(appIds) {
      const catalog = window.OS_CATALOG || [];
      return appIds.map(id => catalog.find(app => app.slug === id || app.id === id)).filter(Boolean);
    },

    _renderComparisonTable(apps) {
      const fields = [
        { key: 'name', label: 'App Name', type: 'text' },
        { key: 'version', label: 'Version', type: 'text' },
        { key: 'updated', label: 'Last Updated', type: 'date' },
        { key: 'status', label: 'Status', type: 'badge' },
        { key: 'bundleId', label: 'Bundle ID', type: 'code' },
        { key: 'developer', label: 'Developer', type: 'text' },
        { key: 'source', label: 'Source', type: 'text' },
        { key: 'size', label: 'Size', type: 'text' },
        { key: 'description', label: 'Description', type: 'text' }
      ];

      return `
        <div class="cmp-grid">
          ${apps.map(app => this._renderCompareCard(app, apps)).join('')}
        </div>
        
        <h3 style="margin-top: 40px;">Detailed Comparison</h3>
        <div class="cmp-table-container">
          <table class="cmp-table">
            <thead>
              <tr>
                <th>Property</th>
                ${apps.map(app => `<th>${app.name}</th>`).join('')}
              </tr>
            </thead>
            <tbody>
              ${fields.map(field => `
                <tr>
                  <td><strong>${field.label}</strong></td>
                  ${apps.map(app => `<td>${this._formatField(app[field.key], field.type)}</td>`).join('')}
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    },

    _renderCompareCard(app, allApps) {
      return `
        <div class="cmp-side">
          <header>
            <img src="${OS.asset(app.icon || 'assets/unknown.png')}" alt="${app.name}" width="68" height="68">
            <div>
              <h2>${app.name}</h2>
              <p>${app.developer || 'Unknown'}</p>
            </div>
          </header>
          <div class="cmp-details">
            <p><strong>Version:</strong> ${app.version || 'N/A'}</p>
            <p><strong>Updated:</strong> ${app.updated || 'N/A'}</p>
            <p><strong>Status:</strong> <span class="badge ${app.status || 'neutral'}">${app.status || 'Unknown'}</span></p>
            <p><strong>Bundle ID:</strong> <code>${app.bundleId || 'N/A'}</code></p>
            <p><strong>Source:</strong> ${app.source || 'N/A'}</p>
          </div>
          <a href="${OS.asset(`/apps/${app.slug}/`)}" class="button">View Details</a>
        </div>
      `;
    },

    _formatField(value, type) {
      if (!value) return 'N/A';
      
      switch (type) {
        case 'badge':
          return `<span class="badge ${value.toLowerCase()}">${value}</span>`;
        case 'code':
          return `<code>${value}</code>`;
        case 'date':
          return new Date(value).toLocaleDateString();
        default:
          return value;
      }
    }
  };

  // ============================================================================
  // QR CODE GENERATOR (P1)
  // ============================================================================

  const QRCode = {
    init() {
      this._injectUI();
      this._loadScript();
    },

    _injectUI() {
      // Add QR button to app pages and feed sections
      const style = document.createElement('style');
      style.textContent = `
        .qr-btn {
          cursor: pointer;
          border: 0;
          background: none;
          padding: 6px;
          color: var(--muted);
          border-radius: 8px;
          transition: color 0.15s ease, background 0.15s ease;
        }
        .qr-btn:hover {
          color: var(--accent);
          background: var(--surface-2);
        }
        .qr-btn svg {
          width: 18px;
          height: 18px;
          fill: none;
          stroke: currentColor;
          stroke-width: 1.8;
        }
        .qr-modal {
          position: fixed;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          background: var(--surface-solid);
          border: 1px solid var(--line);
          border-radius: var(--radius-xl);
          padding: 24px;
          max-width: 320px;
          width: 90%;
          box-shadow: var(--shadow-lg);
          z-index: 1000;
          display: none;
        }
        .qr-modal.show {
          display: block;
        }
        .qr-modal h3 {
          margin: 0 0 12px;
          font-size: 18px;
        }
        .qr-modal .qr-code {
          text-align: center;
          margin: 16px 0;
          padding: 16px;
          background: #fff;
          border-radius: var(--radius-md);
        }
        .qr-modal .qr-code canvas {
          max-width: 100%;
          height: auto;
        }
        .qr-modal .url-display {
          font: 11px var(--font-mono);
          color: var(--muted);
          word-break: break-all;
          background: var(--surface-2);
          padding: 8px 12px;
          border-radius: var(--radius-sm);
          margin-top: 12px;
        }
        .qr-modal .actions {
          display: flex;
          gap: 8px;
          margin-top: 16px;
          justify-content: flex-end;
        }
        .qr-backdrop {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          backdrop-filter: blur(4px);
          z-index: 999;
          opacity: 0;
          pointer-events: none;
          transition: opacity 0.2s ease;
        }
        .qr-backdrop.show {
          opacity: 1;
          pointer-events: all;
        }
      `;
      document.head.appendChild(style);
    },

    _loadScript() {
      // Load qrcode.js library
      if (document.getElementById('qrcode-js')) return;
      
      const script = document.createElement('script');
      script.id = 'qrcode-js';
      script.src = 'https://cdn.jsdelivr.net/npm/qrcode@1.5.1/build/qrcode.min.js';
      script.onload = () => {
        this._ready = true;
        this._attachHandlers();
      };
      document.head.appendChild(script);
    },

    _ready: false,
    _modal: null,
    _backdrop: null,

    showQR(text, title = 'QR Code') {
      if (!this._ready) {
        // Fallback: open in new tab with online generator
        window.open(`https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(text)}`, '_blank');
        return;
      }

      // Create modal if doesn't exist
      if (!this._modal) {
        this._createModal();
      }

      // Generate QR code
      const qrContainer = this._modal.querySelector('.qr-code');
      qrContainer.innerHTML = '';
      
      new QRCode(qrContainer, {
        text: text,
        width: 200,
        height: 200,
        colorDark: '#000000',
        colorLight: '#ffffff',
        correctLevel: QRCode.CorrectLevel.H
      });

      // Update URL display
      const urlDisplay = this._modal.querySelector('.url-display');
      urlDisplay.textContent = text;

      // Update title
      const titleEl = this._modal.querySelector('h3');
      titleEl.textContent = title;

      // Show modal
      this._backdrop.classList.add('show');
      this._modal.classList.add('show');
    },

    hideQR() {
      if (this._backdrop) this._backdrop.classList.remove('show');
      if (this._modal) this._modal.classList.remove('show');
    },

    _createModal() {
      this._backdrop = document.createElement('div');
      this._backdrop.className = 'qr-backdrop';
      this._backdrop.addEventListener('click', () => this.hideQR());
      document.body.appendChild(this._backdrop);

      this._modal = document.createElement('div');
      this._modal.className = 'qr-modal';
      this._modal.innerHTML = `
        <h3>QR Code</h3>
        <div class="qr-code"></div>
        <div class="url-display"></div>
        <div class="actions">
          <button class="button" onclick="OS.QRCode.download()">Download</button>
          <button class="button ghost" onclick="OS.QRCode.hideQR()">Close</button>
        </div>
      `;
      document.body.appendChild(this._modal);

      // Close on escape key
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') this.hideQR();
      });
    },

    download() {
      const canvas = this._modal.querySelector('.qr-code canvas');
      if (canvas) {
        const link = document.createElement('a');
        link.href = canvas.toDataURL('image/png');
        link.download = 'omnisource-qr.png';
        link.click();
      }
    },

    _attachHandlers() {
      // Add QR buttons to feed URLs
      document.querySelectorAll('code[class*="feed"], .source-box code, a[href*="apps.json"]').forEach(el => {
        const container = el.closest('.source-box, .source-card, .app-card, .rail-card, .featured-card') || el.parentElement;
        
        const btn = document.createElement('button');
        btn.className = 'qr-btn';
        btn.setAttribute('aria-label', 'Show QR code');
        btn.innerHTML = `
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 2.31 1.03 4.4 2.69 5.88L12 22l4.31-7.12C18.97 13.4 20 11.31 20 9c0-3.87-3.13-7-7-7zm0 14.5c-3.04 0-5.5-2.46-5.5-5.5s2.46-5.5 5.5-5.5 5.5 2.46 5.5 5.5-2.46 5.5-5.5 5.5z"/>
            <path d="M12 6.5c-1.93 0-3.5 1.57-3.5 3.5s1.57 3.5 3.5 3.5 3.5-1.57 3.5-3.5-1.57-3.5-3.5-3.5z"/>
          </svg>
        `;
        
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          const text = el.textContent.trim();
          const title = container.querySelector('h3, h2')?.textContent.trim() || 'Feed URL';
          this.showQR(text, title);
        });

        el.after(btn);
      });
    }
  };

  // ============================================================================
  // SEARCH OPERATORS (P1)
  // ============================================================================

  const Search = {
    init() {
      this._injectUI();
      this._setupListeners();
    },

    _injectUI() {
      const searchBox = document.querySelector('.hero-search .search-box, .search-box');
      if (!searchBox) return;

      const style = document.createElement('style');
      style.textContent = `
        .search-help {
          position: absolute;
          right: 12px;
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: 0;
          color: var(--muted);
          cursor: pointer;
          padding: 4px;
          border-radius: 6px;
          font: 700 10px var(--font-mono);
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }
        .search-help:hover {
          color: var(--text);
          background: var(--surface-2);
        }
        .search-operators-panel {
          position: absolute;
          top: 100%;
          right: 0;
          margin-top: 8px;
          background: var(--surface-solid);
          border: 1px solid var(--line);
          border-radius: var(--radius-md);
          padding: 12px;
          min-width: 240px;
          box-shadow: var(--shadow-md);
          z-index: 100;
          display: none;
        }
        .search-operators-panel.show {
          display: block;
        }
        .search-operators-panel h4 {
          margin: 0 0 8px;
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: var(--muted);
        }
        .search-operators-panel .operator-list {
          display: grid;
          gap: 6px;
        }
        .search-operators-panel .operator-item {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
          padding: 6px 8px;
          border-radius: var(--radius-sm);
          cursor: pointer;
          transition: background 0.15s ease;
        }
        .search-operators-panel .operator-item:hover {
          background: var(--surface-2);
        }
        .search-operators-panel .operator-item code {
          font: 600 10px var(--font-mono);
          background: var(--surface-2);
          padding: 2px 6px;
          border-radius: 4px;
        }
        .search-operators-panel .operator-item span {
          color: var(--muted);
        }
      `;
      document.head.appendChild(style);

      const helpBtn = document.createElement('button');
      helpBtn.className = 'search-help';
      helpBtn.textContent = '?';
      helpBtn.setAttribute('aria-label', 'Search operators help');

      const operatorsPanel = document.createElement('div');
      operatorsPanel.className = 'search-operators-panel';
      operatorsPanel.innerHTML = `
        <h4>Search Operators</h4>
        <div class="operator-list">
          <div class="operator-item" data-operator="status:">
            <code>status:</code>
            <span>Filter by status (stable, beta, manual, unmaintained)</span>
          </div>
          <div class="operator-item" data-operator="source:">
            <code>source:</code>
            <span>Filter by source</span>
          </div>
          <div class="operator-item" data-operator="category:">
            <code>category:</code>
            <span>Filter by category</span>
          </div>
          <div class="operator-item" data-operator="updated:>">
            <code>updated:&gt;</code>
            <span>Updated after date (e.g., updated:>7d)</span>
          </div>
          <div class="operator-item" data-operator="updated:<">
            <code>updated:&lt;</code>
            <span>Updated before date</span>
          </div>
          <div class="operator-item" data-operator="version:">
            <code>version:</code>
            <span>Filter by version</span>
          </div>
        </div>
      `;

      searchBox.appendChild(helpBtn);
      searchBox.appendChild(operatorsPanel);

      helpBtn.addEventListener('click', (e) => {
        e.preventDefault();
        operatorsPanel.classList.toggle('show');
      });

      // Close panel when clicking outside
      document.addEventListener('click', (e) => {
        if (!searchBox.contains(e.target)) {
          operatorsPanel.classList.remove('show');
        }
      });

      // Add click handlers for operator items
      operatorsPanel.querySelectorAll('.operator-item').forEach(item => {
        item.addEventListener('click', () => {
          const op = item.getAttribute('data-operator');
          const input = searchBox.querySelector('input');
          if (input) {
            input.value = input.value + op;
            input.focus();
            operatorsPanel.classList.remove('show');
          }
        });
      });
    },

    _setupListeners() {
      // Intercept search form submissions
      document.querySelectorAll('form[action*="search"], .search-box form').forEach(form => {
        form.addEventListener('submit', (e) => {
          const input = form.querySelector('input');
          if (input) {
            const query = input.value.trim();
            if (query) {
              this.executeSearch(query);
              e.preventDefault();
            }
          }
        });
      });

      // Handle real-time search
      document.querySelectorAll('.search-box input').forEach(input => {
        input.addEventListener('input', debounce((e) => {
          const query = e.target.value.trim();
          if (query.length >= 2) {
            this.executeSearch(query);
          } else if (query.length === 0) {
            this.clearResults();
          }
        }, 300));
      });
    },

    executeSearch(query) {
      // Parse query for operators
      const { operators, keywords } = this.parseQuery(query);
      
      // Get all apps
      const apps = window.OS_CATALOG || [];
      
      // Filter apps
      const results = apps.filter(app => {
        // Check keywords in name, description, developer, etc.
        const keywordMatch = keywords.length === 0 || 
          keywords.some(kw => 
            app.name.toLowerCase().includes(kw) ||
            (app.description || '').toLowerCase().includes(kw) ||
            (app.developer || '').toLowerCase().includes(kw) ||
            (app.bundleId || '').toLowerCase().includes(kw) ||
            (app.tags || []).some(t => t.toLowerCase().includes(kw))
          );
        
        if (!keywordMatch) return false;
        
        // Check operators
        for (const [key, value] of Object.entries(operators)) {
          switch (key) {
            case 'status':
              if (app.status?.toLowerCase() !== value.toLowerCase()) return false;
              break;
            case 'source':
              if ((app.source || '').toLowerCase().includes(value.toLowerCase()) === false) return false;
              break;
            case 'category':
              if ((app.category || '').toLowerCase() !== value.toLowerCase() &&
                  !(app.tags || []).some(t => t.toLowerCase() === value.toLowerCase())) return false;
              break;
            case 'updated>':
              if (!this.checkDate(app.updated, value, '>')) return false;
              break;
            case 'updated<':
              if (!this.checkDate(app.updated, value, '<')) return false;
              break;
            case 'version':
              if ((app.version || '').toLowerCase().includes(value.toLowerCase()) === false) return false;
              break;
          }
        }
        
        return true;
      });

      this.displayResults(results, query);
    },

    parseQuery(query) {
      const operators = {};
      const keywords = [];
      
      // Match operators like status:stable, updated:>7d, etc.
      const operatorRegex = /(\w+):([><]?[\w\d]+)/g;
      let match;
      
      while ((match = operatorRegex.exec(query)) !== null) {
        const [full, key, value] = match;
        operators[key] = value;
      }

      // Remove operators from query to get keywords
      const cleanQuery = query.replace(operatorRegex, '').trim();
      if (cleanQuery) {
        keywords.push(...cleanQuery.toLowerCase().split(/\s+/).filter(Boolean));
      }

      return { operators, keywords };
    },

    checkDate(dateStr, value, operator) {
      if (!dateStr) return false;
      
      const appDate = new Date(dateStr);
      const now = new Date();
      
      // Parse value like "7d", "2w", "3m", "1y"
      const num = parseInt(value);
      const unit = value.slice(-1);
      
      let days;
      switch (unit) {
        case 'd': days = num; break;
        case 'w': days = num * 7; break;
        case 'm': days = num * 30; break;
        case 'y': days = num * 365; break;
        default: days = num; // assume days
      }
      
      const thresholdDate = new Date(now.getTime() - (days * 24 * 60 * 60 * 1000));
      
      if (operator === '>') {
        return appDate > thresholdDate;
      } else {
        return appDate < thresholdDate;
      }
    },

    displayResults(results, query) {
      const resultsContainer = document.querySelector('.search-results, .apps-grid');
      if (!resultsContainer) return;

      if (results.length === 0) {
        resultsContainer.innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">🔍</div>
            <h3>No results found</h3>
            <p>Try a different search query.</p>
          </div>
        `;
        return;
      }

      resultsContainer.innerHTML = `
        <div class="results-meta">
          <span>${results.length} result${results.length !== 1 ? 's' : ''} for "${query}"</span>
          <button class="text-button" onclick="OS.Search.clearResults()">Clear</button>
        </div>
        <div class="apps-grid">
          ${results.map(app => this._renderAppCard(app)).join('')}
        </div>
      `;

      // Inject favorite buttons
      if (window.OS.Favorites) {
        window.OS.Favorites.injectButtons(resultsContainer);
      }
    },

    clearResults() {
      const resultsContainer = document.querySelector('.search-results, .apps-grid');
      if (resultsContainer) {
        resultsContainer.innerHTML = '';
      }
      
      const inputs = document.querySelectorAll('.search-box input');
      inputs.forEach(input => input.value = '');
    },

    _renderAppCard(app) {
      return `
        <article class="app-card" data-app-id="${app.slug || app.id}">
          <div class="card-top">
            <div class="icon-wrap">
              <img src="${OS.asset(app.icon || 'assets/unknown.png')}" alt="${app.name}" class="app-icon" width="58" height="58">
            </div>
            <div class="card-identity">
              <h3><a href="${OS.asset(`/apps/${app.slug}/`)}">${app.name}</a></h3>
              <p class="card-dev">${app.developer || 'Unknown'}</p>
            </div>
          </div>
          <p class="app-description">${app.description || 'No description available.'}</p>
          <div class="card-meta">
            <span class="meta-item"><b>${app.version || 'N/A'}</b> version</span>
            <span class="meta-item"><b>${app.status || 'unknown'}</b> status</span>
            <span class="meta-item"><b>${app.source || 'N/A'}</b> source</span>
          </div>
        </article>
      `;
    }
  };

  // ============================================================================
  // USER RATINGS (P2)
  // ============================================================================

  const Ratings = {
    STORAGE_KEY: 'ratings',

    init() {
      this._injectUI();
      this._loadFromStorage();
    },

    _injectUI() {
      const style = document.createElement('style');
      style.textContent = `
        .rating-stars {
          display: inline-flex;
          align-items: center;
          gap: 2px;
          font-size: 14px;
        }
        .rating-stars .star {
          cursor: pointer;
          color: var(--muted);
          transition: color 0.15s ease, transform 0.15s ease;
        }
        .rating-stars .star:hover {
          color: var(--amber);
          transform: scale(1.2);
        }
        .rating-stars .star.active {
          color: var(--amber);
        }
        .rating-stars .star svg {
          width: 16px;
          height: 16px;
          fill: currentColor;
        }
        .rating-display {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          color: var(--muted);
        }
        .rating-display .stars {
          color: var(--amber);
        }
        .rating-count {
          font-size: 11px;
          color: var(--faint);
        }
        .rate-btn {
          cursor: pointer;
          border: 0;
          background: none;
          padding: 4px 8px;
          color: var(--muted);
          font: 700 10px var(--font-mono);
          letter-spacing: 0.08em;
          text-transform: uppercase;
          border-radius: 6px;
          transition: all 0.15s ease;
        }
        .rate-btn:hover {
          color: var(--amber);
          background: var(--amber-soft);
        }
        .rating-modal {
          position: fixed;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          background: var(--surface-solid);
          border: 1px solid var(--line);
          border-radius: var(--radius-xl);
          padding: 24px;
          max-width: 360px;
          width: 90%;
          box-shadow: var(--shadow-lg);
          z-index: 1000;
          display: none;
        }
        .rating-modal.show {
          display: block;
        }
        .rating-modal h3 {
          margin: 0 0 8px;
          font-size: 18px;
        }
        .rating-modal p {
          color: var(--muted);
          font-size: 13px;
          margin: 0 0 16px;
        }
        .rating-modal .rating-stars {
          justify-content: center;
          font-size: 24px;
          margin: 16px 0;
        }
        .rating-modal .rating-stars .star {
          font-size: 28px;
        }
        .rating-modal .actions {
          display: flex;
          gap: 8px;
          justify-content: flex-end;
        }
        .rating-backdrop {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          backdrop-filter: blur(4px);
          z-index: 999;
          opacity: 0;
          pointer-events: none;
          transition: opacity 0.2s ease;
        }
        .rating-backdrop.show {
          opacity: 1;
          pointer-events: all;
        }
      `;
      document.head.appendChild(style);
    },

    _loadFromStorage() {
      if (!Storage.get(this.STORAGE_KEY)) {
        Storage.set(this.STORAGE_KEY, {});
      }
    },

    getRating(appId) {
      const ratings = Storage.get(this.STORAGE_KEY, {});
      return ratings[appId] || 0;
    },

    setRating(appId, rating) {
      const ratings = Storage.get(this.STORAGE_KEY, {});
      ratings[appId] = rating;
      Storage.set(this.STORAGE_KEY, ratings);
      OS.emit('ratings:updated', { appId, rating });
    },

    getAverageRating(appId) {
      // In a real implementation, this would come from a backend
      // For now, just return the user's rating
      return this.getRating(appId);
    },

    getRatingCount(appId) {
      // In a real implementation, this would come from a backend
      return this.getRating(appId) > 0 ? 1 : 0;
    },

    showRatingModal(appId, appName) {
      if (!this._modal) {
        this._createModal();
      }

      const title = this._modal.querySelector('h3');
      title.textContent = `Rate ${appName}`;

      const currentRating = this.getRating(appId);
      const stars = this._modal.querySelectorAll('.star');
      stars.forEach((star, index) => {
        star.classList.toggle('active', index < currentRating);
      });

      // Store current app ID
      this._currentAppId = appId;

      this._backdrop.classList.add('show');
      this._modal.classList.add('show');
    },

    hideRatingModal() {
      if (this._backdrop) this._backdrop.classList.remove('show');
      if (this._modal) this._modal.classList.remove('show');
    },

    _createModal() {
      this._backdrop = document.createElement('div');
      this._backdrop.className = 'rating-backdrop';
      this._backdrop.addEventListener('click', () => this.hideRatingModal());
      document.body.appendChild(this._backdrop);

      this._modal = document.createElement('div');
      this._modal.className = 'rating-modal';
      this._modal.innerHTML = `
        <h3>Rate App</h3>
        <p>Help others discover great apps by sharing your experience.</p>
        <div class="rating-stars">
          ${[1, 2, 3, 4, 5].map(i => `
            <span class="star" data-rating="${i}">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
              </svg>
            </span>
          `).join('')}
        </div>
        <div class="actions">
          <button class="button ghost" onclick="OS.Ratings.hideRatingModal()">Cancel</button>
          <button class="button primary" onclick="OS.Ratings.submitRating()">Submit</button>
        </div>
      `;
      document.body.appendChild(this._modal);

      // Setup star hover effects
      const stars = this._modal.querySelectorAll('.star');
      stars.forEach((star, index) => {
        star.addEventListener('click', () => {
          stars.forEach((s, i) => {
            s.classList.toggle('active', i <= index);
          });
        });
        
        star.addEventListener('mouseenter', () => {
          stars.forEach((s, i) => {
            s.classList.toggle('active', i <= index);
          });
        });
      });

      // Close on escape
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') this.hideRatingModal();
      });
    },

    submitRating() {
      if (!this._currentAppId) return;
      
      const activeStars = this._modal.querySelectorAll('.star.active');
      const rating = activeStars.length;
      
      this.setRating(this._currentAppId, rating);
      this.hideRatingModal();
      
      OS.toast(`Rated with ${rating} star${rating !== 1 ? 's' : ''}!`);
      
      // Update UI
      this.injectRatingDisplays();
    },

    injectRatingDisplays(container = document) {
      const appCards = container.querySelectorAll('.app-card, .rail-card, .featured-card, .result-row');
      appCards.forEach(card => {
        const appId = this._getAppId(card);
        if (!appId) return;

        // Remove existing rating display
        const existing = card.querySelector('.rating-display');
        if (existing) existing.remove();

        const rating = this.getAverageRating(appId);
        const count = this.getRatingCount(appId);

        if (rating === 0 && count === 0) return;

        const display = document.createElement('div');
        display.className = 'rating-display';
        display.innerHTML = `
          <span class="stars">${'★'.repeat(Math.floor(rating))}${'☆'.repeat(5 - Math.floor(rating))}</span>
          <span class="rating-count">(${count})</span>
        `;

        // Try to insert in a good location
        const meta = card.querySelector('.card-meta, .meta');
        if (meta) {
          meta.appendChild(display);
        } else {
          card.appendChild(display);
        }
      });

      // Add rate buttons
      this._injectRateButtons(container);
    },

    _injectRateButtons(container = document) {
      const appCards = container.querySelectorAll('.app-card, .rail-card, .featured-card, .result-row');
      appCards.forEach(card => {
        if (card.querySelector('.rate-btn')) return;

        const appId = this._getAppId(card);
        if (!appId) return;

        const appName = card.querySelector('h3, h2')?.textContent.trim() || 'this app';

        const btn = document.createElement('button');
        btn.className = 'rate-btn';
        btn.textContent = 'Rate';
        btn.setAttribute('data-app-id', appId);
        btn.setAttribute('data-app-name', appName);
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          this.showRatingModal(appId, appName);
        });

        const actions = card.querySelector('.card-actions, .actions');
        if (actions) {
          actions.appendChild(btn);
        }
      });
    },

    _getAppId(card) {
      // Same logic as Favorites
      const href = card.getAttribute('href');
      if (href && href.includes('/apps/')) {
        const match = href.match(/\/apps\/([^\/]+)/);
        if (match) return match[1];
      }

      const dataId = card.getAttribute('data-app-id') ||
                    card.getAttribute('data-id') ||
                    card.getAttribute('id');
      if (dataId) return dataId;

      const title = card.querySelector('h3, h2, .card-identity h3');
      if (title) {
        const text = title.textContent.trim().toLowerCase().replace(/\s+/g, '-');
        return text;
      }

      return null;
    }
  };

  // ============================================================================
  // HISTORICAL UPTIME CHARTS (P2)
  // ============================================================================

  const Charts = {
    init() {
      this._loadScript();
      this._injectUI();
    },

    _loadScript() {
      if (document.getElementById('chartjs')) return;
      
      const script = document.createElement('script');
      script.id = 'chartjs';
      script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
      script.onload = () => {
        this._ready = true;
        this.renderCharts();
      };
      document.head.appendChild(script);
    },

    _ready: false,

    _injectUI() {
      // Add charts to status page
      const statusPage = document.querySelector('.st-overview, .status-tile');
      if (!statusPage) return;

      const style = document.createElement('style');
      style.textContent = `
        .chart-container {
          position: relative;
          height: 200px;
          width: 100%;
          margin: 20px 0;
        }
        .chart-container canvas {
          max-height: 100%;
        }
        .status-chart-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 20px;
          margin-top: 30px;
        }
      `;
      document.head.appendChild(style);
    },

    renderCharts() {
      if (!this._ready) {
        setTimeout(() => this.renderCharts(), 100);
        return;
      }

      // Check if we're on the status page
      const statusPage = document.querySelector('.st-panel');
      if (!statusPage) return;

      // Check if charts already rendered
      if (document.querySelector('.status-chart-grid')) return;

      // Create charts container
      const chartsContainer = document.createElement('div');
      chartsContainer.className = 'status-chart-grid';

      // Get status data
      const statusData = window.OS_STATUS_DATA || this._fetchStatusData();
      if (!statusData) return;

      // Render uptime chart
      chartsContainer.appendChild(this._renderUptimeChart(statusData));
      
      // Render latency chart
      chartsContainer.appendChild(this._renderLatencyChart(statusData));

      // Insert after the overview
      const overview = document.querySelector('.st-overview');
      if (overview) {
        overview.after(chartsContainer);
      } else {
        statusPage.prepend(chartsContainer);
      }
    },

    _fetchStatusData() {
      try {
        // Try to get from the page data
        const script = document.querySelector('script#status-data');
        if (script) {
          return JSON.parse(script.textContent);
        }
      } catch {}
      return null;
    },

    _renderUptimeChart(data) {
      const container = document.createElement('div');
      container.className = 'chart-container';
      
      const canvas = document.createElement('canvas');
      container.appendChild(canvas);

      const sources = Object.keys(data.sources || {});
      const labels = sources;
      const uptimeData = sources.map(source => {
        const stats = data.sources[source];
        return ((stats.uptime || 0) / stats.totalChecks || 0) * 100;
      });

      new Chart(canvas, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Uptime (%)',
            data: uptimeData,
            backgroundColor: 'rgba(109, 94, 245, 0.8)',
            borderColor: 'rgba(109, 94, 245, 1)',
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              callbacks: {
                label: (context) => {
                  return `${context.parsed.y.toFixed(1)}% uptime`;
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              ticks: {
                callback: (value) => value + '%'
              }
            }
          }
        }
      });

      return container;
    },

    _renderLatencyChart(data) {
      const container = document.createElement('div');
      container.className = 'chart-container';
      
      const canvas = document.createElement('canvas');
      container.appendChild(canvas);

      const sources = Object.keys(data.sources || {});
      const labels = sources;
      const latencyData = sources.map(source => {
        const stats = data.sources[source];
        return stats.avgLatency || 0;
      });

      new Chart(canvas, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Avg Latency (ms)',
            data: latencyData,
            backgroundColor: 'rgba(10, 132, 255, 0.8)',
            borderColor: 'rgba(10, 132, 255, 1)',
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              callbacks: {
                label: (context) => {
                  return `${context.parsed.y.toFixed(0)} ms`;
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                callback: (value) => value + ' ms'
              }
            }
          }
        }
      });

      return container;
    }
  };

  // ============================================================================
  // PUSH NOTIFICATIONS (P2)
  // ============================================================================

  const Notifications = {
    _swRegistration: null,
    _subscription: null,

    init() {
      this._checkSupport();
      this._injectUI();
    },

    _checkSupport() {
      if ('serviceWorker' in navigator && 'PushManager' in window) {
        this._registerSW();
      }
    },

    async _registerSW() {
      try {
        this._swRegistration = await navigator.serviceWorker.register(
          OS.asset('sw.js'),
          { scope: '/' }
        );
        
        this._swRegistration.onupdatefound = () => {
          console.log('Service Worker update found');
        };

        // Check for existing subscription
        this._subscription = await this._swRegistration.pushManager.getSubscription();
        
        // Update UI based on subscription status
        this._updateUI();
      } catch (e) {
        console.warn('Service Worker registration failed:', e);
      }
    },

    _injectUI() {
      const style = document.createElement('style');
      style.textContent = `
        .notifications-btn {
          cursor: pointer;
          border: 0;
          background: none;
          padding: 6px;
          color: var(--muted);
          border-radius: 8px;
          transition: color 0.15s ease, background 0.15s ease;
        }
        .notifications-btn:hover {
          color: var(--accent);
          background: var(--surface-2);
        }
        .notifications-btn.enabled {
          color: var(--green);
        }
        .notifications-btn svg {
          width: 18px;
          height: 18px;
          fill: none;
          stroke: currentColor;
          stroke-width: 1.8;
        }
        .notifications-modal {
          position: fixed;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          background: var(--surface-solid);
          border: 1px solid var(--line);
          border-radius: var(--radius-xl);
          padding: 24px;
          max-width: 400px;
          width: 90%;
          box-shadow: var(--shadow-lg);
          z-index: 1000;
          display: none;
        }
        .notifications-modal.show {
          display: block;
        }
        .notifications-modal h3 {
          margin: 0 0 8px;
          font-size: 18px;
        }
        .notifications-modal p {
          color: var(--muted);
          font-size: 13px;
          margin: 0 0 16px;
        }
        .notifications-modal .toggle {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          background: var(--surface-2);
          border-radius: var(--radius-md);
          margin: 16px 0;
        }
        .notifications-modal .toggle input {
          width: 44px;
          height: 24px;
          appearance: none;
          background: var(--line-strong);
          border-radius: 999px;
          position: relative;
          cursor: pointer;
          transition: background 0.2s ease;
        }
        .notifications-modal .toggle input:checked {
          background: var(--green);
        }
        .notifications-modal .toggle input::before {
          content: '';
          position: absolute;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: white;
          top: 2px;
          left: 2px;
          transition: transform 0.2s ease;
        }
        .notifications-modal .toggle input:checked::before {
          transform: translateX(20px);
        }
        .notifications-modal .toggle label {
          cursor: pointer;
          font-weight: 600;
        }
        .notifications-modal .actions {
          display: flex;
          gap: 8px;
          justify-content: flex-end;
        }
        .notifications-backdrop {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          backdrop-filter: blur(4px);
          z-index: 999;
          opacity: 0;
          pointer-events: none;
          transition: opacity 0.2s ease;
        }
        .notifications-backdrop.show {
          opacity: 1;
          pointer-events: all;
        }
      `;
      document.head.appendChild(style);

      // Add notifications button to nav
      const navControls = document.querySelector('.nav-controls');
      if (navControls) {
        const btn = document.createElement('button');
        btn.className = 'notifications-btn icon-button';
        btn.setAttribute('aria-label', 'Manage notifications');
        btn.innerHTML = `
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2zm-6 4h8v-2H6v2z"/>
          </svg>
        `;
        btn.addEventListener('click', () => this.showSettings());
        navControls.prepend(btn);
      }
    },

    _updateUI() {
      const btn = document.querySelector('.notifications-btn');
      if (btn) {
        btn.classList.toggle('enabled', !!this._subscription);
      }
    },

    showSettings() {
      if (!this._modal) {
        this._createModal();
      }

      const toggle = this._modal.querySelector('input[type="checkbox"]');
      if (toggle) {
        toggle.checked = !!this._subscription;
      }

      this._backdrop.classList.add('show');
      this._modal.classList.add('show');
    },

    hideSettings() {
      if (this._backdrop) this._backdrop.classList.remove('show');
      if (this._modal) this._modal.classList.remove('show');
    },

    _createModal() {
      this._backdrop = document.createElement('div');
      this._backdrop.className = 'notifications-backdrop';
      this._backdrop.addEventListener('click', () => this.hideSettings());
      document.body.appendChild(this._backdrop);

      this._modal = document.createElement('div');
      this._modal.className = 'notifications-modal';
      this._modal.innerHTML = `
        <h3>Notifications</h3>
        <p>Get notified when your favorite apps are updated.</p>
        <div class="toggle">
          <input type="checkbox" id="notifications-toggle" ${this._subscription ? 'checked' : ''}>
          <label for="notifications-toggle">Enable push notifications</label>
        </div>
        <p style="font-size: 11px; color: var(--faint); margin: 0;">
          You'll receive notifications for app updates even when the site is closed.
        </p>
        <div class="actions" style="margin-top: 20px;">
          <button class="button ghost" onclick="OS.Notifications.hideSettings()">Close</button>
          <button class="button primary" onclick="OS.Notifications.toggleNotifications()">Save</button>
        </div>
      `;
      document.body.appendChild(this._modal);

      // Close on escape
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') this.hideSettings();
      });
    },

    async toggleNotifications() {
      if (this._subscription) {
        await this._subscription.unsubscribe();
        this._subscription = null;
        this._updateUI();
        OS.toast('Notifications disabled');
      } else {
        await this._subscribe();
      }
      this.hideSettings();
    },

    async _subscribe() {
      try {
        if (!this._swRegistration) {
          await this._registerSW();
        }

        // Request permission
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
          OS.toast('Notification permission denied');
          return;
        }

        // Subscribe to push
        const subscription = await this._swRegistration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: this._getPublicKey()
        });

        this._subscription = subscription;
        this._updateUI();
        
        // Send subscription to server (would need backend)
        await this._saveSubscription(subscription);
        
        OS.toast('Notifications enabled!');
      } catch (e) {
        console.error('Failed to subscribe:', e);
        OS.toast('Failed to enable notifications');
      }
    },

    _getPublicKey() {
      // This would be your VAPID public key
      // For now, return a placeholder
      return urlBase64ToUint8Array('BLmjMvQ4p8Q1Xv76JXvQ4p8Q1Xv76JXvQ4p8Q1Xv76JX');
    },

    async _saveSubscription(subscription) {
      // In a real implementation, this would send to your backend
      // For now, just store in localStorage
      Storage.set('push-subscription', subscription);
    }
  };

  // ============================================================================
  // WEBHOOKS (P0) - Requires backend, but client-side UI
  // ============================================================================

  const Webhooks = {
    STORAGE_KEY: 'webhooks',

    init() {
      this._injectUI();
      this._loadFromStorage();
    },

    _injectUI() {
      // Add webhooks link to user menu or settings
      const navControls = document.querySelector('.nav-controls');
      if (!navControls) return;

      const style = document.createElement('style');
      style.textContent = `
        .webhooks-btn {
          cursor: pointer;
          border: 0;
          background: none;
          padding: 6px;
          color: var(--muted);
          border-radius: 8px;
          transition: color 0.15s ease, background 0.15s ease;
        }
        .webhooks-btn:hover {
          color: var(--accent);
          background: var(--surface-2);
        }
        .webhooks-btn svg {
          width: 18px;
          height: 18px;
          fill: none;
          stroke: currentColor;
          stroke-width: 1.8;
        }
        .webhooks-modal {
          position: fixed;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          background: var(--surface-solid);
          border: 1px solid var(--line);
          border-radius: var(--radius-xl);
          padding: 24px;
          max-width: 500px;
          width: 90%;
          max-height: 80vh;
          overflow-y: auto;
          box-shadow: var(--shadow-lg);
          z-index: 1000;
          display: none;
        }
        .webhooks-modal.show {
          display: block;
        }
        .webhooks-modal h3 {
          margin: 0 0 8px;
          font-size: 18px;
        }
        .webhooks-modal p {
          color: var(--muted);
          font-size: 13px;
          margin: 0 0 16px;
        }
        .webhook-form {
          display: grid;
          gap: 12px;
          margin-top: 16px;
        }
        .webhook-form .field {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .webhook-form label {
          font: 700 11px var(--font-mono);
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: var(--muted);
        }
        .webhook-form input,
        .webhook-form select {
          height: 40px;
          border: 1px solid var(--line);
          background: var(--surface-solid);
          color: var(--text);
          border-radius: var(--radius-md);
          padding: 0 12px;
          font-size: 13px;
        }
        .webhook-list {
          display: grid;
          gap: 12px;
          margin-top: 20px;
        }
        .webhook-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          background: var(--surface-2);
          border-radius: var(--radius-md);
          border: 1px solid var(--line);
        }
        .webhook-item .info {
          flex: 1;
        }
        .webhook-item .info h4 {
          margin: 0 0 4px;
          font-size: 13px;
        }
        .webhook-item .info p {
          margin: 0;
          font-size: 11px;
          color: var(--muted);
        }
        .webhook-item .actions {
          display: flex;
          gap: 6px;
        }
        .webhook-item .actions button {
          height: 28px;
          padding: 0 12px;
          font-size: 11px;
        }
        .webhooks-backdrop {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          backdrop-filter: blur(4px);
          z-index: 999;
          opacity: 0;
          pointer-events: none;
          transition: opacity 0.2s ease;
        }
        .webhooks-backdrop.show {
          opacity: 1;
          pointer-events: all;
        }
      `;
      document.head.appendChild(style);

      const btn = document.createElement('button');
      btn.className = 'webhooks-btn icon-button';
      btn.setAttribute('aria-label', 'Manage webhooks');
      btn.innerHTML = `
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2L13.09 8.26L22 9L13.09 9.74L12 16L10.91 9.74L2 9L10.91 8.26L12 2Z"/>
          <path d="M2 15L10.91 15.74L12 22L13.09 15.74L22 15L13.09 14.26L12 8L10.91 14.26L2 15Z"/>
        </svg>
      `;
      btn.addEventListener('click', () => this.showModal());
      navControls.prepend(btn);
    },

    _loadFromStorage() {
      if (!Storage.get(this.STORAGE_KEY)) {
        Storage.set(this.STORAGE_KEY, []);
      }
    },

    getAll() {
      return Storage.get(this.STORAGE_KEY, []);
    },

    add(webhook) {
      const webhooks = this.getAll();
      webhook.id = generateId();
      webhooks.push(webhook);
      Storage.set(this.STORAGE_KEY, webhooks);
      this._renderList();
      return webhook;
    },

    remove(id) {
      const webhooks = this.getAll();
      const index = webhooks.findIndex(w => w.id === id);
      if (index > -1) {
        webhooks.splice(index, 1);
        Storage.set(this.STORAGE_KEY, webhooks);
        this._renderList();
        return true;
      }
      return false;
    },

    showModal() {
      if (!this._modal) {
        this._createModal();
      }
      this._renderList();
      this._backdrop.classList.add('show');
      this._modal.classList.add('show');
    },

    hideModal() {
      if (this._backdrop) this._backdrop.classList.remove('show');
      if (this._modal) this._modal.classList.remove('show');
    },

    _createModal() {
      this._backdrop = document.createElement('div');
      this._backdrop.className = 'webhooks-backdrop';
      this._backdrop.addEventListener('click', () => this.hideModal());
      document.body.appendChild(this._backdrop);

      this._modal = document.createElement('div');
      this._modal.className = 'webhooks-modal';
      this._modal.innerHTML = `
        <h3>Webhooks</h3>
        <p>Get notified via webhook when apps are updated. Perfect for Discord, Slack, or custom integrations.</p>
        
        <form class="webhook-form" id="webhook-form">
          <div class="field">
            <label>Webhook URL *</label>
            <input type="url" name="url" placeholder="https://your-webhook.url" required>
          </div>
          <div class="field">
            <label>Events</label>
            <select name="events" multiple style="height: auto; min-height: 40px;">
              <option value="app:update">App Updated</option>
              <option value="app:new">New App Added</option>
              <option value="source:down">Source Down</option>
              <option value="source:up">Source Back Up</option>
            </select>
          </div>
          <div class="field">
            <label>App Filter (optional)</label>
            <input type="text" name="appFilter" placeholder="com.example.app or leave blank for all">
          </div>
          <button type="submit" class="button primary" style="margin-top: 8px;">Add Webhook</button>
        </form>
        
        <div class="webhook-list" id="webhook-list"></div>
        
        <div class="actions" style="margin-top: 20px; display: flex; justify-content: flex-end;">
          <button class="button ghost" onclick="OS.Webhooks.hideModal()">Close</button>
        </div>
      `;
      document.body.appendChild(this._modal);

      // Setup form
      const form = this._modal.querySelector('#webhook-form');
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const url = form.querySelector('[name="url"]').value;
        const events = Array.from(form.querySelector('[name="events"]').selectedOptions)
          .map(o => o.value);
        const appFilter = form.querySelector('[name="appFilter"]').value;
        
        if (!url) {
          OS.toast('Please enter a webhook URL');
          return;
        }
        
        this.add({ url, events, appFilter });
        form.reset();
        OS.toast('Webhook added! (Note: Requires backend to work)');
      });

      // Close on escape
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') this.hideModal();
      });
    },

    _renderList() {
      const list = this._modal.querySelector('#webhook-list');
      const webhooks = this.getAll();
      
      if (webhooks.length === 0) {
        list.innerHTML = '<p style="color: var(--faint); text-align: center;">No webhooks configured.</p>';
        return;
      }

      list.innerHTML = webhooks.map(webhook => `
        <div class="webhook-item" data-id="${webhook.id}">
          <div class="info">
            <h4>${webhook.url}</h4>
            <p>${webhook.events.join(', ')} ${webhook.appFilter ? `for ${webhook.appFilter}` : ''}</p>
          </div>
          <div class="actions">
            <button class="button danger" onclick="OS.Webhooks.remove('${webhook.id}')">Remove</button>
          </div>
        </div>
      `).join('');
    }
  };

  // ============================================================================
  // MOBILE APP (P3) - Architecture Design
  // ============================================================================

  const MobileApp = {
    // This is a design document for the mobile app
    // The actual implementation would be in a separate repo
    
    architecture: {
      platform: 'React Native (Expo)',
      stateManagement: 'Zustand',
      navigation: 'React Navigation',
      styling: 'Tailwind CSS or custom theme matching web',
      storage: 'AsyncStorage + SQLite',
      networking: 'React Query',
      deepLinks: 'React Navigation deep links',
      notifications: 'Expo Notifications',
      biometrics: 'Expo Local Authentication'
    },

    features: [
      'Browse OmniSource catalog',
      'View app details',
      'Add/remove favorites',
      'Get update notifications',
      'Scan QR codes for feeds',
      'Compare apps',
      'View source health',
      'Offline catalog (cached)',
      'Dark mode',
      'Biometric authentication for sensitive actions'
    ],

    apiEndpoints: [
      'GET /api/catalog.json - Get app catalog',
      'GET /api/apps/{id}.json - Get app details',
      'GET /api/status.json - Get source health',
      'GET /api/updates.json - Get recent updates',
      'POST /api/webhooks - Register webhook (backend required)',
      'POST /api/notifications/subscribe - Subscribe to push (backend required)'
    ]
  };

  // ============================================================================
  // MULTI-LANGUAGE SUPPORT (P3)
  // ============================================================================

  const I18n = {
    STORAGE_KEY: 'language',
    
    languages: {
      en: { name: 'English', native: 'English' },
      es: { name: 'Spanish', native: 'Español' },
      zh: { name: 'Chinese', native: '中文' },
      ar: { name: 'Arabic', native: 'العربية' },
      fr: { name: 'French', native: 'Français' },
      de: { name: 'German', native: 'Deutsch' }
    },

    translations: {
      en: {
        // English translations (default)
        home: 'Home',
        compare: 'Compare',
        status: 'Status',
        analytics: 'Analytics',
        install: 'Install',
        favorites: 'Favorites',
        collections: 'Collections',
        search: 'Search',
        'no-results': 'No results found',
        'loading': 'Loading...',
        'app-updated': 'App updated',
        'new-app': 'New app added',
        'source-down': 'Source is down',
        'rate-app': 'Rate this app',
        'add-to-favorites': 'Add to favorites',
        'remove-from-favorites': 'Remove from favorites',
        'enable-notifications': 'Enable notifications',
        'disable-notifications': 'Disable notifications'
      },
      es: {
        home: 'Inicio',
        compare: 'Comparar',
        status: 'Estado',
        analytics: 'Analíticas',
        install: 'Instalar',
        favorites: 'Favoritos',
        collections: 'Colecciones',
        search: 'Buscar',
        'no-results': 'No se encontraron resultados',
        'loading': 'Cargando...',
        'app-updated': 'Aplicación actualizada',
        'new-app': 'Nueva aplicación añadida',
        'source-down': 'Fuente no disponible',
        'rate-app': 'Calificar esta aplicación',
        'add-to-favorites': 'Añadir a favoritos',
        'remove-from-favorites': 'Eliminar de favoritos',
        'enable-notifications': 'Activar notificaciones',
        'disable-notifications': 'Desactivar notificaciones'
      }
    },

    init() {
      this._loadLanguage();
      this._injectUI();
      this._applyTranslations();
    },

    _loadLanguage() {
      const saved = Storage.get(this.STORAGE_KEY);
      if (saved && this.translations[saved]) {
        this.currentLanguage = saved;
      } else {
        // Try to detect browser language
        const browserLang = navigator.language.split('-')[0];
        this.currentLanguage = this.translations[browserLang] ? browserLang : 'en';
      }
    },

    _injectUI() {
      const style = document.createElement('style');
      style.textContent = `
        .language-selector {
          position: relative;
        }
        .language-selector select {
          height: 36px;
          border: 1px solid var(--line);
          background: var(--surface-solid);
          color: var(--text);
          border-radius: var(--radius-md);
          padding: 0 10px;
          font-size: 12px;
          cursor: pointer;
          appearance: none;
          -webkit-appearance: none;
        }
        .language-selector::after {
          content: '▼';
          position: absolute;
          right: 10px;
          top: 50%;
          transform: translateY(-50%);
          pointer-events: none;
          color: var(--muted);
          font-size: 10px;
        }
      `;
      document.head.appendChild(style);

      // Add language selector to nav
      const navControls = document.querySelector('.nav-controls');
      if (!navControls) return;

      const selector = document.createElement('div');
      selector.className = 'language-selector';
      selector.innerHTML = `
        <select id="language-select">
          ${Object.entries(this.languages).map(([code, lang]) => `
            <option value="${code}" ${code === this.currentLanguage ? 'selected' : ''}>
              ${lang.native}
            </option>
          `).join('')}
        </select>
      `;

      navControls.appendChild(selector);

      selector.querySelector('select').addEventListener('change', (e) => {
        this.setLanguage(e.target.value);
      });
    },

    setLanguage(code) {
      if (!this.translations[code]) return;
      
      this.currentLanguage = code;
      Storage.set(this.STORAGE_KEY, code);
      this._applyTranslations();
      OS.emit('language:changed', code);
    },

    getLanguage() {
      return this.currentLanguage;
    },

    t(key, params = {}) {
      const lang = this.translations[this.currentLanguage] || this.translations.en;
      let translation = lang[key] || key;
      
      // Replace placeholders
      for (const [placeholder, value] of Object.entries(params)) {
        translation = translation.replace(new RegExp(`\${placeholder}`, 'g'), value);
      }
      
      return translation;
    },

    _applyTranslations() {
      // Translate all elements with data-i18n attributes
      document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const params = el.getAttribute('data-i18n-params');
        el.textContent = this.t(key, params ? JSON.parse(params) : {});
      });

      // Update document title
      document.title = this.t('site-title', { site: 'OmniSource' });
    }
  };

  // ============================================================================
  // TOAST NOTIFICATIONS (Utility)
  // ============================================================================

  const Toast = {
    init() {
      this._injectContainer();
    },

    _injectContainer() {
      if (document.getElementById('toast-container')) return;

      const container = document.createElement('div');
      container.id = 'toast-container';
      container.style.cssText = `
        position: fixed;
        bottom: 24px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 2000;
        display: flex;
        flex-direction: column;
        gap: 8px;
        pointer-events: none;
      `;
      document.body.appendChild(container);
    },

    show(message, options = {}) {
      const { duration = 3000, type = 'default' } = options;

      const toast = document.createElement('div');
      toast.className = `toast ${type}`;
      toast.textContent = message;
      toast.style.cssText = `
        background: var(--surface-solid);
        color: var(--text);
        border: 1px solid var(--line);
        border-radius: var(--radius-pill);
        padding: 12px 20px;
        font-size: 13px;
        font-weight: 600;
        box-shadow: var(--shadow-lg);
        pointer-events: auto;
        animation: slideIn 0.3s ease-out;
        ${type === 'success' ? 'border-color: var(--green);' : ''}
        ${type === 'error' ? 'border-color: var(--red);' : ''}
        ${type === 'warning' ? 'border-color: var(--amber);' : ''}
      `;

      const container = document.getElementById('toast-container');
      container.appendChild(toast);

      // Auto-remove
      setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
      }, duration);

      return toast;
    }
  };

  // Add toast animation styles
  const toastStyles = document.createElement('style');
  toastStyles.textContent = `
    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translate(-50%, 20px);
      }
      to {
        opacity: 1;
        transform: translate(-50%, 0);
      }
    }
    @keyframes slideOut {
      from {
        opacity: 1;
        transform: translate(-50%, 0);
      }
      to {
        opacity: 0;
        transform: translate(-50%, -20px);
      }
    }
  `;
  document.head.appendChild(toastStyles);

  // ============================================================================
  // URL BASE64 UTILITY (for VAPID keys)
  // ============================================================================

  function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  // ============================================================================
  // INITIALIZE ALL FEATURES
  // ============================================================================

  const init = () => {
    // Initialize utilities
    Toast.init();
    OS.toast = Toast.show;

    // Initialize features
    Favorites.init();
    Collections.init();
    Compare.init();
    QRCode.init();
    Search.init();
    Ratings.init();
    Charts.init();
    Notifications.init();
    Webhooks.init();
    I18n.init();

    // Make features accessible
    OS.Favorites = Favorites;
    OS.Collections = Collections;
    OS.Compare = Compare;
    OS.QRCode = QRCode;
    OS.Search = Search;
    OS.Ratings = Ratings;
    OS.Charts = Charts;
    OS.Notifications = Notifications;
    OS.Webhooks = Webhooks;
    OS.I18n = I18n;

    // Auto-initialize features on page load
    document.addEventListener('DOMContentLoaded', () => {
      // Inject favorite buttons on app cards
      Favorites.injectButtons();
      Favorites.updateCount();

      // Inject rating displays
      Ratings.injectRatingDisplays();

      // Attach QR code handlers
      QRCode._attachHandlers();

      // Initialize charts if on status page
      if (document.querySelector('.st-panel')) {
        Charts.renderCharts();
      }
    });

    console.log('OmniSource Features initialized');
  };

  // Run on DOM ready or immediately if already loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Export for module usage
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Favorites, Collections, Compare, QRCode, Search, Ratings, Charts, Notifications, Webhooks, I18n };
  }
})();
