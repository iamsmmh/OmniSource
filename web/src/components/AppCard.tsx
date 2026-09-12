import Link from "next/link";
import type { AltApp } from "@/lib/data";

export function tint(app: AltApp): string {
  const raw = (app.tintColor ?? "FF0000").replace("#", "");
  return /^[0-9A-Fa-f]{6}$/.test(raw) ? `#${raw}` : "#FF0000";
}

export default function AppCard({ id, app }: { id: string; app: AltApp }) {
  return (
    <Link
      href={`/apps/${encodeURIComponent(id)}`}
      className="group flex gap-3 rounded-2xl border border-zinc-200 bg-white p-3 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900"
    >
      {app.iconURL ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={app.iconURL}
          alt=""
          loading="lazy"
          className="h-14 w-14 shrink-0 rounded-xl object-cover"
          style={{ background: tint(app) }}
        />
      ) : (
        <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl text-xl font-bold text-white" style={{ background: tint(app) }}>
          {app.name.slice(0, 1)}
        </span>
      )}
      <span className="min-w-0">
        <span className="block truncate font-semibold text-zinc-900 group-hover:underline dark:text-zinc-100">
          {app.name}
        </span>
        <span className="block truncate text-sm text-zinc-500 dark:text-zinc-400">
          {app.developerName} · v{app.version ?? "?"}
        </span>
        <span className="mt-1 inline-block rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
          {app.category ?? "Utilities"}
        </span>
      </span>
    </Link>
  );
}
