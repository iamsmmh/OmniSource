import AppCard from "@/components/AppCard";
import { getAppsWithIds, getTrending } from "@/lib/data";
import { getLangDict } from "@/lib/lang";

interface TrendEntry {
  slug?: string;
  name?: string;
  score?: number;
}

export default async function TrendingPage() {
  const { dict } = await getLangDict();
  const doc = getTrending() as { trending?: TrendEntry[]; rising?: TrendEntry[]; recentlyUpdated?: TrendEntry[] };
  const entries = getAppsWithIds();
  const byName = new Map(entries.map((e) => [e.app.name.toLowerCase(), e]));
  const byBundle = new Map(entries.map((e) => [e.app.bundleIdentifier.toLowerCase(), e]));

  function resolve(list: TrendEntry[] = []) {
    return list
      .map((t) => {
        const key = (t.slug ?? t.name ?? "").toLowerCase();
        return byBundle.get(key) ?? byName.get((t.name ?? "").toLowerCase());
      })
      .filter((e): e is NonNullable<typeof e> => Boolean(e));
  }

  const groups: Array<{ title: string; items: ReturnType<typeof resolve> }> = [
    { title: "🔥 Trending", items: resolve(doc.trending) },
    { title: "📈 Rising", items: resolve(doc.rising) },
    { title: "🆕 Recently updated", items: resolve(doc.recentlyUpdated) },
  ];
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-extrabold">{dict.sections.trendingTitle}</h1>
        <p className="text-zinc-600 dark:text-zinc-400">{dict.sections.trendingSubtitle}</p>
      </div>
      {groups.map((g) => (
        <section key={g.title}>
          <h2 className="mb-3 text-lg font-bold">{g.title}</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {g.items.map(({ id, app }) => (
              <AppCard key={`${g.title}-${id}`} id={id} app={app} />
            ))}
          </div>
          {!g.items.length && <p className="text-sm text-zinc-500">{dict.common.noResults}</p>}
        </section>
      ))}
    </div>
  );
}
