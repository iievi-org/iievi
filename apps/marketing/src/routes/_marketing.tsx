import { createFileRoute, Outlet } from "@tanstack/react-router";
import { Nav } from "@/components/linen/Nav";
import { Footer } from "@/components/linen/Footer";

export const Route = createFileRoute("/_marketing")({
  component: MarketingLayout,
});

function MarketingLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-surface">
      <Nav />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
