/*
 * Compare module (Phase 7): deep-link parsing and winner marking for
 * /compare/. The heavy lifting (matrix, deltas) stays in
 * src/js/compare-engine.js behind js/site.js; this module owns the URL
 * contract — `?left=&right=` — so both code paths agree on state, and marks
 * per-row winners using the shared trust comparison rule.
 */

import { normalize } from './search.js';

export function readQuery(search) {
  const params = new URLSearchParams(search || (typeof location !== 'undefined' ? location.search : ''));
  return { left: params.get('left') || '', right: params.get('right') || '' };
}

export function writeQuery(left, right) {
  const params = new URLSearchParams();
  if (left) params.set('left', left);
  if (right) params.set('right', right);
  const query = params.toString();
  const url = location.pathname + (query ? '?' + query : '');
  history.replaceState(null, '', url);
}

/** Higher trust wins; ties are marked null so the UI stays honest. */
export function winnerOf(a, b, metric) {
  const left = Number((a && a[metric]) || 0);
  const right = Number((b && b[metric]) || 0);
  if (left === right) return null;
  return left > right ? 'left' : 'right';
}

const METRICS = ['trustScore', 'downloads', 'sizeBytes', 'versionAge'];

/** Mark `.cmp-row` elements that carry data-metric with a winner class. */
export function markWinners() {
  document.querySelectorAll('.cmp-row[data-metric]').forEach(function (row) {
    const metric = normalize(row.getAttribute('data-metric'));
    if (METRICS.indexOf(metric) === -1) return;
    const left = row.querySelector('[data-side="left"]');
    const right = row.querySelector('[data-side="right"]');
    if (!left || !right) return;
    [left, right].forEach(function (node) { node.classList.remove('is-winner'); });
    const winner = winnerOf(
      { v: left.getAttribute('data-value') },
      { v: right.getAttribute('data-value') },
      'v'
    );
    if (!winner) return;
    (winner === 'left' ? left : right).classList.add('is-winner');
  });
}

if (typeof document !== 'undefined') {
  document.addEventListener('compare:rendered', markWinners);
}
