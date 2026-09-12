import { getStatus } from "@/lib/data";
import { getLangDict } from "@/lib/lang";

interface SourceState {
  id?: string;
  slug?: string;
  status?: string;
  latencyMs?: number | null;
  lastProbe?: string;
}

const DOT: Record<string, string> = {
  healthy: "bg-emerald-500",
  online: "bg-emerald-500",
  degraded: "bg-amber-500",
  unavailable: "bg-red-500",
  offline: "bg-red-500",
  unknown: "bg-zinc-400",
};

export default async function StatusPage() {
  const { dict } = await getLangDict();
  const doc = getStatus() as {
    overall?: string;
    generatedAt?: string;
    totals?: Record<string, number>;
    pipeline?: Record<string, unknown>;
    sources?: SourceState[];
  };
  const sources = Array.isArray(doc.sources) ? doc.sources : [];
  const totals = doc.totals ?? {};
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold">{dict.sections.statusTitle}</h1>
        <p className="text-zinc-600 dark:text-zinc-400">{dict.sections.statusSubtitle}</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-4">
        {Object.entries(totals).map(([k, v]) => (
          <div key={k} className="rounded-2xl border border-zinc-200 bg-white p-4 text-center dark:border-zinc-800 dark:bg-zinc-900">
            <div className="text-2xl font-extrabold">{v}</div>
            <div className="text-xs uppercase tracking-wide text-zinc-500">{k}</div>
          </div>
        ))}
      </div>
      <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <table className="w-full text-left text-sm">
          <thead className="bg-zinc-50 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
            <tr>
              <th className="px-4 py-2 font-semibold">{dict.common.source}</th>
              <th className="px-4 py-2 font-semibold">{dict.nav.status}</th>
              <th className="px-4 py-2 font-semibold">Latency</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s, i) => (
              <tr key={s.id ?? s.slug ?? i} className="border-t border-zinc-100 dark:border-zinc-800">
                <td className="px-4 py-2 font-medium">{s.id ?? s.slug}</td>
                <td className="px-4 py-2">
                  <span className="inline-flex items-center gap-1.5">
                    <span className={`h-2.5 w-2.5 rounded-full ${DOT[s.status ?? "unknown"] ?? DOT.unknown}`} />
                    {s.status ?? "unknown"}
                  </span>
                </td>
                <td className="px-4 py-2 text-zinc-500">{s.latencyMs == null ? "—" : `${s.latencyMs} ms`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
