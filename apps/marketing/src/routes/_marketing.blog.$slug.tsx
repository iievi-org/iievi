import { createFileRoute, Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { Container } from "@/components/linen/Container";
import { Rule } from "@/components/linen/Rule";
import { Pill } from "@/components/linen/Pill";
import { FadeIn } from "@/components/linen/FadeIn";
import { CTASection } from "@/components/linen/CTASection";

export const Route = createFileRoute("/_marketing/blog/$slug")({
  head: ({ params }) => ({
    meta: [
      { title: `${params.slug.replace(/-/g, " ")} — IIEVI Blog` },
      {
        name: "description",
        content:
          "Field notes on Global service businesses, WhatsApp commerce, and building calm AI.",
      },
    ],
  }),
  component: BlogPost,
});

const TOC = [
  { id: "context", label: "The context" },
  { id: "data", label: "What the data shows" },
  { id: "playbook", label: "The playbook" },
  { id: "results", label: "What changed" },
  { id: "next", label: "What's next" },
];

function BlogPost() {
  const { t } = useTranslation();
  const { slug } = Route.useParams();
  const title = slug.replace(/-/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase());

  return (
    <>
      <Container>
        <div className="pt-12 pb-8">
          <Link
            to="/blog"
            className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone hover:text-ink"
          >
            ← Back to blog
          </Link>
        </div>
      </Container>

      <Container>
        <div className="max-w-[680px] mx-auto pb-12">
          <FadeIn>
            <Pill>{t("Playbook")}</Pill>
            <h1 className="mt-6 font-display text-headline-lg md:text-[64px] leading-[1.05] text-ink">
              {title}
            </h1>
            <p className="mt-6 font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
              {t("By Aarav Krishnan · 6 min read · Nov 2026")}
            </p>
          </FadeIn>
        </div>
      </Container>

      <Container>
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_220px] gap-12">
          <article className="max-w-[680px] mx-auto lg:mx-0 w-full">
            <FadeIn>
              <p className="font-body text-body-md text-graphite leading-[1.7]">
                <span className="font-display font-bold text-[80px] leading-none float-left mr-3 mt-2 text-ink">
                  A
                </span>
                t 11:47 PM on a Tuesday in October, a customer messaged Glow Salon in Bandra: "any
                slot tomorrow morning?" The owner was asleep. The message sat unread until 7:13 the
                next morning. By then the customer had already booked elsewhere. We see this exact
                pattern in our logs every single day, in every city, across every category.
              </p>
            </FadeIn>

            <h2 id="context" className="mt-12 font-display text-headline-md text-ink">
              {t("The context")}
            </h2>
            <p className="mt-4 text-body-md text-graphite leading-[1.7]">
              {t(
                "Global service businesses live on WhatsApp. The owner is the customer-service team. Replies happen between haircuts, between patients, between dispatches. Late at night, after a long day, replies stop entirely.",
              )}
            </p>

            <div className="border-l-2 border-l-signal pl-6 my-10">
              <p className="font-display text-headline-sm text-ink leading-[1.4]">
                {t(
                  '"If they don\'t reply in 5 minutes, I go to the next one. Three minutes is the new limit for me."',
                )}
              </p>
              <p className="mt-3 font-mono text-mono-sm text-stone uppercase tracking-[0.14em]">
                {t("Anonymous customer, Bangalore")}
              </p>
            </div>

            <h2 id="data" className="mt-12 font-display text-headline-md text-ink">
              {t("What the data shows")}
            </h2>
            <p className="mt-4 text-body-md text-graphite leading-[1.7]">
              {t(
                "Across 4.2 million conversations we processed in 2025, conversion drops 14% for every minute of delay in the first reply. After 5 minutes it's effectively flat — the customer has moved on.",
              )}
            </p>
            <div className="my-8 bg-neutral border border-hairline p-6">
              <pre className="font-mono text-mono-sm text-ink overflow-x-auto">{`Reply delay → Conversion rate
  0 - 60s       62%
  1 - 5m        43%
  5 - 30m       21%
  30m+           8%`}</pre>
            </div>

            <h2 id="playbook" className="mt-12 font-display text-headline-md text-ink">
              {t("The playbook")}
            </h2>
            <p className="mt-4 text-body-md text-graphite leading-[1.7]">
              {t("Three changes, in order of impact:")}
            </p>
            <ol className="mt-6 space-y-4 text-body-md text-graphite leading-[1.7] list-decimal pl-6">
              <li>{t("Acknowledge in 3 seconds, even if the answer takes longer.")}</li>
              <li>{t("Qualify and price in the same message, not over five back-and-forths.")}</li>
              <li>{t('Offer a specific slot, don\'t ask "when works for you".')}</li>
            </ol>

            <h2 id="results" className="mt-12 font-display text-headline-md text-ink">
              {t("What changed")}
            </h2>
            <p className="mt-4 text-body-md text-graphite leading-[1.7]">
              {t(
                "Glow Salon turned on IIEVI in early October. Within 21 days, their booked-from-WhatsApp rate climbed from 31% to 64%. Diwali week — historically a chaos period — was their calmest in three years.",
              )}
            </p>

            <h2 id="next" className="mt-12 font-display text-headline-md text-ink">
              {t("What's next")}
            </h2>
            <p className="mt-4 text-body-md text-graphite leading-[1.7]">
              {t(
                "We're rolling out voice-note replies and multilingual Tamil/Bengali later this quarter. If you'd like early access, write to us at field@iievi.in.",
              )}
            </p>
          </article>

          <aside className="hidden lg:block">
            <div className="sticky top-28 border-l border-hairline pl-6">
              <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone mb-4">
                {t("On this page")}
              </p>
              <ul className="space-y-3">
                {TOC.map((t) => (
                  <li key={t.id}>
                    <a
                      href={`#${t.id}`}
                      className="text-body-sm text-graphite hover:text-ink block"
                    >
                      {t.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      </Container>

      <div className="mt-24">
        <Rule />
        <CTASection />
      </div>
    </>
  );
}
