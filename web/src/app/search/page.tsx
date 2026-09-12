import AppCard from "@/components/AppCard";
import SearchBox from "@/components/SearchBox";
import { getAppsWithIds, getCategories } from "@/lib/data";
import { searchApps } from "@/lib/search";
import { getLangDict } from "@/lib/lang";

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; category?: string; sort?: "relevance" | "name" | "updated" }>;
}) {
  const { dict } = await getLangDict();
  const params = await searchParams;
  const q = params.q ?? "";
  const category = params.category ?? "";
  const sort = params.sort ?? "relevance";
  const entries = getAppsWithIds();
  const byName = new Map(entries.map((e) => [e.app, e.id]));
  const result = searchApps(
    entries.map((e) => e.app),
    q,
    { category, sort, limit: 48 },
  );
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold">{dict.sections.searchTitle}</h1>
        <p className="text-zinc-600 dark:text-zinc-400">{dict.sections.searchSubtitle}</p>
      </div>
      <SearchBox placeholder={dict.sections.searchPlaceholder} initial={q} />
      <form method="get" className="flex flex-wrap gap-2">
        <input type="hidden" name="q" value={q} />
        <select
          name="category"
          defaultValue={category}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        >
          <option value="">— {dict.common.category} —</option>
          {getCategories().map((c) => (
            <option key={c.name} value={c.name}>
              {c.name}
            </option>
          ))}
        </select>
        <select
          name="sort"
          defaultValue={sort}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        >
          <option value="relevance">★ Relevance</option>
          <option value="name">A–Z</option>
          <option value="updated">{dict.common.updated}</option>
        </select>
        <button type="submit" className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white dark:bg-zinc-100 dark:text-zinc-900">
          OK
        </button>
      </form>
      <p className="text-sm text-zinc-500">
        {result.total} {dict.common.apps}
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {result.results.map(({ app, score }) => (
          <div key={byName.get(app)} className="relative">
            {q && (
              <span className="absolute -top-2 right-2 z-10 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800 dark:bg-amber-900 dark:text-amber-200">
                {score.toFixed(1)}
              </span>
            )}
            <AppCard id={byName.get(app) ?? app.bundleIdentifier} app={app} />
          </div>
        ))}
      </div>
      {!result.results.length && <p className="text-zinc-500">{dict.common.noResults}</p>}
    </div>
  );
}
