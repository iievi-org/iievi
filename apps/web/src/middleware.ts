import { type NextRequest, NextResponse } from "next/server";

/**
 * Guards the dashboard (Prompt 8 Step 3). Middleware can't validate a JWT, so it
 * only checks for a session cookie's presence and redirects to /login otherwise,
 * preserving the original URL as ?redirect. We check `csrf_token` (Path=/) rather
 * than `refresh_token` (scoped to /api/v1/auth/refresh, so never sent here); both
 * are set on login and cleared on logout, so it's an equivalent presence signal.
 */
export function middleware(request: NextRequest): NextResponse {
  if (!request.cookies.has("csrf_token")) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", `${request.nextUrl.pathname}${request.nextUrl.search}`);
    return NextResponse.redirect(loginUrl);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
