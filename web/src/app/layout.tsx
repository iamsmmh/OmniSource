import type { Metadata, Viewport } from "next";
import "./globals.css";
import Nav from "@/components/Nav";
import PwaRegister from "@/components/PwaRegister";
import { getGeneratedAt, getApps, getSources } from "@/lib/data";
import { getLangDict, isRtl } from "@/lib/lang";

export const metadata: Metadata = {
  title: { default: "OmniSource — verified source catalog", template: "%s · OmniSource" },
  description: "One feed for AltStore, SideStore, Feather, ESign and LiveContainer. Always current.",
  manifest: "/manifest.webmanifest",
  appleWebApp: { capable: true, title: "OmniSource", statusBarStyle: "default" },
};

export const viewport: Viewport = {
  themeColor: "#dc2626",
  width: "device-width",
  initialScale: 1,
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const { lang, dict } = await getLangDict();
  const apps = getApps().length;
  const sources = getSources().length;
  const synced = getGeneratedAt();
  return (
    <html lang={lang} dir={isRtl(lang) ? "rtl" : "ltr"}>
      <body className="min-h-screen bg-zinc-50 text-zinc-900 antialiased dark:bg-zinc-950 dark:text-zinc-100">
        <PwaRegister />
        <Nav dict={dict} lang={lang} />
        <main className="mx-auto w-full max-w-6xl px-4 py-8">{children}</main>
        <footer className="border-t border-zinc-200 py-6 text-center text-sm text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
          OmniSource · {apps} {dict.common.apps} · {sources} {dict.common.sources}
          {synced && <> · {dict.common.lastSync} {synced.slice(0, 10)}</>}
        </footer>
      </body>
    </html>
  );
}
