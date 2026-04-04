import { NextRequest, NextResponse } from "next/server";
import { serverEnv } from "@/lib/env";

export async function POST(request: NextRequest) {
  const refreshToken = request.cookies.get("refresh_token")?.value;

  if (!refreshToken) {
    return NextResponse.json({ error: "No refresh token" }, { status: 401 });
  }

  const backendRes = await fetch(`${serverEnv.BACKEND_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!backendRes.ok) {
    const response = NextResponse.json(
      { error: "Refresh failed" },
      { status: 401 },
    );
    response.cookies.delete("access_token");
    response.cookies.delete("refresh_token");
    return response;
  }

  const tokens = await backendRes.json();
  const secure = request.nextUrl.protocol === "https:";
  const response = NextResponse.json({ ok: true });

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
