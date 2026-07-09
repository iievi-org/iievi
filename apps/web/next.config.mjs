import { withSentryConfig } from "@sentry/nextjs";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: [
    "@iievi/api-client",
    "@iievi/constants",
    "@iievi/types",
    "@iievi/validators",
  ],
};

// Source-map upload needs SENTRY_AUTH_TOKEN (CI/production only); local builds
// stay fast and offline without it.
export default process.env.SENTRY_AUTH_TOKEN
  ? withSentryConfig(nextConfig, { silent: true })
  : nextConfig;
