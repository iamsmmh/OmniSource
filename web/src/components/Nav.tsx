import Link from "next/link";
import type { Dictionary } from "@/i18n/dictionaries";
import LanguageSwitcher from "./LanguageSwitcher";

const LINKS: Array<{ href: string; key: keyof Dictionary["nav"] }> = [
  { href: "/", key: "home" },
  { href: "/apps", key: "apps" },
  { href: "/sources", key: "sources" },
  { href: "/collections", key: "collections" },
  { href: "/categories", key: "categories" },
  { href: "/developers", key: "developers" },
  { href: "/search", key: "search" },
  { href: "/status", key: "status" },
  { href: "/security", key: "security" },
  { href: "/statistics", key: "statistics" },
  { href: "/about", key: "about" },
];

export default function Nav({ dict, lang }: { dict: Dictionary; lang: string }) {
  return (
    <header className="sticky top-0 z-40 border-b border-zinc-200 bg-white/85 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/85">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-5 gap-y-2 px-4 py-3">
        <Link href="/" className="flex items-center gap-2 font-extrabold tracking-tight text-zinc-900 dark:text-white">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-red-500 to-orange-500 text-lg text-white">
            O
          </span>
          OmniSource
        </Link>
        <nav aria-label="Primary" className="flex flex-1 flex-wrap items-center gap-x-4 gap-y-1 text-sm">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="rounded px-1 py-0.5 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800 dark:hover:text-white"
            >
              {dict.nav[l.key]}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <LanguageSwitcher lang={lang} label={dict.nav.language} />
        </div>
      </div>
    </header>
  );
}
