"use client";

import * as Sentry from "@sentry/nextjs";
import { Component, type ErrorInfo, type ReactNode } from "react";

import { Button } from "@/components/linen";

interface BoundaryProps {
  children: ReactNode;
}
interface BoundaryState {
  hasError: boolean;
}

abstract class ErrorBoundaryBase extends Component<BoundaryProps, BoundaryState> {
  override state: BoundaryState = { hasError: false };

  static getDerivedStateFromError(): BoundaryState {
    return { hasError: true };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    Sentry.captureException(error, { extra: { componentStack: info.componentStack } });
  }

  reset = (): void => this.setState({ hasError: false });

  protected abstract renderFallback(reset: () => void): ReactNode;

  override render(): ReactNode {
    return this.state.hasError ? this.renderFallback(this.reset) : this.props.children;
  }
}

function reload(): void {
  if (typeof window !== "undefined") window.location.reload();
}

/** Full-page boundary for catastrophic errors (mounted at the app root). */
export class RootErrorBoundary extends ErrorBoundaryBase {
  protected override renderFallback(): ReactNode {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col items-start justify-center gap-4 px-6">
        <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-signal">Error</p>
        <h1 className="font-display text-headline-md text-ink">Something went wrong</h1>
        <p className="font-body text-body-md text-graphite">
          The app hit an unexpected error. Reloading usually fixes it.
        </p>
        <Button variant="primary" onClick={reload}>
          Reload
        </Button>
      </main>
    );
  }
}

/** Full-page boundary inside the dashboard shell. */
export class DashboardErrorBoundary extends ErrorBoundaryBase {
  protected override renderFallback(): ReactNode {
    return (
      <div className="flex min-h-[60vh] flex-col items-start justify-center gap-4 px-6">
        <h2 className="font-display text-headline-md text-ink">Something went wrong</h2>
        <p className="font-body text-body-md text-graphite">
          This section failed to load. Try reloading the page.
        </p>
        <Button variant="primary" onClick={reload}>
          Reload
        </Button>
      </div>
    );
  }
}

/** Inline, card-sized boundary that wraps a single dashboard widget. */
export class WidgetErrorBoundary extends ErrorBoundaryBase {
  protected override renderFallback(reset: () => void): ReactNode {
    return (
      <div className="flex flex-col items-start gap-3 border border-hairline p-6">
        <p className="font-body text-body-sm text-graphite">Failed to load.</p>
        <Button variant="ghost" onClick={reset}>
          Retry
        </Button>
      </div>
    );
  }
}
