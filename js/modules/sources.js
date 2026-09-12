/*
 * /sources/ — Source Explorer page controller (Phase 4 + 8).
 *
 * Loads feeds/sources.json (the enriched machine contract), joins the live
 * health/reputation roll-ups, and renders filterable, fuzzy-searchable
 * source cards. Everything degrades honestly: the static server-rendered
 * table in the page remains until data arrives, and each card links to a
 * fully static sources/<slug>/ page so the section works with JS disabled.
 */

import { countUp, debounce, esc, fetchJSON, localize, relDays, translate } from './utils.js';
import { highlight, normalize, search } from './search.js';
import { badgeClassFor, cadenceText, daysSince, meaningFor, scoreClass, scoreText, statusOf, STATUSES } from './status.js';

const SOURCE_FIELDS = [
  { get: (s) => s.source, weight: 1.4 },
  { get: (s) => s.publisher, weight: 1.1 },
  { get: (s) => s.id, weight: 1.0 },
  { get: (s) => (s.apps || []).map((a) => a.name + ' ' + a.slug).join(' '), weight: 0.9 },
  { get: (s) => s.sourceURL, weight: 0.6 },
  { get: (s) => s.type, weight: 0.4 },
];

const state = { sources: [], query: '', status: '', sort: 'reputation' };
let grid = null;
let empty = null;

function sortKey(source) {
  switch (state.sort) {
    case 'health':
      return -Number(source.healthScore || 0);
    case 'apps':
      return -Number(source.appCount || 0);
    case 'updated':
      return -(daysSince(source.lastUpdate) === null ? 99999 : daysSince(source.lastUpdate));
    default:
      return -Number(source.score == null ? -1 : source.score);
  }
}

function visibleSources() {
  let items = state.sources;
  if (state.status) items = items.filter((source) => statusOf(source) === state.status);
  if (normalize(state.query)) items = search(state.query, items, SOURCE_FIELDS);
  else items = items.slice().sort((a, b) => sortKey(a) - sortKey(b));
  return items;
}

function card(source) {
  const status = statusOf(source);
  const apps = Number(source.appCount || 0);
  const verified = Number(source.verifiedApps || 0);
  const slug = source.slug ? String(source.slug) : '';
  const nameHtml = highlight(source.source, state.query);
  const maintainer = source.publisher ? String(source.publisher) : '';
  const feed = source.sourceURL ? String(source.sourceURL) : '';
  const feedShort = feed.length > 52 ? feed.slice(0, 49) + '…' : feed;
  return (
    '<article class="source-card panel" data-source="' + esc(slug) + '" data-status="' + esc(status) + '">' +
    '  <header>' +
    '    <h3>' + nameHtml + '</h3>' +
    '    <span class="' + esc(badgeClassFor(status)) + '">' + esc(status) + '</span>' +
    '  </header>' +
    '  <p class="source-sub">' +
    (maintainer
      ? '<span>' + esc(translate('sources.maintainer', 'Maintainer')) + ': <b>' + esc(maintainer) + '</b></span>'
      : '') +
    (feed
      ? ' <a class="source-url" href="' + esc(feed) + '" target="_blank" rel="noopener" title="' + esc(feed) + '">' +
        '<code>' + esc(feedShort) + '</code></a>'
      : '') +
    '  </p>' +
    '  <dl class="source-metrics">' +
    '    <div><dt>' + esc(translate('sources.apps', apps + ' apps', { count: apps }).replace('${count}', apps)) + '</dt>' +
    '      <dd>' + esc(translate('sources.verification', 'Verification')) + ' <b>' + verified + '/' + apps + '</b></dd></div>' +
    '    <div><dt>' + esc(translate('sources.reputation', 'Reputation')) + '</dt>' +
    '      <dd><span class="score-pill ' + esc(scoreClass(source.score)) + '">' + esc(scoreText(source.score)) + '</span></dd></div>' +
    '    <div><dt>' + esc(translate('sources.health', 'Health')) + '</dt>' +
    '      <dd><span class="score-pill ' + esc(scoreClass(source.healthScore)) + '">' + esc(scoreText(source.healthScore)) + '</span></dd></div>' +
    '    <div><dt>' + esc(translate('sources.frequency', 'Update frequency')) + '</dt>' +
    '      <dd>' + esc(cadenceText(source.updateFrequencyDays)) + '</dd></div>' +
    '    <div><dt>' + esc(translate('sources.lastUpdate', 'Last update')) + '</dt>' +
    '      <dd>' + esc(relDays(source.lastUpdate)) + '</dd></div>' +
    '  </dl>' +
    '  <p class="source-note">' + esc(meaningFor(status)) + '</p>' +
    (slug
      ? '  <a class="button small" href="' + esc(slug) + '/">' + esc(translate('sources.open', 'Open source page')) + ' &rarr;</a>'
      : '') +
    '</article>'
  );
}

function render() {
  if (!grid) return;
  const items = visibleSources();
  empty.hidden = items.length > 0;
  const staticBlock = document.getElementById('srcStatic');
  grid.innerHTML = items.length
    ? items.map(card).join('')
    : '<p class="text-muted" role="status">' + esc(translate('sources.noData', 'Source data is still loading.')) + '</p>';
  grid.removeAttribute('aria-busy');
  if (items.length && staticBlock) staticBlock.hidden = true;
  localize(grid);
}

function applyStats(sourcesDoc, healthDoc) {
  const sources = sourcesDoc.sources || [];
  const apps = Number(sourcesDoc.count_apps || 0) ||
    (healthDoc && healthDoc.summary ? Number(healthDoc.summary.apps || 0) : 0);
  const healths = sources.map((s) => Number(s.healthScore || 0)).filter((n) => n > 0);
  const reputations = sources.map((s) => Number(s.score || 0)).filter((n) => n > 0);
  const average = (list) => (list.length ? Math.round(list.reduce((a, b) => a + b, 0) / list.length) : 0);
  const targets = {
    srcStatTotal: sources.length,
    srcStatVerified: Number(sourcesDoc.verifiedApps || apps || 0),
    srcStatHealth: average(healths),
    srcStatReputation: average(reputations),
  };
  for (const id of Object.keys(targets)) {
    const node = document.getElementById(id);
    if (node) countUp(node, targets[id]);
  }
}

function buildStatusOptions(sources) {
  const select = document.getElementById('srcStatus');
  const chips = document.getElementById('srcChips');
  if (!select) return;
  const counts = {};
  for (const source of sources) {
    const status = statusOf(source);
    counts[status] = (counts[status] || 0) + 1;
  }
  const options = ['<option value="">' + esc(translate('sources.allStatuses', 'All statuses')) + ' (' + sources.length + ')</option>'];
  const chipHtml = [];
  for (const status of STATUSES) {
    if (!counts[status]) continue;
    options.push('<option value="' + esc(status) + '">' + esc(status) + ' (' + counts[status] + ')</option>');
    chipHtml.push(
      '<button type="button" class="status-chip ' + esc(badgeClassFor(status)) + '" data-status="' + esc(status) + '" ' +
        'title="' + esc(meaningFor(status)) + '">' + esc(status) + ' <b>' + counts[status] + '</b></button>'
    );
  }
  select.innerHTML = options.join('');
  select.value = state.status || '';
  if (chips) chips.innerHTML = chipHtml.join('');
}

function wire() {
  const filter = document.getElementById('srcFilter');
  const sort = document.getElementById('srcSort');
  const select = document.getElementById('srcStatus');
  const reset = document.getElementById('srcReset');
  if (filter) {
    const onInput = debounce(function () {
      state.query = filter.value || '';
      render();
    }, 120);
    filter.addEventListener('input', onInput);
    filter.addEventListener('search', onInput);
  }
  if (sort) {
    sort.addEventListener('change', function () {
      state.sort = sort.value || 'reputation';
      render();
    });
  }
  if (select) {
    select.addEventListener('change', function () {
      state.status = select.value || '';
      syncChips();
      render();
    });
  }
  const chips = document.getElementById('srcChips');
  if (chips) {
    chips.addEventListener('click', function (event) {
      const chip = event.target.closest ? event.target.closest('[data-status]') : null;
      if (!chip) return;
      state.status = state.status === chip.dataset.status ? '' : chip.dataset.status;
      if (select) select.value = state.status || '';
      syncChips();
      render();
    });
  }
  if (reset) {
    reset.addEventListener('click', function () {
      state.query = '';
      state.status = '';
      if (filter) filter.value = '';
      if (select) select.value = '';
      syncChips();
      render();
    });
  }
}

function syncChips() {
  const chips = document.getElementById('srcChips');
  if (!chips) return;
  for (const chip of chips.querySelectorAll('[data-status]')) {
    const active = chip.dataset.status === state.status;
    chip.setAttribute('aria-pressed', active ? 'true' : 'false');
    chip.classList.toggle('is-active', active);
  }
}

async function init() {
  grid = document.getElementById('srcGrid');
  empty = document.getElementById('srcEmpty');
  if (!grid) return; // not the sources page
  wire();
  const [sourcesDoc, healthDoc] = await Promise.all([
    fetchJSON('feeds/sources.json'),
    fetchJSON('feeds/health.json'),
  ]);
  if (!sourcesDoc || !Array.isArray(sourcesDoc.sources)) return; // static table stays
  state.sources = sourcesDoc.sources;
  buildStatusOptions(state.sources);
  applyStats(sourcesDoc, healthDoc);
  render();
  document.addEventListener('i18n:changed', function () {
    render();
    buildStatusOptions(state.sources);
  });
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
}
