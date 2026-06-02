import { JWTExpired } from "jose/errors";
import { jwtVerify } from "jose";
import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/login", "/api"];

// Routes under /api/* that this app implements natively (the auth BFF
// + per-provider OAuth callback). Anything else under /api/* is
// reverse-proxied to BACKEND_URL.
const LOCAL_API_ROUTES: RegExp[] = [
  /^\/api\/auth\/logout$/,
  /^\/api\/auth\/me$/,
  /^\/api\/auth\/refresh$/,
  /^\/api\/auth\/refresh-redirect$/,
  /^\/api\/auth\/[^/]+\/callback$/,
];

function getSecret() {
  const secret = process.env.SECRET_KEY;
  if (!secret) throw new Error("Missing required environment variable: SECRET_KEY");
  return new TextEncoder().encode(secret);
}

function proxyToBackend(request: NextRequest) {
  const backend = process.env.BACKEND_URL;
  if (!backend) {
    return NextResponse.json(
      { detail: "BACKEND_URL is not configured" },
      { status: 500 }
    );
  }
  // Strip the leading /api and graft the remaining path + query onto the
  // backend origin. NextResponse.rewrite preserves method/headers/body.
  const tail = request.nextUrl.pathname.replace(/^\/api/, "");
  const target = new URL(tail + request.nextUrl.search, backend);
  return NextResponse.rewrite(target);
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Reverse-proxy /api/* (except /api/auth/*) to BACKEND_URL at request
  // time. Moved out of next.config.ts because rewrites there are baked
  // at build time and would freeze BACKEND_URL to whatever the build
  // environment had.
  if (
    pathname.startsWith("/api/") &&
    !LOCAL_API_ROUTES.some((re) => re.test(pathname))
  ) {
    return proxyToBackend(request);
  }

  const accessToken = request.cookies.get("access_token")?.value;
  const refreshToken = request.cookies.get("refresh_token")?.value;

  if (pathname.startsWith("/login")) {
    if (accessToken) {
      try {
        await jwtVerify(accessToken, getSecret());
        return NextResponse.redirect(new URL("/", request.url));
      } catch {
        // Invalid/expired token — let them reach login
      }
    }
    return NextResponse.next();
  }

  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  if (!accessToken) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  try {
    await jwtVerify(accessToken, getSecret());
    return NextResponse.next();
  } catch (err) {
    if (err instanceof JWTExpired && refreshToken) {
      const redirectUrl = new URL("/api/auth/refresh-redirect", request.url);
      redirectUrl.searchParams.set("returnTo", pathname);
      return NextResponse.redirect(redirectUrl);
    }
    const response = NextResponse.redirect(new URL("/login", request.url));
    response.cookies.delete("access_token");
    response.cookies.delete("refresh_token");
    return response;
  }
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
  // Run on the Node.js runtime (not the default Edge runtime) so the
  // middleware can read process.env.BACKEND_URL at request time. On
  // Edge, runtime env access is restricted to `NEXT_PUBLIC_*` and the
  // explicit `env` block in next.config.ts — both inappropriate here
  // because BACKEND_URL is a server-only address.
  runtime: "nodejs",
};
