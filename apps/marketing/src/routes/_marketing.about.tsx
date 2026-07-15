import { createFileRoute } from "@tanstack/react-router";
import { Container, Section } from "@/components/linen/Container";
import { Rule } from "@/components/linen/Rule";
import { SectionLabel } from "@/components/linen/SectionLabel";
import { Card } from "@/components/linen/Card";
import { Stat } from "@/components/linen/Stat";
import { FadeIn } from "@/components/linen/FadeIn";
import { CTASection } from "@/components/linen/CTASection";

export const Route = createFileRoute("/_marketing/about")({
  head: () => ({
    meta: [
      { title: "About — IIEVI" },
      {
        name: "description",
        content:
          "We're building the AI back-office for service businesses everywhere in the world. Here's why.",
      },
      { property: "og:title", content: "About — IIEVI" },
      {
        property: "og:description",
        content: "Why we're building IIEVI for everyone everywhere in the world.",
      },
    ],
  }),
  component: AboutPage,
});

const values = [
  {
    name: "Calm",
    desc: "Software should reduce noise, not add to it. We measure our progress by how much we let business owners stop checking.",
  },
  {
    name: "Global",
    desc: "Built for everyone everywhere in the world, the way customers actually message — native languages, voice notes, photos, missed calls. No translation layer.",
  },
  {
    name: "Honest",
    desc: "We don't promise '10x your revenue'. We promise to reply in 3 seconds, every time. The revenue follows.",
  },
  {
    name: "Craft",
    desc: "From the chat tone to this typography. Service businesses deserve software that looks like it was made with care.",
  },
];

function AboutPage() {
  return (
    <>
      <Container>
        <div className="pt-16 md:pt-24 pb-12">
          <FadeIn>
            <SectionLabel>About IIEVI</SectionLabel>
          </FadeIn>
          <FadeIn delay={0.05}>
            <h1 className="mt-6 max-w-3xl font-display text-[44px] md:text-display-lg text-ink leading-[0.96]">
              We're building the AI back-office for everyone everywhere in the world.
            </h1>
          </FadeIn>
        </div>
      </Container>

      <Rule />

      <Section>
        <div className="max-w-[720px] mx-auto">
          <FadeIn>
            <SectionLabel>The Origin</SectionLabel>
          </FadeIn>
          <div className="mt-10 space-y-6 text-body-md text-graphite leading-[1.7]">
            <p>
              In 2026, our co-founders Raza Sabir and Mrityunjay Srivastava were running a small
              chain of three salons. Every evening they'd come home and spend two hours replying to
              WhatsApp messages. Most of them were the same five questions. Many had been waiting
              since morning. Some had already gone to the salon next door.
            </p>
            <p>
              The CRMs they tried were built for SaaS sales teams, not stylists. The chatbots they
              tried sounded like Wikipedia. The booking apps they tried asked customers to download
              something. None of them met customers where they already were — on chat, in native
              languages, sending voice notes and photos.
            </p>

            <div className="border-l-2 border-l-signal pl-6 my-12">
              <p className="font-display text-headline-sm text-ink leading-[1.4]">
                "We didn't need a CRM. We needed someone who'd just reply for us — the way we'd
                reply, in our voice, at 11 PM, while we were sleeping."
              </p>
              <p className="mt-4 font-mono text-mono-sm text-stone uppercase tracking-[0.14em]">
                Raza Sabir, CEO - Co-Founder & Mrityunjay Srivastava, CTO - Co-Founder
              </p>
            </div>

            <p>
              IIEVI is that someone. We've spent time training it to sound like a local service
              business — to handle native languages, voice notes, missed calls, and the rhythm of
              customer service everywhere. Today, 2,400+ businesses trust it to run their entire
              customer thread.
            </p>

            <div className="border-l-2 border-l-signal pl-6 my-12">
              <p className="font-display text-headline-sm text-ink leading-[1.4]">
                "Your leads are your business. We isolate every tenant, encrypt every byte, and
                never train shared models on your conversations. The competitor down the road will
                never know you exist on IIEVI."
              </p>
              <p className="mt-4 font-mono text-mono-sm text-stone uppercase tracking-[0.14em]">
                On data isolation — IIEVI security charter
              </p>
            </div>

            <p>
              We're 18 people. We're a long way from done. Our goal is simple: every service
              business everywhere should reply in 3 seconds — at 2 AM, on holidays, during a
              haircut. Without anyone having to.
            </p>
          </div>

          <div className="mt-16 grid grid-cols-1 md:grid-cols-2 gap-8">
            <FadeIn>
              <div className="group">
                <div className="aspect-[4/5] bg-neutral overflow-hidden border border-hairline mb-4 relative">
                  {/* Photo for Raza Sabir */}
                  <img src="" alt="Raza Sabir" className="object-cover w-full h-full" />
                </div>
                <h3 className="font-display text-headline-sm text-ink">Raza Sabir</h3>
                <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone mt-1">
                  CEO - Co-Founder
                </p>
              </div>
            </FadeIn>
            <FadeIn delay={0.1}>
              <div className="group">
                <div className="aspect-[4/5] bg-neutral overflow-hidden border border-hairline mb-4 relative">
                  {/* Photo for Mrityunjay Srivastava */}
                  <img src="" alt="Mrityunjay Srivastava" className="object-cover w-full h-full" />
                </div>
                <h3 className="font-display text-headline-sm text-ink">Mrityunjay Srivastava</h3>
                <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone mt-1">
                  CTO - Co-Founder
                </p>
              </div>
            </FadeIn>
          </div>
        </div>
      </Section>

      <Rule />

      <Section inset>
        <FadeIn>
          <SectionLabel>By the Numbers</SectionLabel>
        </FadeIn>
        <div className="mt-10 grid grid-cols-2 md:grid-cols-4 gap-8">
          <Stat value="2,400+" label="Active businesses" />
          <Stat value="18" label="People in team" />
          <Stat value="2M+" label="Messages processed" />
          <Stat value="Global" label="Reach" />
        </div>
      </Section>

      <Rule />

      <Section>
        <FadeIn>
          <SectionLabel>Values</SectionLabel>
        </FadeIn>
        <FadeIn delay={0.05}>
          <h2 className="mt-6 font-display text-headline-lg text-ink max-w-2xl">
            Four words we keep coming back to.
          </h2>
        </FadeIn>
        <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
          {values.map((v, i) => (
            <FadeIn key={v.name} delay={i * 0.05}>
              <Card className="h-full">
                <h3 className="font-display text-headline-md text-ink">{v.name}</h3>
                <p className="mt-4 text-body-sm text-graphite">{v.desc}</p>
              </Card>
            </FadeIn>
          ))}
        </div>
      </Section>

      <CTASection />
    </>
  );
}
