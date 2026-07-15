import { type ReactNode } from "react";

import { DashboardSidebar } from "@/components/dashboard/DashboardSidebar";
import { DashboardErrorBoundary } from "@/components/errors/ErrorBoundaries";
import { UpdateBanner } from "@/components/realtime/UpdateBanner";
import { AuthProvider } from "@/lib/auth-context";
import { WebSocketProvider } from "@/lib/websocket";

/** The authenticated dashboard shell: auth + realtime providers, sidebar, and an error boundary. */
export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <WebSocketProvider>
        <UpdateBanner />
        <div className="flex min-h-screen">
          <DashboardSidebar />
          <main className="min-w-0 flex-1">
            <DashboardErrorBoundary>{children}</DashboardErrorBoundary>
          </main>
        </div>
      </WebSocketProvider>
    </AuthProvider>
  );
}
