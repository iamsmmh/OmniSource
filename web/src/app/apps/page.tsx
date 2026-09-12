import AppCard from "@/components/AppCard";
import { getAppsWithIds, getCategories } from "@/lib/data";
import { getLangDict } from "@/lib/lang";

export default async function AppsPage({
  searchParams,
}: {
  searchParams: Promise<{ category?: string; sort?: string }>;
}) {
  const { dict } = await getLangDict();
  const params = await searchParams;
  const category = params.category ?? "";
  const sort = params.sort ?? "name";
  const categories = getCategories();
  let entries = getAppsWithIds();
  if (category) entries = entries.filter((e) => (e.app.category ?? "") === category);
  entries = [...entries].sort((a, b) =>
    sort === "updated"
      ? String(b.app.versionDate ?? "").localeCompare(String(a.app.versionDate ?? ""))
      : a.app.name.localeCompare(b.app.name),
  );
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold">{dict.sections.appsTitle}</h1>
        <p className="text-zinc-600 dark:text-zinc-400">{dict.sections.appsSubtitle}</p>
      </div>
      <form method="get" className="flex flex-wrap gap-2">
        <select
          name="category"
          defaultValue={category}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        >
          <option value="">— {dict.common.category} —</option>
          {categories.map((c) => (
            <option key={c.name} value={c.name}>
              {c.name} ({c.count})
            </option>
          ))}
        </select>
        <select
          name="sort"
          defaultValue={sort}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        >
          <option value="name">A–Z</option>
          <option value="updated">{dict.common.updated}</option>
        </select>
        <button type="submit" className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white dark:bg-zinc-100 dark:text-zinc-900">
          OK
        </button>
      </form>
      <p className="text-sm text-zinc-500">
        {entries.length} {dict.common.apps}
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {entries.map(({ id, app }) => (
          <AppCard key={id} id={id} app={app} />
        ))}
      </div>
      {!entries.length && <p className="text-zinc-500">{dict.common.noResults}</p>}
    </div>
  );
}
