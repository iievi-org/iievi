import type { Metadata, Viewport } from "next";
import { Archivo_Narrow, Inter, JetBrains_Mono } from "next/font/google";
import type { ReactNode } from "react";

import { AppProviders } from "@/components/providers/AppProviders";
import { RootErrorBoundary } from "@/components/errors/ErrorBoundaries";
import { THEME_INIT_SCRIPT } from "@/lib/theme";

import "./globals.css";

const archivoNarrow = Archivo_Narrow({
  subsets: ["latin"],
  variable: "--font-display",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-body",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "IIEVI — One Chat. Every Business Task.",
  description:
    "Social-first AI automation for service businesses. Capture leads, book appointments, and follow up — automatically.",
  applicationName: "IIEVI",
  manifest: "/manifest.json",
  appleWebApp: { capable: true, statusBarStyle: "default", title: "IIEVI" },
  icons: {
    icon: "/icons/icon-192.png",
    apple: "/icons/apple-touch-icon.png",
  },
};

export const viewport: Viewport = {
  themeColor: "#f1ede3",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${archivoNarrow.variable} ${inter.variable} ${jetbrainsMono.variable}`}
    >
      <head>
        {/* Set the theme before paint to avoid a flash of the wrong palette. */}
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body>
        <AppProviders>
          <RootErrorBoundary>{children}</RootErrorBoundary>
        </AppProviders>
      </body>
    </html>
  );
}
