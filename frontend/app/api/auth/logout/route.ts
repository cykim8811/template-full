import { NextRequest, NextResponse } from "next/server";
import { serverEnv } from "@/lib/env";

export async function GET(request: NextRequest) {
  const refreshToken = request.cookies.get("refresh_token")?.value;

  if (refreshToken) {
    try {
      await fetch(`${serverEnv.BACKEND_URL}/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch {
      // Backend unreachable — proceed with local cookie deletion anyway
    }
  }

  const response = NextResponse.redirect(new URL("/login", request.url));
  response.cookies.delete("access_token");
  response.cookies.delete("refresh_token");
  return response;
}
