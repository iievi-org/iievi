import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { Container } from "@/components/linen/Container";
import { Rule } from "@/components/linen/Rule";
import { SectionLabel } from "@/components/linen/SectionLabel";
import { FadeIn } from "@/components/linen/FadeIn";

export const Route = createFileRoute("/_marketing/privacy")({
  head: () => ({
    meta: [
      { title: "Privacy Policy — IIEVI" },
      { name: "description", content: "How IIEVI collects, stores, and protects your data and your customers' data." },
    ],
  }),
  component: PrivacyPage,
});

const SECTIONS = [
  { id: "intro", title: "1. Introduction", body: "IIEVI Technologies Pvt. Ltd. (\"IIEVI\", \"we\", \"us\") is committed to protecting your privacy and that of your customers. This Privacy Policy explains how we collect, use, store, and share information." },
  { id: "data", title: "2. Data we collect", body: "Account data: name, email, business name, GSTIN, phone. Conversation data: messages sent and received on connected WhatsApp numbers, for the purpose of generating AI responses. Usage data: log files, IP address, device type." },
  { id: "use", title: "3. How we use your data", body: "To provide the IIEVI service, to generate AI replies on your behalf, to bill you correctly, to provide customer support, and to comply with applicable Global law including DPDP Act 2023." },
  { id: "sharing", title: "4. Sharing", body: "We do not sell your data. We share data only with: (a) sub-processors required to deliver the service (e.g. WhatsApp Business API providers, payment processors), (b) when compelled by a valid Global legal order, (c) with your explicit consent." },
  { id: "retention", title: "5. Retention", body: "Conversation data is retained for the duration of your subscription plus 90 days. You may request earlier deletion in writing to privacy@iievi.in. Account billing data is retained for 7 years per Global tax law." },
  { id: "rights", title: "6. Your rights under DPDP", body: "You may access, correct, or delete your personal data at any time. You may withdraw consent for processing. You may file a grievance with our Data Protection Officer at dpo@iievi.in." },
  { id: "security", title: "7. Security", body: "We are ISO 27001 certified. Data is encrypted at rest (AES-256) and in transit (TLS 1.3). We perform third-party penetration testing annually." },
  { id: "contact", title: "8. Contact", body: "Questions? privacy@iievi.in or write to: IIEVI Technologies Pvt. Ltd., 4th Floor, HSR Layout Sector 1, Bangalore 560102." },
];

function PrivacyPage() {
  const { t } = useTranslation();
  return (
    <>
      <Container>
        <div className="pt-12 pb-8">
          <FadeIn>
            <SectionLabel>{t("Legal")}</SectionLabel>
            <h1 className="mt-6 font-display text-[44px] md:text-display-lg text-ink leading-[0.96]">
              {t("Privacy Policy")}
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
                <h2 id={s.id} className="font-body text-headline-sm font-medium text-ink scroll-mt-24">{s.title}</h2>
                <p className="mt-4 text-body-md text-graphite leading-[1.7]">{s.body}</p>
                {i < SECTIONS.length - 1 && <Rule className="my-10" />}
              </div>
            ))}
          </article>
          <aside className="hidden lg:block">
            <div className="sticky top-28 border-l border-hairline pl-6">
              <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone mb-4">{t("Contents")}</p>
              <ul className="space-y-3">
                {SECTIONS.map((s) => (
                  <li key={s.id}>
                    <a href={`#${s.id}`} className="text-body-sm text-graphite hover:text-ink block">
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
