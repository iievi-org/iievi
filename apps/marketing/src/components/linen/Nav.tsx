import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Menu, X } from "lucide-react";
import { Container } from "@/components/linen/Container";
import { ButtonLink } from "@/components/linen/Button";
import { ThemeToggle } from "@/components/linen/ThemeToggle";

const NAV = [
  { to: "/features", label: "Features" },
  { to: "/pricing", label: "Pricing" },
  { to: "/solutions", label: "Solutions" },
  { to: "/about", label: "About" },
  { to: "/blog", label: "Blog" },
  { to: "/help", label: "Help" },
];

export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <header
      className={`sticky top-0 z-50 transition-colors duration-200 ${
        scrolled ? "bg-surface border-b border-hairline" : "bg-transparent"
      }`}
    >
      <Container>
        <div className="flex items-center justify-between h-16 md:h-20">
          <Link
            to="/"
            className="font-display font-bold text-[22px] tracking-[-0.01em] text-ink"
            onClick={() => setOpen(false)}
          >
            IIEVI
          </Link>
          <nav className="hidden md:flex items-center gap-8">
            {NAV.map((n) => (
              <Link
                key={n.to}
                to={n.to}
                className="font-body text-label-sm uppercase tracking-[0.14em] text-graphite hover:text-ink transition-colors pb-1 border-b-2 border-transparent"
                activeProps={{ className: "text-ink border-signal" }}
                activeOptions={{ exact: false }}
              >
                {n.label}
              </Link>
            ))}
          </nav>
          <div className="hidden md:flex items-center gap-3">
            <ThemeToggle />
            <ButtonLink to="/register" variant="ghost">
              Login
            </ButtonLink>
            <ButtonLink to="/register" variant="primary">
              Start Free
            </ButtonLink>
          </div>

          <button
            className="md:hidden text-ink p-2"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen(!open)}
          >
            {open ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </Container>

      {open && (
        <div className="md:hidden fixed inset-0 top-16 bg-surface z-40 overflow-y-auto">
          <Container>
            <div className="py-8 flex flex-col">
              {NAV.map((n) => (
                <Link
                  key={n.to}
                  to={n.to}
                  onClick={() => setOpen(false)}
                  className="font-display text-headline-md text-ink py-5 border-b border-hairline"
                >
                  {n.label}
                </Link>
              ))}
              <div className="flex flex-col gap-3 pt-8">
                <div className="flex items-center justify-between border border-hairline px-4 py-3">
                  <span className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
                    Theme
                  </span>
                  <ThemeToggle />
                </div>
                <ButtonLink to="/register" variant="ghost" onClick={() => setOpen(false)}>
                  Login
                </ButtonLink>
                <ButtonLink to="/register" variant="primary" onClick={() => setOpen(false)}>
                  Start Free
                </ButtonLink>
              </div>
            </div>
          </Container>
        </div>
      )}
    </header>
  );
}
