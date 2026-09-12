/*
 * Fuzzy search core (modernization Phase 8), shared by the /sources/
 * explorer and the instant palette. Pure functions over plain objects —
 * no DOM, no globals — so it is unit-testable and cheap at thousands of
 * documents (scoring is bigram + bounded edit distance, both O(len)).
 */

import { esc } from './utils.js';

/** Normalize for comparison: caseless, accentless, punctuation-light. */
export function normalize(value) {
  return String(value === null || value === undefined ? '' : value)
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9. ]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/** Character bigrams of a normalized string (Dice coefficient input). */
export function bigrams(text) {
  const pairs = new Map();
  const value = text.length === 1 ? text + ' ' : text;
  for (let i = 0; i < value.length - 1; i += 1) {
    const pair = value.slice(i, i + 2);
    pairs.set(pair, (pairs.get(pair) || 0) + 1);
  }
  return pairs;
}

/** Dice similarity of two strings over shared bigrams, 0..1. */
export function dice(text, other) {
  if (!text || !other) return 0;
  if (text === other) return 1;
  const left = bigrams(text);
  const right = bigrams(other);
  let overlap = 0;
  let total = 0;
  for (const [pair, count] of left) {
    total += count;
    if (right.has(pair)) overlap += Math.min(count, right.get(pair));
  }
  for (const count of right.values()) total += count;
  if (!total) return 0;
  return (2 * overlap) / total;
}

/** Levenshtein capped at `cap` (early exit keeps long fields cheap). */
export function editDistance(a, b, cap) {
  if (a === b) return 0;
  if (Math.abs(a.length - b.length) > cap) return cap + 1;
  let previous = new Array(b.length + 1);
  let current = new Array(b.length + 1);
  for (let j = 0; j <= b.length; j += 1) previous[j] = j;
  for (let i = 1; i <= a.length; i += 1) {
    current[0] = i;
    let rowMin = current[0];
    for (let j = 1; j <= b.length; j += 1) {
      const cost = a.charCodeAt(i - 1) === b.charCodeAt(j - 1) ? 0 : 1;
      current[j] = Math.min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost);
      if (current[j] < rowMin) rowMin = current[j];
    }
    if (rowMin > cap) return cap + 1;
    const swap = previous;
    previous = current;
    current = swap;
  }
  return previous[b.length];
}

/**
 * Match one query term against one field value.
 * Returns {score, exact} or null. Weighted by field (caller), ranked:
 * exact > prefix > word-prefix > substring > typo-tolerant fuzzy.
 */
export function matchField(term, value, options) {
  const field = normalize(value);
  if (!field || !term) return null;
  const boost = (options && options.weight) || 1;
  if (field === term) return { score: 120 * boost, exact: true };
  if (field.startsWith(term)) return { score: 90 * boost, exact: false };
  const words = field.split(' ');
  if (words.indexOf(term) !== -1) return { score: 85 * boost, exact: false };
  if (words.some(function (w) { return w.startsWith(term); })) return { score: 70 * boost, exact: false };
  const index = field.indexOf(term);
  if (index !== -1) return { score: (55 + Math.min(index, 20) * -0.5) * boost, exact: false };
  // Typo tolerance: budget grows with term length (<=1 error at 4 chars,
  // 2 at 7+, never more) so short queries stay strict.
  const budget = term.length >= 7 ? 2 : term.length >= 4 ? 1 : 0;
  if (budget > 0) {
    let best = Infinity;
    for (const word of words) {
      if (Math.abs(word.length - term.length) > budget) continue;
      const distance = editDistance(term, word, budget);
      if (distance < best) best = distance;
      if (best === 0) break;
    }
    if (best <= budget) {
      const diceScore = dice(term, field.slice(0, Math.max(field.length, term.length)));
      return { score: (40 - best * 10 + diceScore * 25) * boost, exact: false };
    }
  }
  return null;
}

/**
 * Score `item`'s `fields` (array of {get, weight}) against `query`.
 * Multi-term queries are conjunctive: every term must match at least one
 * field. Returns the summed score, or 0 for a non-match.
 */
export function scoreItem(query, item, fields) {
  const terms = normalize(query).split(' ').filter(Boolean);
  if (!terms.length) return 1;
  let total = 0;
  for (const term of terms) {
    let best = null;
    for (const field of fields) {
      const hit = matchField(term, field.get(item), { weight: field.weight });
      if (hit && (!best || hit.score > best.score)) best = hit;
    }
    if (!best) return 0;
    total += best.score;
  }
  return Math.round(total);
}

/**
 * Rank `items` by fuzzy relevance for `query`; stable ties keep original
 * order. Empty query returns a copy untouched (callers pre-sort by their
 * own key).
 */
export function search(query, items, fields) {
  if (!normalize(query)) return items.slice();
  const scored = [];
  for (let i = 0; i < items.length; i += 1) {
    const score = scoreItem(query, items[i], fields);
    if (score > 0) scored.push({ item: items[i], score: score, index: i });
  }
  scored.sort(function (a, b) {
    return b.score - a.score || a.index - b.index;
  });
  return scored.map(function (entry) {
    return entry.item;
  });
}

/** Highlight hits as escaped HTML with `<mark>` around matched words. */
export function highlight(text, query) {
  const value = String(text === null || text === undefined ? '' : text);
  const terms = normalize(query).split(' ').filter(Boolean);
  if (!terms.length) return esc(value);
  const pattern = new RegExp('([\\p{L}\\p{N}.\\-]+)', 'giu');
  return value.replace(pattern, function (word) {
    const clean = normalize(word);
    for (const term of terms) {
      if (clean === term || clean.startsWith(term) || dice(term, clean) > 0.6) {
        return '<mark>' + esc(word) + '</mark>';
      }
    }
    return esc(word);
  });
}
