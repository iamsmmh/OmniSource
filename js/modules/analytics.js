/*
 * Analytics module (Phase 7): progressive enhancement for /analytics/.
 * Renders the 30-day history sparklines from feeds/analytics.json without
 * touching the legacy renderers — it only fills elements that are empty, so
 * js/site.js (if present) always wins and nothing double-renders.
 */

import { esc, fetchJSON, localize, translate } from './utils.js';

const SPARK = 'spark';

function sparkline(values, width, height) {
  const numbers = values.map(Number).filter(function (n) { return isFinite(n); });
  if (numbers.length < 2) return '';
  const max = Math.max.apply(null, numbers);
  const min = Math.min.apply(null, numbers);
  const span = max - min || 1;
  const step = width / (numbers.length - 1);
  const points = numbers
    .map(function (value, index) {
      const x = (index * step).toFixed(1);
      const y = (height - ((value - min) / span) * height).toFixed(1);
      return x + ',' + y;
    })
    .join(' ');
  return (
    '<svg class="' + SPARK + '" viewBox="0 0 ' + width + ' ' + height + '" role="img" ' +
    'aria-label="' + esc(translate('analytics.trend', '30-day trend')) + '" preserveAspectRatio="none">' +
    '<polyline points="' + points + '" fill="none" stroke="currentColor" stroke-width="1.5" ' +
    'vector-effect="non-scaling-stroke"/></svg>'
  );
}

function topBars(entries, label) {
  const rows = (entries || []).slice(0, 8);
  if (!rows.length) return '';
  const max = Math.max.apply(null, rows.map(function (row) { return Number(row.count || row.apps) || 0; })) || 1;
  return rows
    .map(function (row) {
      const name = row.name || row.category || row.slug || '—';
      const count = Number(row.count || row.apps) || 0;
      const width = Math.max(4, Math.round((count / max) * 100));
      return (
        '<li class="bar-row"><span class="bar-name">' + esc(name) + '</span>' +
        '<span class="bar-track" aria-hidden="true"><i style="width:' + width + '%"></i></span>' +
        '<b class="num">' + count + '</b></li>'
      );
    })
    .map(function (html, index) {
      return '<div class="bar-block"><h4>' + esc(index === 0 ? label : '') + '</h4><ul>' + html + '</ul></div>';
    })
    .join('');
}

async function init() {
  const doc = await fetchJSON('feeds/analytics.json');
  if (!doc || !doc.totals) return;
  const history = Array.isArray(doc.history) ? doc.history : [];
  const targets = [
    { id: 'anAppsSpark', pick: function (entry) { return (entry.totals || {}).apps; } },
    { id: 'anHealthSpark', pick: function (entry) { return (entry.health || {}).healthyPct; } },
  ];
  for (const target of targets) {
    const node = document.getElementById(target.id);
    if (!node || node.children.length) continue;
    node.innerHTML = sparkline(history.map(target.pick), 220, 44);
    node.setAttribute('title', translate('analytics.days', '${count} days').replace('${count}', history.length));
  }
  const categories = document.getElementById('anTopCategories');
  if (categories && !categories.children.length) {
    categories.innerHTML = topBars(doc.categories || doc.topCategories, translate('analytics.categories', 'Categories'));
  }
  const statuses = document.getElementById('anStatusMix');
  if (statuses && !statuses.children.length) {
    statuses.innerHTML = topBars(doc.statuses || doc.provenance, translate('analytics.provenance', 'Provenance'));
  }
  localize(document.getElementById('main') || document.body);
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
}
