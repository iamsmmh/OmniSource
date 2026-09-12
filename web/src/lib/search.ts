// Client-side fuzzy search — the TypeScript twin of src/omnisource/search.py
// (same weights, same AND semantics, same short-token guard).
import type { AltApp } from "./data";

const WEIGHTS: Array<[keyof AltApp | "tags", number]> = [
  ["name", 5],
  ["bundleIdentifier", 4],
  ["developerName", 3],
  ["category", 2],
  ["subtitle", 1.5],
  ["localizedDescription", 1],
];

const THRESHOLD = 0.55;

export function tokenize(text: string): string[] {
  return text.toLowerCase().match(/[a-z0-9]+/g) ?? [];
}

function bigrams(s: string): Set<string> {
  const out = new Set<string>();
  for (let i = 0; i < s.length - 1; i++) out.add(s.slice(i, i + 2));
  return out;
}

/** Dice coefficient over character bigrams (fast Jaccard-style similarity). */
function dice(a: string, b: string): number {
  if (!a || !b) return 0;
  const A = bigrams(a);
  const B = bigrams(b);
  if (!A.size || !B.size) return 0;
  let hit = 0;
  for (const g of A) if (B.has(g)) hit++;
  return (2 * hit) / (A.size + B.size);
}

export function fuzzyScore(query: string, text: string): number {
  const q = query.trim().toLowerCase();
  const t = text.trim().toLowerCase();
  if (!q || !t) return 0;
  if (q === t) return 1;
  if (t.startsWith(q)) return 0.95;
  if (t.includes(q)) return 0.85;
  if (q.length <= 4) return 0;
  const tokens = tokenize(t);
  let best = dice(q, t);
  for (const tok of tokens) best = Math.max(best, dice(q, tok));
  return best;
}

function fieldText(app: AltApp, field: keyof AltApp | "tags"): string {
  const v = app[field as keyof AltApp];
  if (Array.isArray(v)) return v.map(String).join(" ");
  return String(v ?? "");
}

export function scoreApp(app: AltApp, query: string): number {
  const tokens = tokenize(query);
  if (!tokens.length) return 0;
  let total = 0;
  for (const tok of tokens) {
    let best = 0;
    for (const [field, w] of WEIGHTS) {
      const s = fuzzyScore(tok, fieldText(app, field));
      if (s >= THRESHOLD) best = Math.max(best, s * w);
    }
    if (!best) return 0;
    total += best;
  }
  return Math.round((total / tokens.length) * 10000) / 10000;
}

export interface SearchOptions {
  category?: string;
  developer?: string;
  sort?: "relevance" | "name" | "updated" | "version";
  limit?: number;
  offset?: number;
}

export function searchApps(apps: AltApp[], query: string, opts: SearchOptions = {}) {
  const { category = "", developer = "", sort = "relevance", limit = 25, offset = 0 } = opts;
  const q = query.trim();
  const filtered = apps.filter((app) => {
    if (category && (app.category ?? "").toLowerCase() !== category.toLowerCase()) return false;
    if (developer && !(app.developerName ?? "").toLowerCase().includes(developer.toLowerCase())) return false;
    return true;
  });
  const scored = filtered
    .map((app) => ({ app, score: q ? scoreApp(app, q) : 1 }))
    .filter((h) => h.score >= (q ? THRESHOLD : 0));
  if (sort === "name") scored.sort((a, b) => a.app.name.localeCompare(b.app.name));
  else if (sort === "updated") scored.sort((a, b) => String(b.app.versionDate ?? "").localeCompare(String(a.app.versionDate ?? "")));
  else if (sort === "version") scored.sort((a, b) => String(b.app.version ?? "").localeCompare(String(a.app.version ?? "")));
  else scored.sort((a, b) => b.score - a.score);
  const total = scored.length;
  return { total, results: scored.slice(offset, offset + limit) };
}
