import { Link } from "@tanstack/react-router";
import { Twitter, Linkedin, Instagram, Youtube } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Container } from "@/components/linen/Container";
import { Rule } from "@/components/linen/Rule";

const cols = [
  {
    label: "Product",
    links: [
      { to: "/features", label: "Features" },
      { to: "/pricing", label: "Pricing" },
      { to: "/solutions/salons", label: "Solutions" },
      { to: "/demo", label: "Book a Demo" },
    ],
  },
  {
    label: "Company",
    links: [
      { to: "/about", label: "About" },
      { to: "/blog", label: "Blog" },
      { to: "/help", label: "Help Center" },
      { to: "/faq", label: "FAQ" },
    ],
  },
  {
    label: "Legal",
    links: [
      { to: "/privacy", label: "Privacy Policy" },
      { to: "/terms", label: "Terms of Service" },
    ],
  },
];

export function Footer() {
  const { t } = useTranslation();
  return (
    <footer className="bg-surface">
      <Rule />
      <Container>
        <div className="py-16 grid grid-cols-1 md:grid-cols-12 gap-8">
          <div className="md:col-span-3">
            <Link to="/" className="font-display font-bold text-[22px] tracking-[-0.01em] text-ink">
              {t("IIEVI")}
            </Link>
            <p className="mt-4 text-body-sm text-graphite max-w-xs">
              {t("AI business automation for Global service businesses. One chat handles every task — leads, bookings, follow-ups, and reviews.")}
            </p>
            <div className="mt-6 flex items-center gap-4 text-stone">
              {[Twitter, Linkedin, Instagram, Youtube].map((Icon, i) => (
                <a key={i} href="#" aria-label="Social" className="hover:text-ink transition-colors">
                  <Icon size={18} strokeWidth={1.5} />
                </a>
              ))}
            </div>
          </div>
          {cols.map((c) => (
            <div key={c.label} className="md:col-span-3">
              <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone mb-5">{c.label}</p>
              <ul className="space-y-3">
                {c.links.map((l) => (
                  <li key={l.to}>
                    <Link
                      to={l.to}
                      className="text-body-sm text-graphite hover:text-ink transition-colors"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Container>
      <Rule />
      <Container>
        <div className="py-6 flex flex-col md:flex-row items-center justify-between gap-3">
          <p className="font-mono text-mono-sm text-stone">
            © {new Date().getFullYear()} IIEVI Technologies Pvt. Ltd.
          </p>
          <p className="font-mono text-mono-sm text-stone">{t("Made with ❤ in India")}</p>
        </div>
      </Container>
    </footer>
  );
}
