import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Reverse-proxying /api/* to the backend is done in middleware.ts so
  // BACKEND_URL is read at request time rather than baked into the
  // build. `next.config.ts` rewrites are evaluated at build time and
  // freeze whatever value process.env.BACKEND_URL had when the image
  // was built — fine for local dev, broken for any environment where
  // the backend lives at a different URL than during the build.
};

export default nextConfig;
