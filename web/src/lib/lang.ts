// Server-side locale resolution. The cookie is the single source of truth,
// read in the root layout and threaded down as props — the server HTML and
// the hydrated client tree always render the same strings.
import { cookies } from "next/headers";
import { DEFAULT_LOCALE, getDictionary, isLocale, type Dictionary, type Locale } from "@/i18n/dictionaries";

export const LANG_COOKIE = "omnisource-lang";

export async function getLang(): Promise<Locale> {
  const store = await cookies();
  const value = store.get(LANG_COOKIE)?.value;
  return isLocale(value) ? value : DEFAULT_LOCALE;
}

export async function getLangDict(): Promise<{ lang: Locale; dict: Dictionary }> {
  const lang = await getLang();
  const dict = await getDictionary(lang);
  return { lang, dict };
}

export function isRtl(lang: string): boolean {
  return lang === "ar";
}
