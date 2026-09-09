'use strict';

const COMPARE_URL = 'feeds/compare.json';
const state = { pairs: [], bySlug: new Map(), left: null, right: null };

const $ = sel => document.querySelector(sel);
const escapeHTML = value => String(value ?? '').replace(/[&<>'"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[ch]));

function loadPairs() {
  return fetch(COMPARE_URL, { cache: 'no-cache' })
    .then(res => res.ok ? res.json() : Promise.reject(new Error(`compare.json ${res.status}`)))
    .then(doc => {
      state.pairs = doc.pairs || [];
      const apps = new Map();
      for (const pair of state.pairs) {
        if (pair.left?.slug) apps.set(pair.left.slug, pair.left);
        if (pair.right?.slug) apps.set(pair.right.slug, pair.right);
      }
      state.bySlug = apps;
    });
}

function renderSelects() {
  const left = $('#leftSelect');
  const right = $('#rightSelect');
  const options = [...state.bySlug.values()]
    .sort((a, b) => a.name.localeCompare(b.name))
    .map(app => `<option value="${escapeHTML(app.slug)}">${escapeHTML(app.name)}</option>`)
    .join('');
  left.innerHTML = options;
  right.innerHTML = options;
  // Default to a meaningful pair: first pair that shares a bundle.
  const featured = state.pairs.find(p => p.shareBundle) || state.pairs[0];
  if (featured) {
    left.value = featured.left.slug;
    right.value = featured.right.slug;
    state.left = featured.left.slug;
    state.right = featured.right.slug;
  }
}

function renderPairList() {
  const list = $('#pairList');
  const featured = state.pairs.filter(p => p.shareBundle).slice(0, 12);
  if (!featured.length) { $('#pairs').hidden = true; return; }
  list.innerHTML = featured.map(p => `
    <li>
      <button type="button" data-left="${escapeHTML(p.left.slug)}" data-right="${escapeHTML(p.right.slug)}">
        <img src="${escapeHTML(p.left.icon || 'assets/OmniSource.png')}" alt="" width="32" height="32" loading="lazy" onerror="this.src='assets/OmniSource.png'">
        <span class="pair-vs">${escapeHTML(p.left.name)} <em>vs</em> ${escapeHTML(p.right.name)}</span>
        <span class="pair-meta">${p.shareBundle ? 'Same bundle' : p.shareCategory ? 'Same category' : ''}</span>
        <span class="pair-arrow" aria-hidden="true">→</span>
      </button>
    </li>
  `).join('');
  $('#pairs').hidden = false;
  list.addEventListener('click', event => {
    const btn = event.target.closest('button');
    if (!btn) return;
    state.left = btn.dataset.left;
    state.right = btn.dataset.right;
    $('#leftSelect').value = state.left;
    $('#rightSelect').value = state.right;
    renderResult();
  });
}

function row(label, leftValue, rightValue) {
  return `<tr><th scope="row">${escapeHTML(label)}</th><td>${leftValue}</td><td>${rightValue}</td></tr>`;
}

function badge(text, cls = '') {
  return `<span class="badge ${cls}">${escapeHTML(text)}</span>`;
}

function renderResult() {
  if (!state.left || !state.right || state.left === state.right) {
    $('#result').hidden = true;
    $('#emptyState').hidden = false;
    return;
  }
  const left = state.bySlug.get(state.left);
  const right = state.bySlug.get(state.right);
  if (!left || !right) return;

  const verificationBadge = level => badge(level, level === 'VERIFIED' ? 'verified' : level === 'COMMUNITY' ? 'community' : 'manual');
  const winner = state.pairs.find(p => p.left.slug === left.slug && p.right.slug === right.slug)?.winner;

  const grid = $('#resultGrid');
  grid.innerHTML = `
    <article class="compare-side">
      <header>
        <img src="${escapeHTML(left.icon || 'assets/OmniSource.png')}" alt="" width="64" height="64" onerror="this.src='assets/OmniSource.png'">
        <div>
          <h2><a href="apps/${encodeURIComponent(left.slug)}/">${escapeHTML(left.name)}</a></h2>
          <p>${escapeHTML(left.category || '')} · ${escapeHTML(left.developer || '')}</p>
          <div class="chips">${verificationBadge(left.verificationLevel || 'UNVERIFIED')} ${left.downloadReachable ? badge('● Online', 'ok') : badge('● Offline', 'bad')}</div>
        </div>
        ${winner === left.slug ? '<span class="winner-tag">Recommended pick</span>' : ''}
      </header>
      <table class="compare-table">
        <tbody>
          ${row('Version', `v${escapeHTML(left.version || '—')}`, `v${escapeHTML(right.version || '—')}`)}
          ${row('Released', escapeHTML(left.releaseDate || '—'), escapeHTML(right.releaseDate || '—'))}
          ${row('Source', escapeHTML(left.source || '—'), escapeHTML(right.source || '—'))}
          ${row('Verification', verificationBadge(left.verificationLevel || 'UNVERIFIED'), verificationBadge(right.verificationLevel || 'UNVERIFIED'))}
          ${row('Update gap (days)', escapeHTML(String(left.updateFrequencyDays || '—')), escapeHTML(String(right.updateFrequencyDays || '—')))}
          ${row('Min iOS', escapeHTML(left.compatibility?.minOSVersion || '—'), escapeHTML(right.compatibility?.minOSVersion || '—'))}
          ${row('Devices', escapeHTML((left.compatibility?.devices || []).join(', ') || '—'), escapeHTML((right.compatibility?.devices || []).join(', ') || '—'))}
        </tbody>
      </table>
    </article>
    <article class="compare-side">
      <header>
        <img src="${escapeHTML(right.icon || 'assets/OmniSource.png')}" alt="" width="64" height="64" onerror="this.src='assets/OmniSource.png'">
        <div>
          <h2><a href="apps/${encodeURIComponent(right.slug)}/">${escapeHTML(right.name)}</a></h2>
          <p>${escapeHTML(right.category || '')} · ${escapeHTML(right.developer || '')}</p>
          <div class="chips">${verificationBadge(right.verificationLevel || 'UNVERIFIED')} ${right.downloadReachable ? badge('● Online', 'ok') : badge('● Offline', 'bad')}</div>
        </div>
        ${winner === right.slug ? '<span class="winner-tag">Recommended pick</span>' : ''}
      </header>
      <table class="compare-table">
        <tbody>
          ${row('Version', `v${escapeHTML(left.version || '—')}`, `v${escapeHTML(right.version || '—')}`)}
          ${row('Released', escapeHTML(left.releaseDate || '—'), escapeHTML(right.releaseDate || '—'))}
          ${row('Source', escapeHTML(left.source || '—'), escapeHTML(right.source || '—'))}
          ${row('Verification', verificationBadge(left.verificationLevel || 'UNVERIFIED'), verificationBadge(right.verificationLevel || 'UNVERIFIED'))}
          ${row('Update gap (days)', escapeHTML(String(left.updateFrequencyDays || '—')), escapeHTML(String(right.updateFrequencyDays || '—')))}
          ${row('Min iOS', escapeHTML(left.compatibility?.minOSVersion || '—'), escapeHTML(right.compatibility?.minOSVersion || '—'))}
          ${row('Devices', escapeHTML((left.compatibility?.devices || []).join(', ') || '—'), escapeHTML((right.compatibility?.devices || []).join(', ') || '—'))}
        </tbody>
      </table>
    </article>
  `;
  // Screenshots / icon gallery fallback.
  const screens = $('#resultScreens');
  screens.innerHTML = `
    <article>
      <h3>${escapeHTML(left.name)}</h3>
      <div class="icon-gallery">
        <img src="${escapeHTML(left.icon || 'assets/OmniSource.png')}" alt="${escapeHTML(left.name)}" loading="lazy" onerror="this.src='assets/OmniSource.png'">
      </div>
      <p><a class="button" href="apps/${encodeURIComponent(left.slug)}/">Open detail page →</a></p>
    </article>
    <article>
      <h3>${escapeHTML(right.name)}</h3>
      <div class="icon-gallery">
        <img src="${escapeHTML(right.icon || 'assets/OmniSource.png')}" alt="${escapeHTML(right.name)}" loading="lazy" onerror="this.src='assets/OmniSource.png'">
      </div>
      <p><a class="button" href="apps/${encodeURIComponent(right.slug)}/">Open detail page →</a></p>
    </article>
  `;
  $('#result').hidden = false;
  $('#emptyState').hidden = true;
}

$('#compareForm')?.addEventListener('submit', event => {
  event.preventDefault();
  state.left = $('#leftSelect').value;
  state.right = $('#rightSelect').value;
  renderResult();
});

loadPairs()
  .then(renderSelects)
  .then(renderPairList)
  .then(renderResult)
  .catch(error => {
    console.error(error);
    $('#emptyState').hidden = false;
    $('#emptyState h3').textContent = 'Comparison data unavailable';
    $('#emptyState p').textContent = 'The compare feed could not be loaded. Try again shortly.';
  });
