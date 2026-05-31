import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Proxy /api/* to the backend as a fallback rewrite. This ensures Next.js
  // API Routes (auth BFF: callback, logout, refresh, me) are matched first,
  // and only unmatched /api/* requests are forwarded to the backend.
  async rewrites() {
    return {
      beforeFiles: [],
      afterFiles: [],
      fallback: [
        {
          source: "/api/:path*",
          // BACKEND_URL is injected at pod start; Next.js validates the
          // destination at build time, so we fall back to a syntactically
          // valid placeholder there.
          destination: `${process.env.BACKEND_URL ?? "http://localhost:8000"}/:path*`,
        },
      ],
    };
  },
};

export default nextConfig;
