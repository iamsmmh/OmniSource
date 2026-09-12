/*
 * Source health & reputation presentation (Phase 5 of the modernization).
 *
 * One place maps the six reputation statuses onto the design-system badge
 * classes, so /sources/, /status/ and the generated pages can never disagree
 * about what "Warning" looks like. The `level` legacy field (TRUSTED /
 * RELIABLE / …) is kept for old consumers and only used as a fallback.
 */

export const STATUSES = Object.freeze([
  'Verified',
  'Community Verified',
  'Maintained',
  'Warning',
  'Inactive',
  'Deprecated',
]);

/** Badge class from components.css for each status. */
export const STATUS_BADGE = Object.freeze({
  Verified: 'badge verified',
  'Community Verified': 'badge community',
  Maintained: 'badge blue',
  Warning: 'badge warn',
  Inactive: 'badge neutral',
  Deprecated: 'badge deprecated',
});

/** Short human blurb per status (English fallback; i18n-aware labels come
 *  from the locales via translate() when a key is provided). */
export const STATUS_MEANING = Object.freeze({
  Verified: 'Valid feed, probed reachable, updated recently.',
  'Community Verified': 'Healthy and trusted by the community, not fully verified.',
  Maintained: 'Working source with no strong trust signals yet.',
  Warning: 'Something is broken: invalid entries, dead links or probes failing.',
  Inactive: 'No release activity in the last year.',
  Deprecated: 'Archived or every app it publishes is inactive.',
});

export function badgeClassFor(status) {
  return STATUS_BADGE[status] || 'badge neutral';
}

export function meaningFor(status) {
  return STATUS_MEANING[status] || '';
}

/** Reputation status with a legacy-level fallback for pre-v2 documents. */
export function statusOf(source) {
  if (!source) return 'Maintained';
  if (source.status && STATUS_BADGE[source.status]) return source.status;
  switch (source.level) {
    case 'TRUSTED':
      return 'Verified';
    case 'RELIABLE':
      return 'Community Verified';
    case 'AVERAGE':
      return 'Maintained';
    case 'EXPERIMENTAL':
      return 'Warning';
    default:
      return 'Maintained';
  }
}

/** 0-100 as a safe integer string; anything unusable renders as an em dash. */
export function scoreText(value) {
  const number = Number(value);
  if (!isFinite(number)) return '—';
  return Math.round(number) + '/100';
}

export function scoreClass(value) {
  const number = Number(value);
  if (!isFinite(number)) return '';
  if (number >= 85) return 'is-high';
  if (number >= 70) return 'is-mid';
  if (number >= 40) return 'is-low';
  return 'is-bad';
}

/** Days since `iso` date (UTC-safe), or null when there is no date. */
export function daysSince(iso) {
  if (!iso) return null;
  const then = Date.parse(iso.length === 10 ? iso + 'T00:00:00Z' : iso);
  if (isNaN(then)) return null;
  return Math.max(0, Math.round((Date.now() - then) / 86400000));
}

export function cadenceText(days) {
  const value = Number(days);
  if (!isFinite(value)) return '—';
  if (value < 1) return '<1 day';
  if (value < 45) return Math.round(value) + ' days';
  return (value / 30.44).toFixed(1) + ' months';
}
