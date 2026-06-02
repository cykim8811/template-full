/**
 * Catch-all reverse proxy for `/api/*` paths the auth BFF doesn't
 * implement. Forwards method + headers + body to BACKEND_URL.
 *
 * Why not Next.js `rewrites()` in `next.config.ts`? Build-time
 * evaluation freezes BACKEND_URL to whatever was in the build env.
 *
 * Why not middleware `NextResponse.rewrite()`? Rewriting to an
 * external origin is silently ignored — the request hangs and the
 * caller times out. A real proxy in a route handler reads env at
 * runtime and gives us proper status / streaming.
 *
 * Next.js routes by specificity: the BFF routes
 * (/api/auth/{logout,me,refresh,refresh-redirect,<provider>/callback})
 * are concrete and win; everything else under /api/* lands here.
 */

import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

async function proxy(request: NextRequest): Promise<Response> {
  const backend = process.env.BACKEND_URL;
  if (!backend) {
    return NextResponse.json(
      { detail: "BACKEND_URL is not configured" },
      { status: 500 }
    );
  }

  // Strip the leading /api and re-graft onto the backend origin.
  const tail = request.nextUrl.pathname.replace(/^\/api/, "");
  const target = new URL(tail + request.nextUrl.search, backend);

  // Forward most headers, but drop Host so fetch fills it from the
  // target URL. Otherwise the backend sees the public hostname and
  // any Host-based routing on the inside (Knative) breaks.
  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("connection");

  const init: RequestInit & { duplex?: string } = {
    method: request.method,
    headers,
    redirect: "manual",
  };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = request.body;
    // Required when streaming a request body in Node fetch.
    init.duplex = "half";
  }

  const upstream = await fetch(target, init);

  // Strip hop-by-hop headers Next can't safely pass through.
  const outHeaders = new Headers(upstream.headers);
  for (const h of ["content-encoding", "content-length", "transfer-encoding", "connection"]) {
    outHeaders.delete(h);
  }
  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: outHeaders,
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const HEAD = proxy;
export const OPTIONS = proxy;
