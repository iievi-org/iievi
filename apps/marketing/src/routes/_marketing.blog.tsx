import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Container, Section } from "@/components/linen/Container";
import { Rule } from "@/components/linen/Rule";
import { Pill } from "@/components/linen/Pill";
import { SectionLabel } from "@/components/linen/SectionLabel";
import { Tabs } from "@/components/linen/Tabs";
import { FadeIn } from "@/components/linen/FadeIn";

export const Route = createFileRoute("/_marketing/blog")({
  head: () => ({
    meta: [
      { title: "Blog — IIEVI" },
      {
        name: "description",
        content:
          "Field notes on Global service businesses, WhatsApp commerce, and building calm AI.",
      },
      { property: "og:title", content: "Blog — IIEVI" },
      {
        property: "og:description",
        content: "Field notes on Global service businesses and WhatsApp AI.",
      },
    ],
  }),
  component: BlogIndex,
});

const POSTS = [
  {
    slug: "five-second-rule",
    cat: "Playbook",
    title: "The 5-second rule that decides whether you keep the lead",
    excerpt:
      "67% of customers go to a competitor if you don't reply in 5 minutes. The math is brutal.",
    read: 6,
    featured: true,
  },
  {
    slug: "hinglish-ai",
    cat: "Engineering",
    title: "Why most AI bots fail in Multilinual Markets — and how we fixed it",
    excerpt:
      "Code-mixed Hindi-English is the default register of Global customer service. Most LLMs treat it as noise.",
    read: 9,
  },
  {
    slug: "diwali-bookings",
    cat: "Case Study",
    title: "How Glow Salon handled 4× Diwali bookings without hiring",
    excerpt:
      "A 14-day run-up, an AI on WhatsApp, and an inbox that never slept. Here's the playbook.",
    read: 7,
  },
  {
    slug: "review-timing",
    cat: "Playbook",
    title: "The exact moment to ask for a Google review",
    excerpt:
      "Not too early, not too late. Our data on 47,000 review requests shows the window is tighter than you think.",
    read: 5,
  },
  {
    slug: "voice-notes",
    cat: "Engineering",
    title: "Building voice-note understanding for Global English",
    excerpt:
      "Whisper out of the box misses 40% of Global English voice notes. Here's our fine-tuning approach.",
    read: 11,
  },
  {
    slug: "missed-call-funnel",
    cat: "Playbook",
    title: "Turn missed calls into bookings — the WhatsApp bridge",
    excerpt:
      "30% of small-business missed calls are real intent. A two-line WhatsApp autoresponder converts them.",
    read: 4,
  },
];

const CATS = ["All", "Playbook", "Engineering", "Case Study"];

function BlogIndex() {
  const { t } = useTranslation();
  const [cat, setCat] = useState("All");
  const filtered = cat === "All" ? POSTS : POSTS.filter((p) => p.cat === cat);
  const featured = POSTS.find((p) => p.featured)!;
  const rest = filtered.filter((p) => !p.featured || cat !== "All");

  return (
    <>
      <Container>
        <div className="pt-16 md:pt-24 pb-12 max-w-3xl">
          <FadeIn>
            <SectionLabel>{t("Field Notes")}</SectionLabel>
          </FadeIn>
          <FadeIn delay={0.05}>
            <h1 className="mt-6 font-display text-[44px] md:text-display-lg text-ink leading-[0.96]">
              {t("Blogs")}
            </h1>
          </FadeIn>
        </div>
      </Container>

      {cat === "All" && (
        <Container>
          <FadeIn>
            <Link to="/blog/$slug" params={{ slug: featured.slug }} className="block group">
              <div className="border border-hairline aspect-[16/7] bg-neutral mb-8 flex items-center justify-center">
                <span className="font-display text-display-lg text-stone/40">{featured.cat}</span>
              </div>
              <Pill>{featured.cat}</Pill>
              <h2 className="mt-6 font-display text-headline-lg text-ink max-w-3xl group-hover:underline underline-offset-8 decoration-signal decoration-2">
                {featured.title}
              </h2>
              <p className="mt-4 text-body-md text-graphite max-w-2xl">{featured.excerpt}</p>
              <p className="mt-4 font-mono text-mono-sm text-stone uppercase tracking-[0.04em]">
                {featured.read} min read
              </p>
            </Link>
          </FadeIn>
        </Container>
      )}

      <Rule className="mt-16" />
      <Container>
        <div className="py-6">
          <Tabs value={cat} onChange={setCat} options={CATS.map((c) => ({ value: c, label: c }))} />
        </div>
      </Container>
      <Rule />

      <Section>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {rest.map((p, i) => (
            <FadeIn key={p.slug} delay={i * 0.04} className="h-full">
              <Link to="/blog/$slug" params={{ slug: p.slug }} className="block group h-full">
                <div className="flex flex-col border border-hairline p-8 h-full bg-transparent hover:bg-neutral transition-colors">
                  <div className="flex-1">
                    <Pill>{p.cat}</Pill>
                    <h3 className="mt-6 font-display text-headline-md text-ink group-hover:underline underline-offset-4 decoration-signal">
                      {p.title}
                    </h3>
                    <p className="mt-4 text-body-sm text-graphite">{p.excerpt}</p>
                  </div>
                  <p className="mt-6 font-mono text-mono-sm text-stone uppercase">
                    {p.read} min read
                  </p>
                </div>
              </Link>
            </FadeIn>
          ))}
        </div>
      </Section>
    </>
  );
}
