"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";
import { Toaster } from "sonner";

import { createQueryClient } from "@/lib/query-client";

import { UpgradeModalProvider } from "./UpgradeModalProvider";

/** App-wide providers: TanStack Query, the upgrade modal, and Sonner toasts. */
export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(createQueryClient);
  return (
    <QueryClientProvider client={queryClient}>
      <UpgradeModalProvider>{children}</UpgradeModalProvider>
      <Toaster
        position="bottom-right"
        toastOptions={{
          className: "font-body text-body-sm",
          style: {
            borderRadius: "0",
            border: "1px solid var(--border)",
            background: "var(--neutral)",
            color: "var(--secondary)",
          },
        }}
      />
    </QueryClientProvider>
  );
}
