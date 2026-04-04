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
          destination: `${process.env.BACKEND_URL}/:path*`,
        },
      ],
    };
  },
};

export default nextConfig;
