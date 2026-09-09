'use strict';

const SOURCE_URL = 'https://iamsmmh.github.io/OmniSource/apps.json';
const BASE_URL = 'https://iamsmmh.github.io/OmniSource';
const state = {
  apps: [],
  health: null,
  query: '',
  category: 'all',
  sort: 'featured',
  compact: localStorage.getItem('omnisource-view') === 'compact',
  favorites: new Set(JSON.parse(localStorage.getItem('omnisource-favorites') || '[]')),
  activeApp: null
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const escapeHTML = value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
const cleanUrl = value => {
  try {
    const url = new URL(value, location.href);
    return ['http:', 'https:'].includes(url.protocol) ? url.href : '#';
  } catch { return '#'; }
};
const slugFor = app => app.omnisource?.slug || app.bundleIdentifier?.split('.').pop()?.toLowerCase() || 'app';
const feedFor = app => `${BASE_URL}/${encodeURIComponent(slugFor(app))}.json`;
const formatBytes = bytes => {
  if (!Number(bytes)) return 'Unknown';
  const units = ['B', 'KB', 'MB', 'GB'];
  const unit = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** unit).toFixed(unit > 1 ? 1 : 0)} ${units[unit]}`;
};
const formatDate = value => {
  if (!value) return 'Unknown';
  const date = new Date(value.length === 10 ? `${value}T12:00:00Z` : value);
  return Number.isNaN(date.valueOf()) ? value : new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric' }).format(date);
};
const categoryLabel = category => ({
  'photo-video': 'Photo & Video', music: 'Music', social: 'Social', news: 'News',
  utilities: 'Utilities', networking: 'Networking', games: 'Games', 'developer-tools': 'Developer Tools', other: 'Other'
}[category] || 'Other');

function toast(message) {
  const node = $('#toast');
  $('span', node).textContent = message;
  node.classList.add('show');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => node.classList.remove('show'), 2400);
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

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('omnisource-theme', theme);
  const labels = { auto: 'Theme: system', light: 'Theme: light', dark: 'Theme: dark' };
  $('#themeButton').title = labels[theme];
  $('#themeButton').setAttribute('aria-label', `${labels[theme]}. Change color theme`);
}

function renderFilters() {
  const categories = [...new Set(state.apps.map(app => app.category || 'other'))].sort((a, b) => categoryLabel(a).localeCompare(categoryLabel(b)));
  const filters = [{ id: 'all', label: 'All apps' }, { id: 'favorites', label: `Saved (${state.favorites.size})` }, ...categories.map(id => ({ id, label: categoryLabel(id) }))];
  $('#categoryFilters').innerHTML = filters.map(filter => `<button type="button" class="filter-chip${state.category === filter.id ? ' active' : ''}" data-category="${escapeHTML(filter.id)}">${escapeHTML(filter.label)}</button>`).join('');
}

function filteredApps() {
  const query = state.query.toLowerCase().trim();
  const result = state.apps.filter(app => {
    const slug = slugFor(app);
    const searchText = [app.name, app.subtitle, app.localizedDescription, app.developerName, app.bundleIdentifier, app.category].join(' ').toLowerCase();
    const categoryMatch = state.category === 'all' || (state.category === 'favorites' ? state.favorites.has(slug) : app.category === state.category);
    return categoryMatch && (!query || searchText.includes(query));
  });
  return result.sort((a, b) => {
    if (state.sort === 'name') return a.name.localeCompare(b.name);
    if (state.sort === 'updated') return String(b.versionDate).localeCompare(String(a.versionDate));
    if (state.sort === 'size') return (a.size || Infinity) - (b.size || Infinity);
    return Number(Boolean(b.omnisource?.featured)) - Number(Boolean(a.omnisource?.featured)) || String(b.versionDate).localeCompare(String(a.versionDate));
  });
}

function cardMarkup(app) {
  const meta = app.omnisource || {};
  const slug = slugFor(app);
  const online = meta.health?.downloadReachable !== false;
  const minOS = meta.compatibility?.minOSVersion;
  const icon = cleanUrl(app.iconURL || 'assets/OmniSource.png');
  return `<article class="app-card" data-slug="${escapeHTML(slug)}" tabindex="0" aria-label="View ${escapeHTML(app.name)} details">
    <div class="card-top">
      <img class="app-icon" src="${escapeHTML(icon)}" alt="${escapeHTML(app.name)} icon" width="58" height="58" loading="lazy">
      <div class="card-identity"><h3>${escapeHTML(app.name)}</h3><p>${escapeHTML(app.developerName || app.subtitle || 'Independent developer')}</p></div>
      <button class="favorite${state.favorites.has(slug) ? ' active' : ''}" type="button" data-favorite="${escapeHTML(slug)}" aria-label="${state.favorites.has(slug) ? 'Remove from' : 'Add to'} saved apps" title="Save app">
        <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 20.5S4.5 16.1 4.5 10A4.5 4.5 0 0 1 12 7.2 4.5 4.5 0 0 1 19.5 10c0 6.1-7.5 10.5-7.5 10.5Z"/></svg>
      </button>
    </div>
    <p class="app-description">${escapeHTML(app.subtitle || app.localizedDescription || 'View app details and installation options.')}</p>
    <div class="tag-row"><span class="tag ${online ? 'online' : ''}">${online ? '● Online' : 'Unavailable'}</span><span class="tag">${escapeHTML(categoryLabel(app.category))}</span>${minOS ? `<span class="tag">iOS ${escapeHTML(minOS)}+</span>` : ''}</div>
    <div class="card-bottom"><div class="version"><strong>v${escapeHTML(app.version || '—')}</strong><span>${escapeHTML(formatDate(app.versionDate))}</span></div><button class="get-button" type="button" data-open="${escapeHTML(slug)}">VIEW</button></div>
  </article>`;
}

function renderApps() {
  const apps = filteredApps();
  const grid = $('#appsGrid');
  grid.classList.toggle('compact', state.compact);
  grid.setAttribute('aria-busy', 'false');
  grid.innerHTML = apps.map(cardMarkup).join('');
  $('#resultCount').textContent = `${apps.length} ${apps.length === 1 ? 'app' : 'apps'} shown`;
  const filtered = state.category !== 'all' || Boolean(state.query);
  $('#clearFilters').hidden = !filtered;
  $('#emptyState').hidden = apps.length > 0;
  grid.hidden = apps.length === 0;
  renderFilters();
}

function detailMarkup(app) {
  const meta = app.omnisource || {};
  const compatibility = meta.compatibility || {};
  const verification = meta.verification || {};
  const online = meta.health?.downloadReachable !== false;
  const sourceFeed = feedFor(app);
  const altUrl = `altstore://source?url=${encodeURIComponent(sourceFeed)}`;
  const sideUrl = `sidestore://source?url=${encodeURIComponent(sourceFeed)}`;
  const featherUrl = `feather://source/${sourceFeed.replace(/^https?:\/\//, '')}`;
  const screenshots = (app.screenshotURLs || []).filter(url => cleanUrl(url) !== '#');
  const notes = compatibility.notes;
  const releaseNotes = app.versionDescription || app.versions?.[0]?.localizedDescription;
  return `<button class="dialog-close" type="button" data-close aria-label="Close details"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18"/></svg></button>
    <div class="dialog-hero"><img class="dialog-icon" src="${escapeHTML(cleanUrl(app.iconURL))}" alt="" width="80" height="80"><div class="dialog-title-wrap"><h2 id="dialogTitle">${escapeHTML(app.name)}</h2><p>${escapeHTML(app.subtitle || `By ${app.developerName}`)}</p><span class="status-line">● ${online ? 'Download verified' : 'Download unavailable'} · ${escapeHTML(meta.status || 'stable')}</span></div></div>
    <div class="dialog-body">
      <div class="dialog-actions">
        <a class="button primary" href="${escapeHTML(cleanUrl(app.downloadURL))}" target="_blank" rel="noopener">Download IPA · ${escapeHTML(formatBytes(app.size))}</a>
        <a class="button" href="${escapeHTML(altUrl)}">AltStore</a>
        <a class="button" href="${escapeHTML(sideUrl)}">SideStore</a>
        <a class="button" href="${escapeHTML(featherUrl)}">Feather</a>
      </div>
      <div class="detail-grid">
        <div><span>Version</span><strong>${escapeHTML(app.version || '—')}</strong></div>
        <div><span>Requires</span><strong>${compatibility.minOSVersion ? `iOS ${escapeHTML(compatibility.minOSVersion)}+` : 'Not listed'}</strong></div>
        <div><span>Updated</span><strong>${escapeHTML(formatDate(app.versionDate))}</strong></div>
        <div><span>Size</span><strong>${escapeHTML(formatBytes(app.size))}</strong></div>
      </div>
      <section class="detail-section"><h3>About</h3><p>${escapeHTML(app.localizedDescription || app.subtitle || 'No description provided.')}</p></section>
      ${screenshots.length ? `<section class="detail-section"><h3>Preview</h3><div class="screenshots">${screenshots.map((url, index) => `<img src="${escapeHTML(cleanUrl(url))}" alt="${escapeHTML(app.name)} screenshot ${index + 1}" loading="lazy">`).join('')}</div></section>` : ''}
      ${releaseNotes ? `<section class="detail-section"><h3>Latest release</h3><p>${escapeHTML(releaseNotes)}</p></section>` : ''}
      ${notes ? `<section class="detail-section"><h3>Compatibility & source notes</h3><p class="detail-note">${escapeHTML(notes)}</p></section>` : ''}
      <section class="detail-section"><h3>Build provenance</h3><p>Published by ${escapeHTML(verification.publisher || app.developerName || 'the upstream developer')} · ${escapeHTML((verification.method || 'upstream source').replaceAll('-', ' '))}. ${verification.checksumPublished ? 'A checksum is published.' : 'No upstream checksum is published.'}</p></section>
      <section class="detail-section"><h3>Links</h3><div class="detail-links"><a href="${escapeHTML(sourceFeed)}" target="_blank" rel="noopener">App feed ↗</a>${meta.upstreamURL ? `<a href="${escapeHTML(cleanUrl(meta.upstreamURL))}" target="_blank" rel="noopener">Upstream ↗</a>` : ''}<button type="button" data-app-qr="${escapeHTML(slugFor(app))}">QR code</button><button type="button" data-share="${escapeHTML(slugFor(app))}">Share</button><button type="button" data-copy-bundle="${escapeHTML(app.bundleIdentifier || '')}">Copy bundle ID</button></div></section>
    </div>`;
}

function openApp(slug) {
  const app = state.apps.find(item => slugFor(item) === slug);
  if (!app) return;
  state.activeApp = app;
  $('#dialogContent').innerHTML = detailMarkup(app);
  $('#appDialog').showModal();
  history.replaceState(null, '', `#app=${encodeURIComponent(slug)}`);
}

function closeApp() {
  $('#appDialog').close();
  state.activeApp = null;
  if (location.hash.startsWith('#app=')) history.replaceState(null, '', `${location.pathname}${location.search}#catalog`);
}

function openQr(title, url) {
  $('#qrTitle').textContent = title;
  $('#qrText').textContent = url;
  $('#qrImage').src = `https://api.qrserver.com/v1/create-qr-code/?size=440x440&margin=0&data=${encodeURIComponent(url)}`;
  $('#qrDialog').showModal();
}

async function shareApp(app) {
  const data = { title: `${app.name} on OmniSource`, text: `${app.name} — ${app.subtitle || 'Available on OmniSource'}`, url: feedFor(app) };
  try { if (navigator.share) await navigator.share(data); else await copyText(data.url, 'App feed copied'); } catch (error) { if (error.name !== 'AbortError') toast('Could not share this app'); }
}

function clearFilters() {
  state.query = ''; state.category = 'all';
  $('#searchInput').value = '';
  renderApps();
}

async function loadCatalog() {
  try {
    const [feedResponse, healthResponse] = await Promise.all([fetch('apps.json'), fetch('feeds/health.json').catch(() => null)]);
    if (!feedResponse.ok) throw new Error(`Feed returned ${feedResponse.status}`);
    const feed = await feedResponse.json();
    state.apps = feed.apps || [];
    if (healthResponse?.ok) state.health = await healthResponse.json();
    const total = state.apps.length;
    const online = state.health?.totals?.reachable ?? state.apps.filter(app => app.omnisource?.health?.downloadReachable !== false).length;
    $('#appTotal').textContent = total;
    $('#healthyTotal').textContent = `${online}/${total}`;
    $('#healthLabel').textContent = online === total ? `All ${total} downloads online` : `${online} of ${total} downloads online`;
    if (online !== total) $('.eyebrow').classList.add('is-error');
    renderApps();
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

function bindEvents() {
  const initialTheme = localStorage.getItem('omnisource-theme') || 'auto';
  setTheme(['auto', 'light', 'dark'].includes(initialTheme) ? initialTheme : 'auto');
  $('#year').textContent = new Date().getFullYear();
  $('#viewToggle').setAttribute('aria-pressed', String(state.compact));

  $('#themeButton').addEventListener('click', () => {
    const themes = ['auto', 'light', 'dark'];
    setTheme(themes[(themes.indexOf(document.documentElement.dataset.theme) + 1) % themes.length]);
  });
  $('#copySource').addEventListener('click', () => copyText(SOURCE_URL, 'Source URL copied'));
  $('#sourceQr').addEventListener('click', () => openQr('OmniSource', SOURCE_URL));
  $('#qrCopy').addEventListener('click', () => copyText($('#qrText').textContent, 'Source URL copied'));
  $('#searchInput').addEventListener('input', event => { state.query = event.target.value; renderApps(); });
  $('#sortSelect').addEventListener('change', event => { state.sort = event.target.value; renderApps(); });
  $('#viewToggle').addEventListener('click', () => {
    state.compact = !state.compact;
    localStorage.setItem('omnisource-view', state.compact ? 'compact' : 'grid');
    $('#viewToggle').setAttribute('aria-pressed', String(state.compact));
    $('#viewToggle').setAttribute('aria-label', state.compact ? 'Use grid view' : 'Use compact view');
    renderApps();
  });
  $('#categoryFilters').addEventListener('click', event => {
    const button = event.target.closest('[data-category]');
    if (button) { state.category = button.dataset.category; renderApps(); }
  });
  $('#clearFilters').addEventListener('click', clearFilters);
  $('#emptyClear').addEventListener('click', clearFilters);
  $('#appsGrid').addEventListener('click', event => {
    const favorite = event.target.closest('[data-favorite]');
    if (favorite) {
      event.stopPropagation();
      const slug = favorite.dataset.favorite;
      state.favorites.has(slug) ? state.favorites.delete(slug) : state.favorites.add(slug);
      localStorage.setItem('omnisource-favorites', JSON.stringify([...state.favorites]));
      renderApps(); toast(state.favorites.has(slug) ? 'Saved for later' : 'Removed from saved apps'); return;
    }
    const card = event.target.closest('[data-slug]');
    if (card) openApp(card.dataset.slug);
  });
  $('#appsGrid').addEventListener('keydown', event => {
    if ((event.key === 'Enter' || event.key === ' ') && event.target.matches('.app-card')) { event.preventDefault(); openApp(event.target.dataset.slug); }
  });
  $('#appDialog').addEventListener('click', event => {
    if (event.target === $('#appDialog') || event.target.closest('[data-close]')) closeApp();
    const qr = event.target.closest('[data-app-qr]');
    if (qr && state.activeApp) {
      const app = state.activeApp;
      closeApp();
      openQr(app.name, feedFor(app));
    }
    const share = event.target.closest('[data-share]'); if (share && state.activeApp) shareApp(state.activeApp);
    const bundle = event.target.closest('[data-copy-bundle]'); if (bundle) copyText(bundle.dataset.copyBundle, 'Bundle ID copied');
  });
  $('#qrDialog').addEventListener('click', event => { if (event.target === $('#qrDialog') || event.target.closest('[data-close]')) $('#qrDialog').close(); });
  $('#appDialog').addEventListener('cancel', event => { event.preventDefault(); closeApp(); });
  document.addEventListener('keydown', event => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); $('#searchInput').focus(); $('#catalog').scrollIntoView(); }
  });
}

bindEvents();
loadCatalog();
