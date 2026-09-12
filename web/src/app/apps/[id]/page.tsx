import Link from "next/link";
import { notFound } from "next/navigation";
import { tint } from "@/components/AppCard";
import { getAppById, getAppsWithIds } from "@/lib/data";
import { getLangDict } from "@/lib/lang";

export function generateStaticParams() {
  return getAppsWithIds().map(({ id }) => ({ id }));
}

export default async function AppDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const app = getAppById(decodeURIComponent(id));
  if (!app) notFound();
  const { dict } = await getLangDict();
  const versions = Array.isArray(app.versions) ? app.versions : [];
  return (
    <div className="space-y-6">
      <Link href="/apps" className="text-sm font-semibold text-red-600 hover:underline">
        ← {dict.sections.appsTitle}
      </Link>
      <div className="flex flex-col gap-5 rounded-3xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900 md:flex-row">
        {app.iconURL ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={app.iconURL} alt="" className="h-28 w-28 rounded-3xl object-cover" style={{ background: tint(app) }} />
        ) : (
          <span className="flex h-28 w-28 items-center justify-center rounded-3xl text-4xl font-bold text-white" style={{ background: tint(app) }}>
            {app.name.slice(0, 1)}
          </span>
        )}
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-extrabold">{app.name}</h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            {app.developerName} · {app.bundleIdentifier}
          </p>
          <div className="mt-2 flex flex-wrap gap-2 text-sm">
            <span className="rounded-full bg-zinc-100 px-3 py-1 dark:bg-zinc-800">
              {dict.common.version} {app.version} · {app.versionDate}
            </span>
            <span className="rounded-full bg-zinc-100 px-3 py-1 dark:bg-zinc-800">{app.category}</span>
            {typeof app.size === "number" && app.size > 0 && (
              <span className="rounded-full bg-zinc-100 px-3 py-1 dark:bg-zinc-800">
                {(app.size / 1048576).toFixed(1)} MB
              </span>
            )}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {app.downloadURL && (
              <a href={app.downloadURL} className="rounded-xl bg-red-600 px-5 py-2.5 font-semibold text-white hover:bg-red-700">
                ⬇ {dict.common.download} (.ipa)
              </a>
            )}
            <a
              href={`https://iamsmmh.github.io/OmniSource/feeds/${encodeURIComponent(app.bundleIdentifier)}.json`}
              className="rounded-xl border border-zinc-300 px-5 py-2.5 font-semibold hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800"
            >
              {dict.home.addSource}
            </a>
          </div>
        </div>
      </div>
      {app.localizedDescription && (
        <div className="prose-omni rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <p className="whitespace-pre-wrap text-[15px]">{app.localizedDescription}</p>
        </div>
      )}
      {!!versions.length && (
        <div className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="mb-3 font-bold">
            {dict.common.version}s ({versions.length})
          </h2>
          <ul className="space-y-2 text-sm">
            {versions.slice(0, 10).map((v, i) => {
              const ver = v as Record<string, unknown>;
              return (
                <li key={i} className="flex flex-wrap items-center gap-2 border-b border-zinc-100 pb-2 dark:border-zinc-800">
                  <span className="font-mono font-semibold">{String(ver.version ?? "?")}</span>
                  <span className="text-zinc-500">{String(ver.date ?? "")}</span>
                  {typeof ver.downloadURL === "string" && (
                    <a href={ver.downloadURL} className="ml-auto font-semibold text-red-600 hover:underline">
                      {dict.common.download}
                    </a>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
