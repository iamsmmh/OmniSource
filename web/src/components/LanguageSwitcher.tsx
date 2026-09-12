"use client";

import { useRouter } from "next/navigation";
import { LOCALES } from "@/i18n/dictionaries";
import { LANG_COOKIE } from "@/lib/lang-client";

const NAMES: Record<string, string> = {
  en: "English",
  bn: "বাংলা",
  ar: "العربية",
  es: "Español",
  fr: "Français",
  de: "Deutsch",
  ja: "日本語",
  zh: "中文",
};

export default function LanguageSwitcher({ lang, label }: { lang: string; label: string }) {
  const router = useRouter();
  return (
    <label className="flex items-center gap-1.5 text-sm text-zinc-600 dark:text-zinc-300">
      <span className="sr-only">{label}</span>
      <span aria-hidden>🌐</span>
      <select
        value={lang}
        onChange={(e) => {
          document.cookie = `${LANG_COOKIE}=${e.target.value};path=/;max-age=31536000;SameSite=Lax`;
          router.refresh();
        }}
        className="rounded-lg border border-zinc-300 bg-transparent px-2 py-1 text-sm dark:border-zinc-700"
      >
        {LOCALES.map((l) => (
          <option key={l} value={l}>
            {NAMES[l]}
          </option>
        ))}
      </select>
    </label>
  );
}
