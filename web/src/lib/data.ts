// Typed access to the synced pipeline snapshots (see scripts/sync-data.mjs).
// Server-only: pages import these helpers; the JSON is bundled at build.
import analyticsDoc from "../data/analytics.json";
import analyticsRollup from "../data/analytics_rollup.json";
import appsDoc from "../data/apps.json";
import canonicalDoc from "../data/canonical_apps.json";
import catalogDoc from "../data/catalog.json";
import collectionsDoc from "../data/collections.json";
import discoveryDoc from "../data/discovery.json";
import reputationDoc from "../data/reputation.json";
import searchIndex from "../data/search-index.json";
import securityDoc from "../data/security.json";
import sourceReputation from "../data/source_reputation.json";
import statusDoc from "../data/status.json";
import trendingDoc from "../data/trending.json";
import sourcesDoc from "../data/sources.json";

export interface AltApp {
  name: string;
  bundleIdentifier: string;
  developerName: string;
  subtitle?: string;
  localizedDescription?: string;
  iconURL?: string;
  tintColor?: string;
  category?: string;
  version?: string;
  versionDate?: string;
  versionDescription?: string;
  downloadURL?: string;
  size?: number;
  versions?: Array<Record<string, unknown>>;
  screenshotURLs?: string[];
  slug?: string;
  id?: string;
}

export interface SourceEntry {
  id: string;
  source: string;
  slug?: string;
  page?: string;
  homepage?: string;
  sourceURL?: string;
  publisher?: string;
  apps?: string[];
  appSlugs?: string[];
  appCount?: number;
  score?: number;
  level?: string;
  status?: string;
  healthScore?: number;
  lastUpdate?: string;
}

export interface CollectionEntry {
  slug: string;
  title: string;
  subtitle?: string;
  description?: string;
  appCount?: number;
  appSlugs?: string[];
  apps?: AltApp[];
}

function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

export function appId(app: AltApp, index = 0): string {
  const base = app.slug || app.id || app.bundleIdentifier || `app-${index}`;
  return base;
}

/** Stable unique IDs across the catalog (suffixed on bundle collision). */
export function catalogIds(apps: AltApp[]): string[] {
  const seen = new Map<string, number>();
  return apps.map((app, i) => {
    const base = appId(app, i);
    const n = (seen.get(base) ?? 0) + 1;
    seen.set(base, n);
    return n === 1 ? base : `${base}-${n}`;
  });
}

export function getApps(): AltApp[] {
  return asArray<AltApp>((appsDoc as { apps?: unknown }).apps);
}

export function getAppsWithIds(): Array<{ id: string; app: AltApp }> {
  const apps = getApps();
  const ids = catalogIds(apps);
  return apps.map((app, i) => ({ id: ids[i], app }));
}

export function getAppById(id: string): AltApp | undefined {
  return getAppsWithIds().find((e) => e.id === id)?.app;
}

export function getSources(): SourceEntry[] {
  return asArray<SourceEntry>((sourcesDoc as { sources?: unknown }).sources);
}

export function getSourceById(id: string): SourceEntry | undefined {
  return getSources().find((s) => s.id === id || s.slug === id);
}

export function getCollections(): CollectionEntry[] {
  return asArray<CollectionEntry>((collectionsDoc as { collections?: unknown }).collections);
}

export function getCategories(): Array<{ name: string; count: number }> {
  const counts = new Map<string, number>();
  for (const app of getApps()) {
    const name = app.category?.trim() || "Utilities";
    counts.set(name, (counts.get(name) ?? 0) + 1);
  }
  return [...counts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
}

export function getTrending(): Record<string, unknown> {
  return trendingDoc as Record<string, unknown>;
}

export function getStatus(): Record<string, unknown> {
  return statusDoc as Record<string, unknown>;
}

export function getSecurity(): Record<string, unknown> {
  return securityDoc as Record<string, unknown>;
}

export function getAnalytics(): Record<string, unknown> {
  return analyticsDoc as Record<string, unknown>;
}

export function getAnalyticsRollup(): Record<string, unknown> {
  return analyticsRollup as Record<string, unknown>;
}

export function getDiscovery(): Record<string, unknown> {
  return discoveryDoc as Record<string, unknown>;
}

export function getSearchIndex(): Record<string, unknown> {
  return searchIndex as Record<string, unknown>;
}

export function getReputation(): Record<string, unknown> {
  return reputationDoc as Record<string, unknown>;
}

export function getSourceReputation(): Record<string, unknown> {
  return sourceReputation as Record<string, unknown>;
}

export function getCanonical(): Record<string, unknown> {
  return canonicalDoc as Record<string, unknown>;
}

export function getCatalog(): Record<string, unknown> {
  return catalogDoc as Record<string, unknown>;
}

export function getGeneratedAt(): string {
  const docs = [discoveryDoc, statusDoc, trendingDoc] as Array<Record<string, unknown>>;
  for (const doc of docs) {
    if (typeof doc.generatedAt === "string" && doc.generatedAt) return doc.generatedAt;
  }
  return "";
}
