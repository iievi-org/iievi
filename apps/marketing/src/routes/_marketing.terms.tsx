import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { Container } from "@/components/linen/Container";
import { Rule } from "@/components/linen/Rule";
import { SectionLabel } from "@/components/linen/SectionLabel";
import { FadeIn } from "@/components/linen/FadeIn";

export const Route = createFileRoute("/_marketing/terms")({
  head: () => ({
    meta: [
      { title: "Terms of Service — IIEVI" },
      { name: "description", content: "The terms that govern your use of IIEVI." },
    ],
  }),
  component: TermsPage,
});

const SECTIONS = [
  {
    id: "acceptance",
    title: "1. Acceptance of terms",
    body: "By creating an IIEVI account, you agree to these Terms of Service and to our Privacy Policy. If you are entering into these terms on behalf of a business, you confirm you have authority to do so.",
  },
  {
    id: "service",
    title: "2. The service",
    body: 'IIEVI provides AI-powered messaging automation for business communications, primarily via WhatsApp Business API. The service is provided on an "as-is" basis, subject to the uptime commitments in your subscription plan.',
  },
  {
    id: "account",
    title: "3. Your account",
    body: "You are responsible for maintaining the security of your account credentials, for all activity that occurs under your account, and for ensuring your use complies with WhatsApp Business policies and Global law.",
  },
  {
    id: "billing",
    title: "4. Billing and payment",
    body: "Subscription fees are billed monthly or annually in advance, in Global rupees, plus applicable GST. Failure to pay may result in suspension. Refunds are available within 30 days of the first invoice if you are not satisfied.",
  },
  {
    id: "acceptable",
    title: "5. Acceptable use",
    body: "You may not use IIEVI to send spam, harass, defraud, or violate any law. You may not attempt to reverse-engineer the service or to send messages to people who have not opted in to receive them.",
  },
  {
    id: "ip",
    title: "6. Intellectual property",
    body: "All IIEVI software, models, and brand are owned by IIEVI Technologies Pvt. Ltd. Conversation content remains owned by you and your customers.",
  },
  {
    id: "liability",
    title: "7. Limitation of liability",
    body: "Our total liability for any claim is limited to the fees you paid in the 12 months before the claim. We are not liable for indirect, incidental, or consequential damages.",
  },
  {
    id: "termination",
    title: "8. Termination",
    body: "You may cancel at any time from your dashboard. We may suspend or terminate for material breach of these terms with 14 days' notice and an opportunity to cure.",
  },
  {
    id: "law",
    title: "9. Governing law",
    body: "These terms are governed by the laws of India. Disputes are subject to the exclusive jurisdiction of the courts at Bangalore, Karnataka.",
  },
];

function TermsPage() {
  const { t } = useTranslation();
  return (
    <>
      <Container>
        <div className="pt-12 pb-8">
          <FadeIn>
            <SectionLabel>{t("Legal")}</SectionLabel>
            <h1 className="mt-6 font-display text-[44px] md:text-display-lg text-ink leading-[0.96]">
              {t("Terms of Service")}
            </h1>
            <p className="mt-6 font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
              {t("Last updated: 1 November 2026")}
            </p>
          </FadeIn>
        </div>
      </Container>

      <Rule />

      <Container>
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_220px] gap-12 py-16">
          <article className="max-w-[680px]">
            {SECTIONS.map((s, i) => (
              <div key={s.id}>
                <h2
                  id={s.id}
                  className="font-body text-headline-sm font-medium text-ink scroll-mt-24"
                >
                  {s.title}
                </h2>
                <p className="mt-4 text-body-md text-graphite leading-[1.7]">{s.body}</p>
                {i < SECTIONS.length - 1 && <Rule className="my-10" />}
              </div>
            ))}
          </article>
          <aside className="hidden lg:block">
            <div className="sticky top-28 border-l border-hairline pl-6">
              <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone mb-4">
                {t("Contents")}
              </p>
              <ul className="space-y-3">
                {SECTIONS.map((s) => (
                  <li key={s.id}>
                    <a
                      href={`#${s.id}`}
                      className="text-body-sm text-graphite hover:text-ink block"
                    >
                      {s.title}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      </Container>
    </>
  );
}
