"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function SearchBox({ placeholder, initial = "" }: { placeholder: string; initial?: string }) {
  const [value, setValue] = useState(initial);
  const router = useRouter();
  return (
    <form
      role="search"
      className="flex w-full max-w-xl gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        router.push(`/search?q=${encodeURIComponent(value)}`);
      }}
    >
      <input
        type="search"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        aria-label={placeholder}
        className="w-full rounded-xl border border-zinc-300 bg-white px-4 py-2.5 text-zinc-900 shadow-sm outline-none focus:border-red-500 focus:ring-2 focus:ring-red-200 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
      />
      <button
        type="submit"
        className="shrink-0 rounded-xl bg-red-600 px-5 py-2.5 font-semibold text-white shadow-sm hover:bg-red-700"
      >
        ⌘K
      </button>
    </form>
  );
}
