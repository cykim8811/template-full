import { NextRequest, NextResponse } from "next/server";
import { serverEnv } from "@/lib/env";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ provider: string }> },
) {
  const { provider } = await params;

  const ALLOWED_PROVIDERS = ["github", "google"];
  if (!ALLOWED_PROVIDERS.includes(provider)) {
    return NextResponse.redirect(new URL("/login?error=unknown_provider", request.url));
  }

  const { searchParams } = request.nextUrl;
  const code = searchParams.get("code");
  const state = searchParams.get("state");

  if (!code || !state) {
    return NextResponse.redirect(new URL("/login?error=missing_params", request.url));
  }

  const callbackUrl = new URL(`/auth/${provider}/callback`, serverEnv.BACKEND_URL);
  callbackUrl.searchParams.set("code", code);
  callbackUrl.searchParams.set("state", state);

  const backendRes = await fetch(callbackUrl.toString(), {
    headers: { cookie: request.headers.get("cookie") ?? "" },
    redirect: "manual",
  });

  if (!backendRes.ok) {
    return NextResponse.redirect(new URL("/login?error=oauth_failed", request.url));
  }

  const tokens = await backendRes.json();
  const response = NextResponse.redirect(new URL("/", request.url));

  const secure = request.nextUrl.protocol === "https:";

  response.cookies.set("access_token", tokens.access_token, {
    httpOnly: true,
    sameSite: "lax",
    secure,
    path: "/",
    maxAge: tokens.expires_in,
  });

  response.cookies.set("refresh_token", tokens.refresh_token, {
    httpOnly: true,
    sameSite: "lax",
    secure,
    path: "/",
    maxAge: 30 * 24 * 60 * 60,
  });

  // Clear the oauth_state cookie set by the backend
  response.cookies.delete("oauth_state");

  return response;
}
