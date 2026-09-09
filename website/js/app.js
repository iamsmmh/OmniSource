'use strict';

const SOURCE_URL = 'https://iamsmmh.github.io/OmniSource/apps.json';
const BASE_URL = 'https://iamsmmh.github.io/OmniSource';
const RSS_URL = `${BASE_URL}/feed.xml`;

const state = {
  apps: [],
  health: null,
  updates: null,
  source: null,
  clients: [],
  analytics: null,
  verification: new Map(), // slug -> { status, hash_verified, checks }
  discovery: new Map(),    // slug -> discovery entry (tags, downloads, page URL)
  collisions: new Map(), // bundleIdentifier -> [slug, ...] when length > 1
  query: '',
  category: 'all',
  status: 'all',
  os: 'any',
  sort: 'featured',
  view: localStorage.getItem('omnisource-view') === 'compact' ? 'compact' : 'grid',
  favorites: new Set(JSON.parse(localStorage.getItem('omnisource-favorites') || '[]')),
  activeApp: null,
  activeTab: 'about'
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const escapeHTML = value => String(value ?? '').replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
const cleanUrl = value => {
  try {
    const url = new URL(value, location.href);
    return ['http:', 'https:'].includes(url.protocol) ? url.href : '#';
  } catch { return '#'; }
};
const slugFor = app => app.omnisource?.slug || app.bundleIdentifier?.split('.').pop()?.toLowerCase() || 'app';
const feedFor = app => `${BASE_URL}/${encodeURIComponent(slugFor(app))}.json`;
const rssFor = app => `${BASE_URL}/${encodeURIComponent(slugFor(app))}.xml`;
const healthFor = app => state.health?.apps?.find(item => item.slug === slugFor(app)) || {};

const CATEGORY_LABELS = {
  'photo-video': 'Photo & Video', music: 'Music', social: 'Social', news: 'News',
  utilities: 'Utilities', networking: 'Networking', games: 'Games',
  'developer-tools': 'Developer Tools', entertainment: 'Entertainment', other: 'Other'
};
const CATEGORY_ICONS = {
  music: '🎵', 'photo-video': '🎬', social: '💬', news: '📰', utilities: '🛠',
  networking: '📡', games: '🎮', 'developer-tools': '⌨️', entertainment: '✨', other: '📦'
};
const STATUS_LABELS = { stable: 'Stable', beta: 'Beta', manual: 'Manual', unmaintained: 'Unmaintained', deprecated: 'Deprecated' };
const KIND_LABELS = { new: 'New app', updated: 'Updated', available: 'Live', unmaintained: 'Flagged' };
const VERIFICATION_LABELS = {
  'VERIFIED': '✓ Verified',
  'COMMUNITY VERIFIED': 'Community verified',
  'UNVERIFIED': 'Unverified'
};
const categoryLabel = category => CATEGORY_LABELS[category] || 'Other';
const statusLabel = status => STATUS_LABELS[status] || (status ? status[0].toUpperCase() + status.slice(1) : 'Unknown');
const verificationFor = app => state.verification.get(slugFor(app)) || null;
const discoveryFor = app => state.discovery.get(slugFor(app)) || null;
const downloadCountFor = app => Number(discoveryFor(app)?.downloads || app.versions?.[0]?.downloads || 0);

const formatBytes = bytes => {
  if (!Number(bytes)) return 'Unknown';
  const units = ['B', 'KB', 'MB', 'GB'];
  const unit = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** unit).toFixed(unit > 1 ? 1 : 0)} ${units[unit]}`;
};
const parseDate = value => {
  if (!value) return null;
  const date = new Date(value.length === 10 ? `${value}T12:00:00Z` : value);
  return Number.isNaN(date.valueOf()) ? null : date;
};
const formatDate = value => {
  const date = parseDate(value);
  return date ? new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric' }).format(date) : (value || 'Unknown');
};
const timeAgo = value => {
  const date = parseDate(value);
  if (!date) return 'Unknown';
  const days = Math.max(0, Math.round((Date.now() - date.getTime()) / 86400000));
  if (days === 0) return 'today';
  if (days === 1) return 'yesterday';
  if (days < 30) return `${days}d ago`;
  if (days < 365) return `${Math.round(days / 30)}mo ago`;
  return `${Math.round(days / 365)}y ago`;
};
const minOSMajor = app => {
  const value = app.omnisource?.compatibility?.minOSVersion;
  if (!value) return null;
  const match = String(value).match(/^(\d+)/);
  return match ? Number(match[1]) : null;
};

function toast(message) {
  const node = $('#toast');
  $('span', node).textContent = message;
  node.classList.add('show');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => node.classList.remove('show'), 2600);
}

async function copyText(text, success = 'Copied to clipboard') {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const input = Object.assign(document.createElement('textarea'), { value: text });
    input.style.cssText = 'position:fixed;opacity:0';
    document.body.append(input); input.select(); document.execCommand('copy'); input.remove();
  }
  toast(success);
}

/* ---------------------------------- theme & view ------------------------- */
function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('omnisource-theme', theme);
  const meta = $('#themeColor');
  if (meta) meta.content = theme === 'light' ? '#f4f5fa' : '#0b0c10';
  const labels = { auto: 'Theme: system', light: 'Theme: light', dark: 'Theme: dark' };
  $('#themeButton').title = labels[theme];
  $('#themeButton').setAttribute('aria-label', `${labels[theme]}. Change color theme`);
}

function setView(view) {
  state.view = view;
  document.documentElement.dataset.view = view;
  localStorage.setItem('omnisource-view', view);
  const compact = view === 'compact';
  $('#viewToggle').setAttribute('aria-pressed', String(compact));
  $('#viewToggle').setAttribute('aria-label', compact ? 'Use grid view' : 'Use compact view');
  $('#viewToggle').title = compact ? 'Grid view' : 'Compact view';
}

/* ---------------------------------- catalog meta ------------------------- */
function buildCollisions() {
  const bundles = new Map();
  for (const app of state.apps) {
    const key = app.bundleIdentifier;
    if (!key) continue;
    if (!bundles.has(key)) bundles.set(key, []);
    bundles.get(key).push(slugFor(app));
  }
  state.collisions = new Map();
  for (const [bundle, slugs] of bundles) {
    if (slugs.length > 1) state.collisions.set(bundle, slugs);
  }
}

function installUrlFor(clientId, feedUrl) {
  if (clientId === 'altstore' || clientId === 'sidestore') return `${clientId}://source?url=${encodeURIComponent(feedUrl)}`;
  if (clientId === 'feather') return `feather://source/${feedUrl.replace(/^https?:\/\//, '')}`;
  return '';
}

function clientButton(client, feedUrl, label) {
  const icon = client.icon ? `<img src="${escapeHTML(cleanUrl(`assets/${client.icon}`))}" alt="" loading="lazy">` : `<span class="cli-fallback">${escapeHTML((client.name || '?').slice(0, 1).toUpperCase())}</span>`;
  const url = installUrlFor(client.id, feedUrl);
  const common = `class="button client-button client-install"`;
  if (url) {
    return `<a ${common} href="${escapeHTML(url)}" title="Add to ${escapeHTML(client.name)}" aria-label="Add to ${escapeHTML(client.name)}">${icon}${escapeHTML(label || client.name)}</a>`;
  }
  return `<button ${common} type="button" data-copy-url="${escapeHTML(feedUrl)}" title="Open ${escapeHTML(client.name)} and paste this URL" aria-label="Copy feed URL for ${escapeHTML(client.name)}">${icon}${escapeHTML(label || client.name)}<small>+</small></button>`;
}

function renderSourceClients() {
  const row = $('#clientButtons');
  row.innerHTML = state.clients.map(client => clientButton(client, SOURCE_URL)).join('');
}

function renderFooterClients() {
  $('#footerClients').innerHTML = state.clients
    .map(client => {
      const img = client.icon ? `<img src="${escapeHTML(cleanUrl(`assets/${client.icon}`))}" alt="">` : '';
      const url = installUrlFor(client.id, SOURCE_URL);
      const inner = `${img}${escapeHTML(client.name)}`;
      return url
        ? `<a class="client-link" href="${escapeHTML(url)}">${inner}</a>`
        : `<button class="client-link" type="button" data-copy-url="${escapeHTML(SOURCE_URL)}">${inner}</button>`;
    })
    .join('');
}

/* ---------------------------------- filters ------------------------------ */
function renderFilters() {
  const categoryCounts = new Map();
  const statusCounts = new Map();
  for (const app of state.apps) {
    const cat = app.category || 'other';
    categoryCounts.set(cat, (categoryCounts.get(cat) || 0) + 1);
    const status = app.omnisource?.status || 'stable';
    statusCounts.set(status, (statusCounts.get(status) || 0) + 1);
  }
  const categories = [...categoryCounts.keys()].sort((a, b) => categoryLabel(a).localeCompare(categoryLabel(b)));
  const catFilters = [
    { id: 'all', label: 'All apps' },
    { id: 'favorites', label: `Saved (${state.favorites.size})` },
    ...categories.map(id => ({ id, label: `${CATEGORY_ICONS[id] || ''} ${categoryLabel(id)}`, count: categoryCounts.get(id) }))
  ];
  $('#categoryFilters').innerHTML = catFilters.map(filter => `
    <button type="button" class="filter-chip${state.category === filter.id ? ' active' : ''}" data-kind="category" data-id="${escapeHTML(filter.id)}">
      <span>${escapeHTML(filter.label)}</span>${filter.count ? `<span class="count">${filter.count}</span>` : ''}
    </button>`).join('');

  const statuses = [...statusCounts.keys()].sort();
  const statusFilters = [
    { id: 'all', label: 'Any status' },
    ...statuses.map(id => ({ id, label: statusLabel(id), count: statusCounts.get(id) }))
  ];
  $('#statusFilters').innerHTML = statusFilters.map(filter => `
    <button type="button" class="filter-chip${state.status === filter.id ? ' active' : ''}" data-kind="status" data-id="${escapeHTML(filter.id)}">
      <span>${escapeHTML(filter.label)}</span><span class="count">${filter.count}</span>
    </button>`).join('');

  const osLevels = [...new Set(state.apps.map(minOSMajor).filter(value => Number.isFinite(value)))].sort((a, b) => a - b);
  if (osLevels.length) {
    const select = $('#osSelect');
    const current = select.value;
    select.innerHTML = [
      '<option value="any">Any iOS</option>',
      ...osLevels.map(level => `<option value="${level}">Works on iOS ${level}+</option>`)
    ].join('');
    select.value = [...osLevels].includes(Number(current)) ? current : 'any';
  }
}

function filteredApps() {
  const query = state.query.toLowerCase().trim();
  const result = state.apps.filter(app => {
    const slug = slugFor(app);
    const meta = app.omnisource || {};
    const discovery = discoveryFor(app);
    const verification = verificationFor(app);
    const searchText = [
      app.name, app.subtitle, app.localizedDescription, app.developerName,
      app.bundleIdentifier, categoryLabel(app.category), meta.verification?.publisher,
      meta.status, slug,
      ...(discovery?.tags || []),
      verification?.status || ''
    ].join(' ').toLowerCase();
    const categoryMatch = state.category === 'all'
      || (state.category === 'favorites' ? state.favorites.has(slug) : app.category === state.category);
    const statusMatch = state.status === 'all' || (meta.status || 'stable') === state.status;
    const osMajor = minOSMajor(app);
    const osMatch = state.os === 'any' || state.os === '' || osMajor === null || osMajor <= Number(state.os);
    return categoryMatch && statusMatch && osMatch && (!query || searchText.includes(query));
  });
  return result.sort((a, b) => {
    if (state.sort === 'name') return a.name.localeCompare(b.name);
    if (state.sort === 'version') return String(b.version).localeCompare(String(a.version), undefined, { numeric: true });
    if (state.sort === 'updated') return String(b.versionDate).localeCompare(String(a.versionDate));
    if (state.sort === 'size') return (a.size || Infinity) - (b.size || Infinity);
    if (state.sort === 'downloads') return downloadCountFor(b) - downloadCountFor(a) || String(b.versionDate).localeCompare(String(a.versionDate));
    return Number(Boolean(b.omnisource?.featured)) - Number(Boolean(a.omnisource?.featured))
      || String(b.versionDate).localeCompare(String(a.versionDate));
  });
}

/* ---------------------------------- cards -------------------------------- */
function collisionInfo(app) {
  const slugs = state.collisions.get(app.bundleIdentifier) || [];
  if (slugs.length < 2) return null;
  const others = slugs.filter(slug => slug !== slugFor(app));
  return {
    count: others.length + 1,
    names: others.map(slug => state.apps.find(item => slugFor(item) === slug)?.name || slug).join(', ')
  };
}

function cardMarkup(app) {
  const meta = app.omnisource || {};
  const slug = slugFor(app);
  const online = healthFor(app).downloadReachable ?? meta.health?.downloadReachable ?? true;
  const status = meta.status || 'stable';
  const stale = Boolean(healthFor(app).stale);
  const conflict = collisionInfo(app);
  const collisionBadge = conflict
    ? `<span class="badge warn" title="Bundle ID ${escapeHTML(app.bundleIdentifier)} is shared by ${conflict.count} apps: ${escapeHTML(conflict.names)}. Installing one replaces the others on device.">⚠️ Shared bundle ×${conflict.count}</span>` : '';
  const statusBadge = `<span class="badge ${status === 'stable' ? 'stable' : status}">${escapeHTML(statusLabel(status))}</span>`;
  const healthBadge = online
    ? '<span class="badge ok">● Online</span>'
    : '<span class="badge bad">● Offline</span>';
  const staleBadge = stale ? '<span class="badge warn">Stale release</span>' : '';
  const verification = verificationFor(app);
  const verificationBadge = verification
    ? `<span class="badge ${verification.status === 'VERIFIED' ? 'verified' : verification.status === 'COMMUNITY VERIFIED' ? 'community' : 'unverified'}" title="${escapeHTML((verification.checks?.fileAvailable ? 'File available · ' : '') + (verification.hash_verified ? 'Checksum verified' : 'No published checksum'))}">${escapeHTML(VERIFICATION_LABELS[verification.status] || verification.status)}</span>`
    : '';
  const osMajor = minOSMajor(app);
  const icon = cleanUrl(app.iconURL || 'assets/OmniSource.png');
  return `<article class="app-card${conflict ? ' has-collision' : ''}" data-slug="${escapeHTML(slug)}" tabindex="0" role="button" aria-label="View ${escapeHTML(app.name)} details">
    <div class="card-top">
      <div class="icon-wrap">
        <img class="app-icon" src="${escapeHTML(icon)}" alt="" width="58" height="58" loading="lazy">
        <span class="health-dot${online ? '' : ' down'}" title="${online ? 'Download online' : 'Download currently unavailable'}"></span>
      </div>
      <div class="card-identity">
        <div class="name-row"><h3><a href="apps/${escapeHTML(slug)}/" title="Open ${escapeHTML(app.name)} detail page">${escapeHTML(app.name)}</a></h3></div>
        <p class="card-dev">${escapeHTML(app.developerName || app.subtitle || 'Independent developer')}</p>
      </div>
      <button class="favorite${state.favorites.has(slug) ? ' active' : ''}" type="button" data-favorite="${escapeHTML(slug)}" aria-label="${state.favorites.has(slug) ? 'Remove from' : 'Add to'} saved apps" title="Save app" aria-pressed="${state.favorites.has(slug)}">
        <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 20.5S4.5 16.1 4.5 10A4.5 4.5 0 0 1 12 7.2a4.5 4.5 0 0 1 7.5 2.8c0 6.1-7.5 10.5-7.5 10.5Z"/></svg>
      </button>
    </div>
    <div class="card-badges">${statusBadge}${healthBadge}${verificationBadge}${collisionBadge}${staleBadge}</div>
    <p class="app-description">${escapeHTML(app.subtitle || app.localizedDescription || 'View app details and installation options.')}</p>
    <div class="card-meta">
      <span class="meta-item"><b>v${escapeHTML(app.version || '—')}</b></span>
      ${osMajor !== null ? `<span class="meta-item">iOS ${osMajor}+</span>` : ''}
      <span class="meta-item">${escapeHTML(formatBytes(app.size))}</span>
      <span class="meta-item" title="${escapeHTML(formatDate(app.versionDate))}">${escapeHTML(timeAgo(app.versionDate))}</span>
    </div>
    <div class="card-bottom">
      <div class="card-mini"><b>${escapeHTML(categoryLabel(app.category))}</b><span>${escapeHTML(categoryLabel(app.category))}</span></div>
      <div class="card-actions">
        <a class="page-link" href="apps/${escapeHTML(slug)}/" title="Open the static detail page">PAGE ↗</a>
        <button class="get-button" type="button" data-open="${escapeHTML(slug)}">VIEW <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12h13M13 6l6 6-6 6"/></svg></button>
      </div>
    </div>
  </article>`;
}

function renderApps() {
  const apps = filteredApps();
  const grid = $('#appsGrid');
  grid.classList.toggle('compact', state.view === 'compact');
  grid.setAttribute('aria-busy', 'false');
  grid.innerHTML = apps.map(cardMarkup).join('');
  $('#resultCount').textContent = `${apps.length} ${apps.length === 1 ? 'app' : 'apps'}${state.view === 'compact' ? ' listed' : ' shown'}`;
  const filtered = state.category !== 'all' || state.status !== 'all' || state.os !== 'any' || Boolean(state.query);
  $('#clearFilters').hidden = !filtered;
  $('#emptyState').hidden = apps.length > 0;
  grid.hidden = apps.length === 0;

  const groups = [...state.collisions.values()];
  const summary = $('#collisionSummary');
  if (groups.length) {
    const duplicated = new Set(groups.flat());
    summary.hidden = false;
    summary.innerHTML = `<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 3 2.8 20h18.4L12 3Zm0 6v5m0 3.2v.1"/></svg><span title="${escapeHTML([...state.collisions.keys()].join('\n'))}">${groups.length} bundle ID${groups.length === 1 ? '' : 's'} shared by ${duplicated.size} apps</span>`;
  } else {
    summary.hidden = true;
  }
  renderFilters();
}

/* ---------------------------------- dialog ------------------------------- */
function dialogChips(app) {
  const meta = app.omnisource || {};
  const status = meta.status || 'stable';
  const chips = [`<span class="badge ${status === 'stable' ? 'stable' : status} status-line"><span class="dot"></span>${escapeHTML(statusLabel(status))}</span>`];
  const verification = verificationFor(app);
  if (verification) {
    chips.push(`<span class="badge ${verification.status === 'VERIFIED' ? 'verified' : verification.status === 'COMMUNITY VERIFIED' ? 'community' : 'unverified'}" title="${escapeHTML((verification.checks?.fileAvailable ? 'File available · ' : '') + (verification.hash_verified ? 'Checksum verified' : 'No published checksum'))}">${escapeHTML(VERIFICATION_LABELS[verification.status] || verification.status)}</span>`);
  }
  const conflict = collisionInfo(app);
  if (conflict) {
    chips.push(`<span class="badge warn" title="Bundle ID ${escapeHTML(app.bundleIdentifier)} is shared by ${conflict.count} apps (${escapeHTML(conflict.names)}). Installing one replaces the others on device.">⚠️ Same bundle ID ×${conflict.count}</span>`);
  }
  if (healthFor(app).stale && status !== 'unmaintained') chips.push('<span class="badge warn">Stale release</span>');
  return chips.join('');
}

function clientButtonsFor(app, sourceFeed) {
  return state.clients.map(client => clientButton(client, sourceFeed)).join('');
}

function detailTabs() {
  const versionCount = (state.activeApp?.versions || []).length;
  const tabs = [['about', 'About'], ['versions', `Versions${versionCount > 1 ? ` <span class="count">${versionCount}</span>` : ''}`], ['info', 'Details']];
  return `<div class="tabs" role="tablist" aria-label="App details">
    ${tabs.map(([id, label]) => `<button type="button" class="tab${state.activeTab === id ? ' active' : ''}" data-tab="${id}" role="tab" aria-selected="${state.activeTab === id}">${label}</button>`).join('')}
  </div>`;
}

function aboutPanel(app) {
  const screenshots = (app.screenshotURLs || []).filter(url => cleanUrl(url) !== '#');
  return `
    <p class="about-text">${escapeHTML(app.localizedDescription || app.subtitle || 'No description provided.')}</p>
    ${screenshots.length ? `<div class="detail-section"><h3>Preview</h3><div class="screenshots">${screenshots.map((url, index) => `<img src="${escapeHTML(cleanUrl(url))}" alt="${escapeHTML(app.name)} screenshot ${index + 1}" loading="lazy">`).join('')}</div></div>` : ''}`;
}

function versionsPanel(app) {
  const versions = app.versions || [];
  if (!versions.length) return '<p class="body">No version history is published yet.</p>';
  return `<div class="version-list">${versions.map((version, index) => {
    const current = index === 0;
    const notes = version.localizedDescription || '';
    const changelog = notes
      ? `<details class="v-changelog"><summary>Release notes</summary><div class="cl-body">${escapeHTML(notes)}</div></details>` : '';
    return `<div class="version-row">
      <div class="v-main">
        <div class="v-head"><span class="v-ver">v${escapeHTML(version.version)}</span>${current ? '<span class="v-tag">Current</span>' : ''}<span class="v-date">${escapeHTML(formatDate(version.date))}</span></div>
        <div class="v-meta">
          <span>${escapeHTML(formatBytes(version.size))}</span>
          ${version.sha256 ? `<span class="sha" title="SHA-256 of the downloaded IPA"><code>${escapeHTML(version.sha256.slice(0, 12))}…</code><button type="button" data-copy="${escapeHTML(version.sha256)}" aria-label="Copy SHA-256 checksum"><svg aria-hidden="true" viewBox="0 0 24 24"><rect x="8" y="8" width="11" height="11" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></svg></button></span>` : ''}
        </div>
        ${changelog}
      </div>
      <div class="v-side">
        <a class="button primary" href="${escapeHTML(cleanUrl(version.downloadURL))}" target="_blank" rel="noopener">Download</a>
      </div>
    </div>`;
  }).join('')}</div>`;
}

function infoPanel(app) {
  const meta = app.omnisource || {};
  const compatibility = meta.compatibility || {};
  const verification = meta.verification || {};
  const health = healthFor(app);
  const version = app.versions?.[0] || {};
  const osMajor = minOSMajor(app);
  const cells = [
    ['Version', `v${app.version || '—'}`],
    ['Updated', formatDate(app.versionDate)],
    ['Size', formatBytes(app.size)],
    ['Requires iOS', osMajor !== null ? `${osMajor}+` : 'Not listed'],
    ['Category', categoryLabel(app.category)],
    ['Developer', app.developerName || '—'],
    ['Bundle ID', `<button type="button" data-copy="${escapeHTML(app.bundleIdentifier || '')}">${escapeHTML(app.bundleIdentifier || '—')} <svg class="copy-icon" aria-hidden="true" viewBox="0 0 24 24"><rect x="8" y="8" width="11" height="11" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></svg></button>`],
    ['Checksum', version.sha256
      ? `<button type="button" data-copy="${escapeHTML(version.sha256)}">${escapeHTML(version.sha256.slice(0, 16))}…</button>`
      : 'Not published'],
    ['Health', `${health.downloadReachable ? 'Online' : 'Unavailable'}${health.detail ? ` · ${escapeHTML(health.detail)}` : ''}`],
    ['Last release', `${timeAgo(app.versionDate)}${health.updatedDaysAgo ? ` (${health.updatedDaysAgo}d)` : ''}`],
  ];
  const sourceNotes = compatibility.notes;
  const upstreamUrl = cleanUrl(meta.upstreamURL);
  const fallbacks = (app.fallbackDownloadURLs || []).filter(url => cleanUrl(url) !== '#');
  const permissions = app.appPermissions || app.permissions || null;
  const entitlements = permissions?.entitlements || null;
  const privacy = permissions?.privacy || null;
  const privacyEntries = privacy ? Object.entries(privacy) : [];
  const legacyPerms = Array.isArray(app.permissions) ? app.permissions : [];
  return `
    <div class="info-grid">${cells.map(([label, value]) => `<div class="info-cell"><span>${escapeHTML(label)}</span><strong>${value}</strong></div>`).join('')}</div>
    <div class="detail-section"><h3>Build provenance</h3>
      <p class="body">Published by ${escapeHTML(verification.publisher || app.developerName || 'the upstream developer')} · ${escapeHTML((verification.method || 'upstream source').replaceAll('-', ' '))}.
${verification.checksumPublished ? 'An official checksum is published.' : 'No upstream checksum is published.'}${meta.status === 'manual' ? '\n\nCommunity-built IPA of an official project that publishes no IPA itself — see compatibility notes.' : ''}</p>
    </div>
    ${sourceNotes ? `<div class="detail-section"><h3>Compatibility &amp; source notes</h3><div class="detail-note">${escapeHTML(sourceNotes)}</div></div>` : ''}
    ${(entitlements || privacyEntries.length || legacyPerms.length) ? `<div class="detail-section"><h3>Permissions</h3><div class="perm-grid">
      ${entitlements ? `<div class="perm"><b>Entitlements</b><span>${escapeHTML(entitlements.join(', '))}</span></div>` : ''}
      ${privacyEntries.map(([type, usage]) => `<div class="perm"><b>${escapeHTML(type)}</b><span>${escapeHTML(usage)}</span></div>`).join('')}
      ${legacyPerms.map(perm => `<div class="perm"><b>${escapeHTML(perm.type)}</b><span>${escapeHTML(perm.usageDescription)}</span></div>`).join('')}
    </div></div>` : ''}
    ${fallbacks.length ? `<div class="detail-section"><h3>Mirror download links</h3><p class="body">${fallbacks.map(url => `<a href="${escapeHTML(cleanUrl(url))}" target="_blank" rel="noopener">${escapeHTML(url)}</a>`).join('<br>')}</p></div>` : ''}
    <div class="detail-section"><h3>Links</h3><div class="link-row">
      <a href="apps/${escapeHTML(slugFor(app))}/" rel="noopener">Detail page ↗</a>
      <a href="${escapeHTML(cleanUrl(app.downloadURL))}" target="_blank" rel="noopener">Direct IPA ↗</a>
      <a href="${escapeHTML(feedFor(app))}" target="_blank" rel="noopener">App feed ↗</a>
      <a href="${escapeHTML(rssFor(app))}" target="_blank" rel="noopener">App RSS ↗</a>
      ${upstreamUrl !== '#' ? `<a href="${escapeHTML(upstreamUrl)}" target="_blank" rel="noopener">Upstream ↗</a>` : ''}
      <button type="button" data-app-qr>QR code</button>
      <button type="button" data-share>Share</button>
    </div></div>`;
}

function detailMarkup(app) {
  const online = healthFor(app).downloadReachable ?? app.omnisource?.health?.downloadReachable ?? true;
  const sourceFeed = feedFor(app);
  const panels = { about: aboutPanel(app), versions: versionsPanel(app), info: infoPanel(app) };
  const visible = state.activeTab in panels ? state.activeTab : 'about';
  return `<button class="dialog-close" type="button" data-close aria-label="Close details"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18"/></svg></button>
    <div class="dialog-hero">
      <img class="dialog-icon" src="${escapeHTML(cleanUrl(app.iconURL))}" alt="" width="84" height="84">
      <div class="dialog-titles">
        <h2 id="dialogTitle">${escapeHTML(app.name)}</h2>
        <p class="dialog-sub">${escapeHTML(app.subtitle || `By ${app.developerName}`)}</p>
        <div class="dialog-chips">${dialogChips(app)}</div>
      </div>
    </div>
    <div class="dialog-body">
      <div class="install-grid">
        <a class="button primary download" href="${escapeHTML(cleanUrl(app.downloadURL))}" target="_blank" rel="noopener">⬇ Download IPA · ${escapeHTML(formatBytes(app.size))}</a>
        ${clientButtonsFor(app, sourceFeed)}
      </div>
      ${collisionInfo(app) ? `<div class="collision-note"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 3 2.8 20h18.4L12 3Zm0 6v5m0 3.2v.1"/></svg><span><b>Shared bundle ID.</b> ${escapeHTML(collisionInfo(app).names)} also use <code>${escapeHTML(app.bundleIdentifier)}</code> — installing this app replaces whichever of them is installed on the same device.</span></div>` : ''}
      ${detailTabs()}
      <div id="panel-about"${visible === 'about' ? '' : ' hidden'}>${panels.about}</div>
      <div id="panel-versions"${visible === 'versions' ? '' : ' hidden'}>${panels.versions}</div>
      <div id="panel-info"${visible === 'info' ? '' : ' hidden'}>${panels.info}</div>
    </div>`;
}

function openApp(slug, tab = 'about') {
  const app = state.apps.find(item => slugFor(item) === slug);
  if (!app) return;
  state.activeApp = app;
  state.activeTab = tab;
  $('#dialogContent').innerHTML = detailMarkup(app);
  $('#appDialog').showModal();
  history.replaceState(null, '', `#app=${encodeURIComponent(slug)}`);
}

function closeApp() {
  $('#appDialog').close();
  state.activeApp = null;
  if (location.hash.startsWith('#app=')) history.replaceState(null, '', `${location.pathname}${location.search}#catalog`);
}

function switchTab(tab) {
  if (!state.activeApp) return;
  state.activeTab = tab;
  $$('.tab', $('#dialogContent')).forEach(button => {
    button.classList.toggle('active', button.dataset.tab === tab);
    button.setAttribute('aria-selected', String(button.dataset.tab === tab));
  });
  ['about', 'versions', 'info'].forEach(key => {
    const panel = $(`#panel-${key}`);
    if (panel) panel.hidden = key !== tab;
  });
}

function openQr(title, url) {
  $('#qrTitle').textContent = title;
  $('#qrText').textContent = url;
  $('#qrImage').src = `https://api.qrserver.com/v1/create-qr-code/?size=460x460&margin=0&data=${encodeURIComponent(url)}`;
  $('#qrDialog').showModal();
}

async function shareApp(app) {
  const data = { title: `${app.name} on OmniSource`, text: `${app.name} — ${app.subtitle || 'Available on OmniSource'}`, url: feedFor(app) };
  try {
    if (navigator.share) await navigator.share(data);
    else await copyText(data.url, 'App feed copied');
  } catch (error) {
    if (error.name !== 'AbortError') toast('Could not share this app');
  }
}

function clearFilters() {
  state.query = '';
  state.category = 'all';
  state.status = 'all';
  state.os = 'any';
  $('#searchInput').value = '';
  $('#osSelect').value = 'any';
  renderApps();
}

/* ---------------------------------- timeline ----------------------------- */
function renderTimeline() {
  const list = $('#updatesList');
  const updates = (state.updates?.updates || []).slice(0, 8);
  if (!updates.length) {
    list.innerHTML = '';
    $('#updatesNote').hidden = false;
    $('#updatesNote').textContent = 'No releases recorded yet — check back after the next sync.';
    return;
  }
  list.innerHTML = updates.map(item => {
    const icon = cleanUrl(item.iconURL || 'assets/OmniSource.png');
    const kind = KIND_LABELS[item.kind] || item.kind || 'Updated';
    const preview = (item.changelog || item.shortDescription || '').trim();
    const snippet = preview ? preview.slice(0, 220) : `${item.name} version ${item.version} is available.`;
    return `<li class="timeline-item">
      <img class="tl-icon" src="${escapeHTML(icon)}" alt="" loading="lazy">
      <div class="tl-card">
        <div class="tl-head">
          <button type="button" class="tl-name" data-open-app="${escapeHTML(item.slug)}" title="Open ${escapeHTML(item.name)}">${escapeHTML(item.name)}</button>
          <span class="badge ${item.kind === 'new' ? 'ok' : item.kind === 'updated' ? 'neutral' : 'manual'}">${escapeHTML(kind)}</span>
          <span class="tl-date" title="${escapeHTML(formatDate(item.date))}">${escapeHTML(timeAgo(item.date))}</span>
        </div>
        <p class="tl-preview">${escapeHTML(snippet)}${preview.length > 220 ? '…' : ''}</p>
        <div class="tl-foot">
          <button type="button" class="version-chip" data-open-app="${escapeHTML(item.slug)}">v${escapeHTML(item.version)}</button>
          <div class="tl-actions">
            <button type="button" data-open-app="${escapeHTML(item.slug)}">Details</button>
            <a href="${escapeHTML(item.rssURL || '')}" title="Per-app RSS feed">RSS</a>
            ${item.downloadURL ? `<a href="${escapeHTML(cleanUrl(item.downloadURL))}" target="_blank" rel="noopener" title="Direct download">IPA</a>` : ''}
          </div>
        </div>
      </div>
    </li>`;
  }).join('');
  $('#updatesNote').hidden = true;
}

/* ---------------------------------- load -------------------------------- */
function renderStats() {
  const total = state.apps.length;
  const totals = state.analytics?.totals || {};
  const healthy = state.health?.totals?.reachable ?? state.apps.filter(app => healthFor(app).downloadReachable !== false).length;
  const verified = totals.verifiedApps ?? state.apps.filter(app => verificationFor(app)?.status === 'VERIFIED').length;
  const sources = totals.sources ?? new Set(state.apps.map(app => app.omnisource?.upstreamURL || app.omnisource?.verification?.publisher || app.developerName)).size;
  const lastSync = totals.lastSync !== undefined ? totals.lastSync : state.analytics?.lastSync || null;

  $('#appTotal').textContent = total;
  $('#sourceTotal').textContent = sources;
  $('#verifiedTotal').textContent = `${verified}/${total}`;
  $('#lastSync').textContent = lastSync ? timeAgo(lastSync) : '—';
  $('#lastSync').setAttribute('title', lastSync ? formatDate(lastSync) : 'Awaiting first sync');
  $('#sourceTotal').setAttribute('title', `${sources} upstream sources`);
  $('#verifiedTotal').setAttribute('title', `${verified} of ${total} apps have a verified upstream provenance`);
  $('.stat-card:nth-child(2)').classList.toggle('ok', sources > 0);
  $('.stat-card:nth-child(4)').classList.toggle('ok', verified === total && total > 0);
  $('.stat-card:nth-child(3)').classList.toggle('warn', Boolean(totals.deadLinks));

  const label = $('#healthLabel');
  if (total === 0) {
    label.textContent = 'Source status unavailable';
  } else if (healthy === total) {
    label.textContent = `All ${total} downloads verified online`;
  } else {
    label.textContent = `${healthy} of ${total} downloads online`;
    $('.eyebrow').classList.add('is-error');
  }
  if (state.source?.subtitle) $('#heroCopy').textContent = state.source.subtitle;
  if (state.source?.name) {
    document.title = `${state.source.name} — Curated iOS Apps, Always Current`;
  }
}

async function loadCatalog() {
  try {
    const [feedResponse, healthResponse, updatesResponse, catalogResponse, analyticsResponse, verificationResponse, discoveryResponse] = await Promise.all([
      fetch('apps.json'),
      fetch('feeds/health.json').catch(() => null),
      fetch('feeds/updates.json').catch(() => null),
      fetch('catalog.json').catch(() => null),
      fetch('feeds/analytics.json').catch(() => null),
      fetch('feeds/verification.json').catch(() => null),
      fetch('discovery.json').catch(() => null)
    ]);
    if (!feedResponse.ok) throw new Error(`Feed returned ${feedResponse.status}`);
    const feed = await feedResponse.json();
    state.apps = feed.apps || [];
    if (healthResponse?.ok) state.health = await healthResponse.json();
    if (updatesResponse?.ok) state.updates = await updatesResponse.json();
    if (analyticsResponse?.ok) state.analytics = await analyticsResponse.json();
    if (verificationResponse?.ok) {
      const doc = await verificationResponse.json();
      for (const entry of doc.apps || []) state.verification.set(entry.app, entry);
    }
    if (discoveryResponse?.ok) {
      const doc = await discoveryResponse.json();
      for (const entry of doc.apps || []) state.discovery.set(entry.id || entry.slug, entry);
    }
    if (catalogResponse?.ok) {
      const meta = await catalogResponse.json();
      state.source = meta.source || null;
      state.clients = meta.clients || [];
    } else {
      state.clients = [
        { id: 'altstore', name: 'AltStore', icon: 'AltStore.png' },
        { id: 'sidestore', name: 'SideStore', icon: 'SideStore.png' },
        { id: 'feather', name: 'Feather', icon: 'Feather.png' },
        { id: 'esign', name: 'ESign', icon: 'E-Sign.png' },
        { id: 'livecontainer', name: 'LiveContainer', icon: 'LiveContainer.png' }
      ];
    }
    if (state.source?.baseURL) {
      const base = String(state.source.baseURL).replace(/\/$/, '');
      $('#sourceUrl').textContent = `${base}/apps.json`;
    }
    buildCollisions();
    renderSourceClients();
    renderFooterClients();
    renderStats();
    renderApps();
    renderTimeline();
    $('#appTotal').textContent = state.apps.length;

    const hashSlug = location.hash.match(/^#app=(.+)$/)?.[1];
    if (hashSlug) openApp(decodeURIComponent(hashSlug));
  } catch (error) {
    console.error(error);
    $('#appsGrid').innerHTML = '';
    $('#appsGrid').hidden = true;
    $('#emptyState').hidden = false;
    $('#emptyState h3').textContent = 'Catalog unavailable';
    $('#emptyState p').textContent = 'The live feed could not be loaded. Please try again shortly.';
    $('#resultCount').textContent = 'Unable to load apps';
    $('#healthLabel').textContent = 'Source status unavailable';
    $('.eyebrow').classList.add('is-error');
  }
}

/* ---------------------------------- events ------------------------------- */
function bindEvents() {
  const initialTheme = localStorage.getItem('omnisource-theme') || 'auto';
  setTheme(['auto', 'light', 'dark'].includes(initialTheme) ? initialTheme : 'auto');
  setView(state.view);
  $('#year').textContent = new Date().getFullYear();

  $('#themeButton').addEventListener('click', () => {
    const themes = ['auto', 'light', 'dark'];
    setTheme(themes[(themes.indexOf(document.documentElement.dataset.theme) + 1) % themes.length]);
  });
  $('#viewToggle').addEventListener('click', () => setView(state.view === 'compact' ? 'grid' : 'compact'));
  $('#copySource').addEventListener('click', () => copyText(SOURCE_URL, 'Source URL copied'));
  $('#sourceQr').addEventListener('click', () => openQr('OmniSource', SOURCE_URL));
  $('#qrCopy').addEventListener('click', () => copyText($('#qrText').textContent, 'Source URL copied'));

  const searchInput = $('#searchInput');
  searchInput.addEventListener('input', event => { state.query = event.target.value; renderApps(); });
  searchInput.addEventListener('keydown', event => {
    if (event.key === 'Escape' && state.query) { state.query = ''; searchInput.value = ''; renderApps(); }
  });
  $('#sortSelect').addEventListener('change', event => { state.sort = event.target.value; renderApps(); });
  $('#osSelect').addEventListener('change', event => {
    state.os = event.target.value === 'any' ? 'any' : Number(event.target.value);
    renderApps();
  });

  document.querySelector('.filter-groups').addEventListener('click', event => {
    const chip = event.target.closest('[data-kind]');
    if (!chip) return;
    const { kind, id } = chip.dataset;
    if (kind === 'category') state.category = state.category === id ? 'all' : id;
    if (kind === 'status') state.status = state.status === id ? 'all' : id;
    renderApps();
  });

  $('#clearFilters').addEventListener('click', clearFilters);
  $('#emptyClear').addEventListener('click', clearFilters);

  $('#appsGrid').addEventListener('click', event => {
    const favorite = event.target.closest('[data-favorite]');
    if (favorite) {
      event.stopPropagation();
      const slug = favorite.dataset.favorite;
      if (state.favorites.has(slug)) state.favorites.delete(slug);
      else state.favorites.add(slug);
      localStorage.setItem('omnisource-favorites', JSON.stringify([...state.favorites]));
      renderApps();
      toast(state.favorites.has(slug) ? 'Saved for later' : 'Removed from saved apps');
      return;
    }
    const card = event.target.closest('[data-slug]');
    if (card) openApp(card.dataset.slug);
  });
  $('#appsGrid').addEventListener('keydown', event => {
    if ((event.key === 'Enter' || event.key === ' ') && event.target.matches('.app-card')) {
      event.preventDefault();
      openApp(event.target.dataset.slug);
    }
  });

  const appDialog = $('#appDialog');
  appDialog.addEventListener('click', event => {
    if (event.target === appDialog || event.target.closest('[data-close]')) { closeApp(); return; }
    if (event.target.closest('.tab')) { switchTab(event.target.closest('.tab').dataset.tab); return; }
    if (event.target.closest('[data-copy]')) {
      copyText(event.target.closest('[data-copy]').dataset.copy, 'Copied');
      return;
    }
    const qr = event.target.closest('[data-app-qr]');
    if (qr && state.activeApp) {
      const app = state.activeApp;
      closeApp();
      openQr(app.name, feedFor(app));
      return;
    }
    const share = event.target.closest('[data-share]');
    if (share && state.activeApp) shareApp(state.activeApp);
  });
  appDialog.addEventListener('cancel', event => { event.preventDefault(); closeApp(); });

  $('#qrDialog').addEventListener('click', event => {
    if (event.target === $('#qrDialog') || event.target.closest('[data-close]')) $('#qrDialog').close();
  });

  document.body.addEventListener('click', event => {
    const copy = event.target.closest('[data-copy-url]');
    if (copy) { copyText(copy.dataset.copyUrl, 'URL copied — paste it in your client'); return; }
    const openAppBtn = event.target.closest('[data-open-app]');
    if (openAppBtn) {
      const slug = openAppBtn.dataset.openApp;
      const app = state.apps.find(item => slugFor(item) === slug);
      if (app) openApp(slug);
    }
  });

  document.addEventListener('keydown', event => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      $('#searchInput').focus();
      $('#catalog').scrollIntoView();
    }
  });
}

function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) return;
  if (location.protocol !== 'https:') return;
  const host = location.hostname.toLowerCase();
  const parts = host.split('.');
  const isLocalhost = host === 'localhost' || host === '127.0.0.1';
  const isGithubPagesHost = parts.length === 3 && parts[1] === 'github' && parts[2] === 'io';
  if (!isGithubPagesHost && !isLocalhost) return;
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('sw.js').catch(() => { /* offline support is progressive */ });
  });
}

bindEvents();
loadCatalog();
registerServiceWorker();
