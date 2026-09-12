import { createHash } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";
import {
  getAnalytics,
  getAnalyticsRollup,
  getAppById,
  getAppsWithIds,
  getSecurity,
  getSourceById,
  getSources,
  getStatus,
  type AltApp,
} from "@/lib/data";
import { scoreApp } from "@/lib/search";

export const dynamic = "force-dynamic";

const API_VERSION = "3.0.0";
const MAX_PER_PAGE = 200;

function envelope(data: unknown, pagination?: Record<string, number>) {
  const body: Record<string, unknown> = { apiVersion: API_VERSION, schemaVersion: 3, data };
  if (pagination) body.pagination = pagination;
  return body;
}

function etag(payload: string): string {
  return `W/"${createHash("sha256").update(payload).digest("hex").slice(0, 32)}"`;
}

function json(request: NextRequest, body: unknown, status = 200): NextResponse {
  const payload = JSON.stringify(body);
  const tag = etag(payload);
  if (request.headers.get("if-none-match") === tag) {
    return new NextResponse(null, { status: 304, headers: { ETag: tag } });
  }
  return new NextResponse(payload, {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      ETag: tag,
      // Next.js compresses (gzip/brotli) automatically; CDN caches for 5 min.
      "Cache-Control": "public, s-maxage=300, stale-while-revalidate=3600",
    },
  });
}

function pageOf<T>(items: T[], request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const perPage = Math.max(1, Math.min(MAX_PER_PAGE, Number(params.get("per_page") ?? 50) || 50));
  const total = items.length;
  const pages = Math.max(1, Math.ceil(total / perPage));
  const page = Math.max(1, Math.min(pages, Number(params.get("page") ?? 1) || 1));
  return {
    page,
    per_page: perPage,
    total,
    pages,
    items: items.slice((page - 1) * perPage, page * perPage),
  };
}

function slim(app: AltApp, id: string) {
  return {
    id,
    name: app.name,
    bundleIdentifier: app.bundleIdentifier,
    developerName: app.developerName,
    category: app.category,
    version: app.version,
    versionDate: app.versionDate,
    iconURL: app.iconURL,
    downloadURL: app.downloadURL,
    size: app.size,
  };
}

function sortApps(entries: Array<{ id: string; app: AltApp }>, sort: string) {
  const desc = sort.startsWith("-");
  const field = (desc ? sort.slice(1) : sort) as keyof AltApp;
  const allowed: Array<keyof AltApp> = ["name", "version", "versionDate", "category", "developerName", "size"];
  const key = allowed.includes(field) ? field : "name";
  return [...entries].sort((a, b) => {
    const av = String(a.app[key] ?? "");
    const bv = String(b.app[key] ?? "");
    return desc ? bv.localeCompare(av) : av.localeCompare(bv);
  });
}

export async function GET(request: NextRequest, { params }: { params: Promise<{ route?: string[] }> }) {
  const segments = (await params).route ?? [];
  const [resource, id] = segments;
  const query = request.nextUrl.searchParams;

  if (!resource || resource === "index") {
    return json(request, {
      apiVersion: API_VERSION,
      schemaVersion: 3,
      endpoints: [
        "/api/v3/apps",
        "/api/v3/apps/{id}",
        "/api/v3/sources",
        "/api/v3/sources/{id}",
        "/api/v3/search",
        "/api/v3/status",
        "/api/v3/security",
        "/api/v3/analytics",
        "/api/v3/releases",
      ],
    });
  }

  if (resource === "apps") {
    const entries = getAppsWithIds();
    if (id) {
      const app = getAppById(decodeURIComponent(id));
      if (!app) return json(request, { error: "not_found" }, 404);
      return json(request, envelope({ id: decodeURIComponent(id), ...app }));
    }
    let filtered = entries;
    const category = query.get("category");
    const developer = query.get("developer");
    const q = query.get("q") ?? query.get("query");
    if (category) filtered = filtered.filter((e) => (e.app.category ?? "") === category);
    if (developer) filtered = filtered.filter((e) => (e.app.developerName ?? "").toLowerCase().includes(developer.toLowerCase()));
    if (q) {
      filtered = filtered
        .map((e) => ({ ...e, _score: scoreApp(e.app, q) }))
        .filter((e) => e._score > 0)
        .sort((a, b) => b._score - a._score);
    } else {
      filtered = sortApps(filtered, query.get("sort") ?? "name");
    }
    const p = pageOf(filtered, request);
    const pagination = { page: p.page, per_page: p.per_page, total: p.total, pages: p.pages };
    return json(request, envelope(p.items.map((e) => slim(e.app, e.id)), pagination));
  }

  if (resource === "sources") {
    if (id) {
      const source = getSourceById(decodeURIComponent(id));
      if (!source) return json(request, { error: "not_found" }, 404);
      return json(request, envelope(source));
    }
    let sources = getSources();
    const status = query.get("status");
    if (status) sources = sources.filter((s) => (s.status ?? "").toLowerCase() === status.toLowerCase());
    const sort = query.get("sort") ?? "-score";
    sources = [...sources].sort((a, b) =>
      sort === "-score" ? (b.score ?? 0) - (a.score ?? 0) : (a.source ?? "").localeCompare(b.source ?? ""),
    );
    const p = pageOf(sources, request);
    return json(
      request,
      envelope(p.items, { page: p.page, per_page: p.per_page, total: p.total, pages: p.pages }),
    );
  }

  if (resource === "status") return json(request, envelope(getStatus()));
  if (resource === "security") return json(request, envelope(getSecurity()));
  if (resource === "analytics") {
    return json(request, envelope({ live: getAnalytics(), rollup: getAnalyticsRollup() }));
  }

  if (resource === "search") {
    const q = query.get("q") ?? query.get("query") ?? "";
    const entries = getAppsWithIds();
    const scored = entries
      .map((e) => ({ ...e, _score: q ? scoreApp(e.app, q) : 1 }))
      .filter((e) => e._score > 0)
      .sort((a, b) => b._score - a._score);
    const p = pageOf(scored, request);
    return json(
      request,
      envelope(
        p.items.map((e) => ({ ...slim(e.app, e.id), _score: e._score })),
        { page: p.page, per_page: p.per_page, total: p.total, pages: p.pages },
      ),
    );
  }

  if (resource === "releases") {
    const timeline = getAppsWithIds().flatMap(({ id: appId, app }) =>
      (Array.isArray(app.versions) ? app.versions : []).slice(0, 5).map((v) => {
        const ver = v as Record<string, unknown>;
        return {
          app: appId,
          version: ver.version,
          date: ver.date,
          downloadURL: ver.downloadURL,
          size: ver.size,
        };
      }),
    );
    timeline.sort((a, b) => String(b.date ?? "").localeCompare(String(a.date ?? "")));
    const p = pageOf(timeline, request);
    return json(
      request,
      envelope(p.items, { page: p.page, per_page: p.per_page, total: p.total, pages: p.pages }),
    );
  }

  return json(request, { error: "not_found", endpoints: "/api/v3" }, 404);
}
