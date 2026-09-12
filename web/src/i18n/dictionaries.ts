// Lazy dictionaries with English fallback. Only the active locale is
// bundled into the client; the server renders with the cookie locale so
// the HTML and the hydrated tree always agree (no hydration mismatch).
export const LOCALES = ["en", "bn", "ar", "es", "fr", "de", "ja", "zh"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "en";

export interface Dictionary {
  nav: Record<string, string>;
  common: Record<string, string>;
  home: Record<string, string>;
  sections: Record<string, string>;
}

const loaders: Record<Locale, () => Promise<{ default: Dictionary }>> = {
  en: () => import("./locales/en"),
  bn: () => import("./locales/bn"),
  ar: () => import("./locales/ar"),
  es: () => import("./locales/es"),
  fr: () => import("./locales/fr"),
  de: () => import("./locales/de"),
  ja: () => import("./locales/ja"),
  zh: () => import("./locales/zh"),
};

export function isLocale(value: unknown): value is Locale {
  return typeof value === "string" && (LOCALES as readonly string[]).includes(value);
}

export async function getDictionary(locale: string): Promise<Dictionary> {
  const lang: Locale = isLocale(locale) ? locale : DEFAULT_LOCALE;
  try {
    return (await loaders[lang]()).default;
  } catch {
    return (await loaders.en()).default; // Fallback to English, always.
  }
}
