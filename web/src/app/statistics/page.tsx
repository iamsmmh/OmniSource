import { getAnalytics, getAnalyticsRollup } from "@/lib/data";
import { getLangDict } from "@/lib/lang";

interface Window {
  date?: string;
  week?: string;
  month?: string;
  days?: number;
  metrics?: Record<string, number>;
  averages?: Record<string, number>;
}

function WindowTable({ title, rows }: { title: string; rows: Window[] }) {
  const keys = [...new Set(rows.flatMap((r) => Object.keys(r.metrics ?? r.averages ?? {})))].slice(0, 6);
  return (
    <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="border-b border-zinc-100 px-4 py-3 font-bold dark:border-zinc-800">{title}</h2>
      <table className="w-full text-left text-sm">
        <thead className="bg-zinc-50 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
          <tr>
            <th className="px-4 py-2 font-semibold">Period</th>
            {keys.map((k) => (
              <th key={k} className="px-4 py-2 text-right font-semibold">
                {k}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-zinc-100 dark:border-zinc-800">
              <td className="px-4 py-2 font-mono text-xs">{r.date ?? r.week ?? r.month}</td>
              {keys.map((k) => (
                <td key={k} className="px-4 py-2 text-right tabular-nums">
                  {(r.metrics ?? r.averages ?? {})[k] ?? "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {!rows.length && <p className="p-4 text-sm text-zinc-500">No data yet.</p>}
    </div>
  );
}

export default async function StatisticsPage() {
  const { dict } = await getLangDict();
  const analytics = getAnalytics() as { totals?: Record<string, number> };
  const rollup = getAnalyticsRollup() as { daily?: Window[]; weekly?: Window[]; monthly?: Window[] };
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold">{dict.sections.statisticsTitle}</h1>
        <p className="text-zinc-600 dark:text-zinc-400">{dict.sections.statisticsSubtitle}</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {Object.entries(analytics.totals ?? {}).map(([k, v]) => (
          <div key={k} className="rounded-2xl border border-zinc-200 bg-white p-4 text-center dark:border-zinc-800 dark:bg-zinc-900">
            <div className="text-2xl font-extrabold">{v}</div>
            <div className="text-xs text-zinc-500">{k}</div>
          </div>
        ))}
      </div>
      <WindowTable title="Daily (30 days)" rows={rollup.daily ?? []} />
      <WindowTable title="Weekly (12 weeks)" rows={rollup.weekly ?? []} />
      <WindowTable title="Monthly (12 months)" rows={rollup.monthly ?? []} />
    </div>
  );
}
