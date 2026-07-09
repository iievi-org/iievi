import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Check, Minus } from "lucide-react";
import { Container, Section } from "@/components/linen/Container";
import { Rule } from "@/components/linen/Rule";
import { Card } from "@/components/linen/Card";
import { SectionLabel } from "@/components/linen/SectionLabel";
import { Pill } from "@/components/linen/Pill";
import { ButtonLink } from "@/components/linen/Button";
import { FadeIn } from "@/components/linen/FadeIn";
import { Accordion } from "@/components/linen/Accordion";
import { CTASection } from "@/components/linen/CTASection";

export const Route = createFileRoute("/_marketing/pricing")({
  head: () => ({
    meta: [
      { title: "Pricing — IIEVI | Plans for Global Service Businesses" },
      { name: "description", content: "Transparent INR pricing. Start free, scale as you grow. No setup fees, no hidden costs." },
      { property: "og:title", content: "Pricing — IIEVI" },
      { property: "og:description", content: "Three plans built for Global service businesses of every size." },
    ],
  }),
  component: PricingPage,
});

const plans = [
  {
    name: "Starter",
    monthly: 1499,
    yearly: 1199,
    tagline: "For solo founders and single-location shops",
    features: [
      { ok: true, t: "1 WhatsApp number" },
      { ok: true, t: "500 AI replies / month" },
      { ok: true, t: "Smart bookings + calendar" },
      { ok: true, t: "Review automation" },
      { ok: true, t: "Email support" },
      { ok: false, t: "Custom workflows" },
      { ok: false, t: "Multi-staff routing" },
      { ok: false, t: "Brand voice training" },
    ],
  },
  {
    name: "Growth",
    monthly: 3999,
    yearly: 3199,
    tagline: "For growing service businesses with a team",
    features: [
      { ok: true, t: "3 WhatsApp numbers" },
      { ok: true, t: "5,000 AI replies / month" },
      { ok: true, t: "Smart bookings + calendar" },
      { ok: true, t: "Review automation" },
      { ok: true, t: "Multi-staff routing" },
      { ok: true, t: "Custom workflows" },
      { ok: true, t: "Brand voice training" },
      { ok: true, t: "Phone + chat support" },
    ],
    featured: true,
  },
  {
    name: "Scale",
    monthly: 9999,
    yearly: 7999,
    tagline: "For multi-location and franchise operators",
    features: [
      { ok: true, t: "Unlimited WhatsApp numbers" },
      { ok: true, t: "Unlimited AI replies" },
      { ok: true, t: "Everything in Growth" },
      { ok: true, t: "Multi-location dashboard" },
      { ok: true, t: "Dedicated success manager" },
      { ok: true, t: "API + Zapier access" },
      { ok: true, t: "Onsite onboarding" },
      { ok: true, t: "SLA-backed uptime" },
    ],
  },
];

const compareRows = [
  ["WhatsApp numbers", "1", "3", "Unlimited"],
  ["AI replies / month", "500", "5,000", "Unlimited"],
  ["Smart bookings", "✓", "✓", "✓"],
  ["Review automation", "✓", "✓", "✓"],
  ["Multi-staff routing", "—", "✓", "✓"],
  ["Custom workflows", "—", "✓", "✓"],
  ["Brand voice training", "—", "✓", "✓"],
  ["Social channels (Meta · IG · LinkedIn · TikTok)", "1 channel", "All 4", "All 4 + multi-brand"],
  ["Campaign automation", "—", "Weekly", "Daily + multi-location"],
  ["AI tools budget included", "₹1,000 / mo", "₹5,000 / mo", "₹20,000 / mo"],
  ["AI booking discounts", "—", "✓", "✓ + custom rules"],
  ["Onboarding sessions", "Self-serve", "3 guided", "Onsite + dedicated"],
  ["Data isolation tier", "Shared cluster", "Dedicated tenant", "Dedicated tenant + region pin"],
  ["API + Zapier", "—", "—", "✓"],
  ["Dedicated success manager", "—", "—", "✓"],
  ["Onsite onboarding", "—", "—", "✓"],
  ["Support", "Email", "Phone + chat", "24/7 dedicated"],
];


const faqs = [
  { question: "Is there really a free trial?", answer: "Yes — 14 days, full Growth plan features, no credit card required. You'll only need to add billing at the end of the trial if you want to keep going." },
  { question: "Can I change plans later?", answer: "Anytime. Upgrades take effect immediately; downgrades happen at the next billing cycle. Annual plans pro-rate any upgrade." },
  { question: "What does an 'AI reply' count as?", answer: "One outgoing message from IIEVI to a customer. Status messages, reminders, and review requests don't count toward your limit." },
  { question: "Do you support GST invoicing?", answer: "Yes — all invoices are GST-compliant. Enter your GSTIN in billing settings and we'll generate proper credit and tax invoices." },
  { question: "What happens if I exceed my plan?", answer: "We never cut off your customers. You'll get a notification at 80% and we'll charge a small per-message overage at the end of the month — or you can upgrade." },
  { question: "Is my customer data secure?", answer: "Yes. We're ISO 27001 certified, hosted in India, and fully DPDP-compliant. We never train models on your conversations." },
];

function PricingPage() {
  const { t } = useTranslation();
  const [yearly, setYearly] = useState(true);

  return (
    <>
      <Container>
        <div className="pt-16 md:pt-24 pb-12 text-center max-w-3xl mx-auto">
          <FadeIn><SectionLabel>{t("Pricing")}</SectionLabel></FadeIn>
          <FadeIn delay={0.05}>
            <h1 className="mt-6 font-display text-[44px] md:text-display-lg text-ink leading-[0.96]">
              {t("Plans that pay for themselves.")}
            </h1>
          </FadeIn>
          <FadeIn delay={0.1}>
            <p className="mt-6 text-body-md text-graphite">
              {t("Average IIEVI customer recovers ₹1.38L in missed bookings within 30 days. All plans in INR. No setup fees. Cancel anytime.")}
            </p>
          </FadeIn>
          <FadeIn delay={0.15}>
            <div className="mt-10 inline-flex items-center gap-2 border border-hairline p-1">
              <button
                onClick={() => setYearly(false)}
                className={`px-5 py-2 font-body text-label-sm uppercase tracking-[0.14em] cursor-pointer transition-colors ${!yearly ? "bg-ink text-surface" : "text-graphite"
                  }`}
              >
                {t("Monthly")}
              </button>
              <button
                onClick={() => setYearly(true)}
                className={`px-5 py-2 font-body text-label-sm uppercase tracking-[0.14em] cursor-pointer transition-colors flex items-center gap-2 ${yearly ? "bg-ink text-surface" : "text-graphite"
                  }`}
              >
                {t("Yearly")}
                <Pill variant="signal" className="!px-2 !py-0.5 !text-[10px]">{t("Save 20%")}</Pill>
              </button>
            </div>
          </FadeIn>
        </div>
      </Container>

      <Container>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pb-16">
          {plans.map((p, i) => (
            <FadeIn key={p.name} delay={i * 0.06}>
              <Card className={`h-full flex flex-col ${p.featured ? "border-2 border-ink" : ""}`}>
                {p.featured && (
                  <div className="mb-6">
                    <Pill variant="ink">{t("Most Popular")}</Pill>
                  </div>
                )}
                <h3 className="font-display text-headline-md text-ink">{p.name}</h3>
                <p className="mt-2 text-body-sm text-graphite">{p.tagline}</p>
                <div className="mt-8 flex items-baseline gap-2">
                  <span className="font-display text-display-lg text-ink">
                    ₹{(yearly ? p.yearly : p.monthly).toLocaleString("en-IN")}
                  </span>
                  <span className="font-mono text-mono-sm text-stone uppercase tracking-[0.04em]">/month</span>
                </div>
                {yearly && (
                  <p className="font-mono text-mono-sm text-stone mt-2">
                    {t("Billed ₹")}{(p.yearly * 12).toLocaleString("en-IN")} {t("yearly")}
                  </p>
                )}
                <ul className="mt-8 space-y-3 flex-1">
                  {p.features.map((f) => (
                    <li key={f.t} className="flex items-start gap-3 text-body-sm">
                      {f.ok ? (
                        <Check size={16} className="text-signal mt-1 shrink-0" strokeWidth={1.5} />
                      ) : (
                        <Minus size={16} className="text-stone mt-1 shrink-0" strokeWidth={1.5} />
                      )}
                      <span className={f.ok ? "text-graphite" : "text-stone"}>{f.t}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-10">
                  <ButtonLink
                    to="/register"
                    variant={p.featured ? "primary" : "ghost"}
                    className="w-full"
                  >
                    {t("Start Free Trial")}
                  </ButtonLink>
                </div>
              </Card>
            </FadeIn>
          ))}
        </div>
      </Container>

      <Rule />

      <Section>
        <FadeIn><SectionLabel>{t("Full Comparison")}</SectionLabel></FadeIn>
        <FadeIn delay={0.05}>
          <h2 className="mt-6 font-display text-headline-lg text-ink">
            {t("Every feature, every plan.")}
          </h2>
        </FadeIn>
        <div className="mt-12 overflow-x-auto">
          <table className="w-full min-w-[640px] border-t border-hairline">
            <thead>
              <tr className="bg-neutral">
                <th className="text-left font-mono text-mono-sm uppercase tracking-[0.14em] text-stone px-4 py-4">{t("Feature")}</th>
                {plans.map((p) => (
                  <th key={p.name} className="text-left font-mono text-mono-sm uppercase tracking-[0.14em] text-stone px-4 py-4">{p.name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {compareRows.map((row) => (
                <tr key={row[0]} className="border-b border-hairline">
                  <td className="font-body text-body-sm text-ink px-4 py-4">{row[0]}</td>
                  {row.slice(1).map((c, i) => (
                    <td key={i} className="font-mono text-mono-sm text-graphite px-4 py-4">{c}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Rule />

      <Section>
        <FadeIn><SectionLabel>{t("Pricing FAQ")}</SectionLabel></FadeIn>
        <FadeIn delay={0.05}>
          <h2 className="mt-6 font-display text-headline-lg text-ink max-w-3xl">
            {t("Questions before you start.")}
          </h2>
        </FadeIn>
        <div className="mt-10 max-w-3xl">
          <Accordion items={faqs} />
        </div>
      </Section>

      <CTASection />
    </>
  );
}
