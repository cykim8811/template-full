import { NextRequest, NextResponse } from "next/server";
import { serverEnv } from "@/lib/env";

async function fetchUser(accessToken: string) {
  return fetch(`${serverEnv.BACKEND_URL}/users/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export async function GET(request: NextRequest) {
  const accessToken = request.cookies.get("access_token")?.value;

  if (!accessToken) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  let backendRes = await fetchUser(accessToken);

  // If access token expired, attempt silent refresh
  if (backendRes.status === 401) {
    const refreshToken = request.cookies.get("refresh_token")?.value;
    if (!refreshToken) {
      return NextResponse.json(
        { error: "Not authenticated" },
        { status: 401 },
      );
    }

    const refreshRes = await fetch(`${serverEnv.BACKEND_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!refreshRes.ok) {
      const response = NextResponse.json(
        { error: "Not authenticated" },
        { status: 401 },
      );
      response.cookies.delete("access_token");
      response.cookies.delete("refresh_token");
      return response;
    }

    const tokens = await refreshRes.json();

    // Retry with new access token
    backendRes = await fetchUser(tokens.access_token);

    if (!backendRes.ok) {
      return NextResponse.json(
        { error: "Not authenticated" },
        { status: 401 },
      );
    }

    const user = await backendRes.json();
    const secure = request.nextUrl.protocol === "https:";
    const response = NextResponse.json(user);

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

  if (!backendRes.ok) {
    return NextResponse.json(
      { error: "Not authenticated" },
      { status: backendRes.status },
    );
  }

  const user = await backendRes.json();
  return NextResponse.json(user);
}
