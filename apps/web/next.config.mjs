import withPWAInit from "@ducanh2912/next-pwa";
import { withSentryConfig } from "@sentry/nextjs";

// App-shell precache + network-first runtime caching (the default cache treats
// cross-origin API GETs as NetworkFirst). Disabled in dev so HMR isn't cached.
const withPWA = withPWAInit({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  register: true,
  cacheOnFrontEndNav: true,
  reloadOnOnline: true,
  workboxOptions: { disableDevLogs: true },
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: [
    "@iievi/api-client",
    "@iievi/constants",
    "@iievi/types",
    "@iievi/validators",
  ],
  // Type-safe next/link hrefs — a wrong route is a build error.
  experimental: {
    typedRoutes: true,
  },
  images: {
    // R2-hosted media caches for an hour before revalidation.
    minimumCacheTTL: 3600,
    remotePatterns: [
      // Cloudflare R2 (S3-compatible) and its public/custom domains.
      { protocol: "https", hostname: "*.r2.cloudflarestorage.com" },
      { protocol: "https", hostname: "*.r2.dev" },
      // Cloudflare Images / CDN.
      { protocol: "https", hostname: "imagedelivery.net" },
      { protocol: "https", hostname: "*.iievi.app" },
      // NanoBanana / generated-creative CDN (host confirmed at integration time).
      { protocol: "https", hostname: "*.iievi.in" },
    ],
  },
};

const withPWAConfig = withPWA(nextConfig);

// Source-map upload needs SENTRY_AUTH_TOKEN (CI/production only); local builds
// stay fast and offline without it.
export default process.env.SENTRY_AUTH_TOKEN
  ? withSentryConfig(withPWAConfig, { silent: true })
  : withPWAConfig;
