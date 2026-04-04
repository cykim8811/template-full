import { NextRequest, NextResponse } from "next/server";
import { serverEnv } from "@/lib/env";

export async function GET(request: NextRequest) {
  const rawReturnTo = request.nextUrl.searchParams.get("returnTo") ?? "/";
  const returnTo = rawReturnTo.startsWith("/") && !rawReturnTo.startsWith("//") ? rawReturnTo : "/";
  const refreshToken = request.cookies.get("refresh_token")?.value;

  if (!refreshToken) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  const backendRes = await fetch(`${serverEnv.BACKEND_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!backendRes.ok) {
    const response = NextResponse.redirect(new URL("/login", request.url));
    response.cookies.delete("access_token");
    response.cookies.delete("refresh_token");
    return response;
  }

  const tokens = await backendRes.json();
  const secure = request.nextUrl.protocol === "https:";
  const response = NextResponse.redirect(new URL(returnTo, request.url));

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

  return response;
}
