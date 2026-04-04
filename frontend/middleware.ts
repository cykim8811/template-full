import { JWTExpired } from "jose/errors";
import { jwtVerify } from "jose";
import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/login", "/api"];

function getSecret() {
  const secret = process.env.SECRET_KEY;
  if (!secret) throw new Error("Missing required environment variable: SECRET_KEY");
  return new TextEncoder().encode(secret);
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
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
};
