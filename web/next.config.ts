import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The static zero-dependency site keeps serving GitHub Pages; this app
  // deploys to Node hosting (Vercel / Cloudflare / self-hosted) with full
  // dynamic API routes. `output: "export"` remains possible (see README)
  // at the cost of the query-string API semantics.
  poweredByHeader: false,
  images: { unoptimized: true },
  async headers() {
    return [
      {
        source: "/api/v3/:path*",
        headers: [
          { key: "Cache-Control", value: "public, s-maxage=300, stale-while-revalidate=3600" },
        ],
      },
      {
        source: "/data/:path*",
        headers: [
          { key: "Cache-Control", value: "public, max-age=3600, stale-while-revalidate=86400" },
        ],
      },
    ];
  },
};

export default nextConfig;
