import { useRef, useState, useEffect } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { useInView } from "framer-motion";
import { Container, Section } from "@/components/linen/Container";
import { Rule } from "@/components/linen/Rule";
import { SectionLabel } from "@/components/linen/SectionLabel";
import { Card } from "@/components/linen/Card";
import { Pill } from "@/components/linen/Pill";
import { FadeIn } from "@/components/linen/FadeIn";
import { CTASection } from "@/components/linen/CTASection";
import { PlaybookMockup } from "@/components/linen/PlaybookMockup";
import { PlaybookProgress } from "@/components/linen/PlaybookProgress";
import { ButtonLink } from "@/components/linen/Button";
import {
  getCategoryData,
  SOLUTION_CATEGORIES,
  type PlaybookStep,
} from "@/lib/solutionPlaybookData";

export const Route = createFileRoute("/_marketing/solutions/$category")({
  head: ({ params }) => {
    const data = getCategoryData(params.category);
    if (!data) return { meta: [{ title: "Solutions — IIEVI" }] };
    return {
      meta: [
        { title: `${data.label} — IIEVI` },
        { name: "description", content: data.intro },
        { property: "og:title", content: `${data.label} on IIEVI` },
        { property: "og:description", content: data.intro },
      ],
    };
  },
  component: PlaybookPage,
  notFoundComponent: () => (
    <Container>
      <div className="py-32 text-center">
        <h1 className="font-display text-headline-lg text-ink">Solution not found.</h1>
        <Link to="/solutions" className="mt-6 inline-block text-ink border-b border-hairline">
          See all solutions
        </Link>
      </div>
    </Container>
  ),
});

function PlaybookPage() {
  const { category } = Route.useParams();
  const data = getCategoryData(category);
  const { t } = useTranslation();
  // Scroll tracking state — declared before the early return to satisfy rules-of-hooks.
  const [activeStepIndex, setActiveStepIndex] = useState(0);

  if (!data) {
    return (
      <Container>
        <div className="py-32 text-center">
          <h1 className="font-display text-headline-lg text-ink">Solution not found.</h1>
          <Link to="/solutions" className="mt-6 inline-block text-ink border-b border-hairline">
            See all solutions
          </Link>
        </div>
      </Container>
    );
  }

  const others = Object.entries(SOLUTION_CATEGORIES).filter(([k]) => k !== category);

  return (
    <>
      <Container>
        <div className="pt-16 md:pt-24 pb-8 max-w-3xl">
          <FadeIn>
            <Pill>{t(data.label)}</Pill>
          </FadeIn>
          <FadeIn delay={0.05}>
            <h1 className="mt-6 font-display text-[40px] md:text-display-lg text-ink leading-[0.96]">
              {t(data.headline)}
            </h1>
          </FadeIn>
          <FadeIn delay={0.1}>
            <p className="mt-8 text-body-md text-graphite">{t(data.intro)}</p>
          </FadeIn>
        </div>
      </Container>

      <Rule />

      {/* The Playbook Layout */}
      <section className="relative">
        <Container>
          {/* Desktop Progress Indicator - Top Horizontal */}
          <div className="hidden lg:block sticky top-[80px] z-10 bg-surface/90 backdrop-blur py-4 mb-8 border-b border-hairline">
            <PlaybookProgress steps={data.playbook} activeStepIndex={activeStepIndex} />
          </div>

          <div className="flex flex-col lg:flex-row items-start relative pb-24">
            {/* Left Column: Scrolling Steps */}
            <div className="w-full lg:w-[40%] lg:pr-12">
              {/* The steps content */}
              <div className="space-y-[30vh]">
                {data.playbook.map((step, index) => (
                  <StepBlock
                    key={step.stepNumber}
                    step={step}
                    index={index}
                    onInView={() => setActiveStepIndex(index)}
                  />
                ))}
              </div>
            </div>

            {/* Right Column: Sticky Mockup */}
            <div className="hidden lg:block w-[60%] sticky top-0 h-screen py-24 pl-8 border-l border-hairline">
              <PlaybookMockup
                mockup={data.playbook[activeStepIndex].mockup}
                key={activeStepIndex}
              />
            </div>

            {/* Mobile Mockup Fallback (shown inline below each step on mobile) */}
            {/* Handled inside StepBlock for mobile screens */}
          </div>
        </Container>
      </section>

      <Rule />

      {/* Try It Live Section */}
      <Section inset>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <FadeIn>
              <SectionLabel>{t("See the Entire Workflow in Action")}</SectionLabel>
              <h2 className="mt-6 font-display text-headline-lg text-ink">
                {t(
                  "Watch how IIEVI can turn social engagement into qualified bookings automatically.",
                )}
              </h2>
              <div className="mt-8">
                <ButtonLink to="/demo" variant="primary">
                  {t("Try It Live")}
                </ButtonLink>
              </div>
            </FadeIn>
          </div>
          <div>
            <FadeIn delay={0.1}>
              <Card variant="open" className="border-signal border-2 bg-surface">
                <div className="space-y-6">
                  {data.finalStats.map((stat, i) => (
                    <div
                      key={stat.label}
                      className="flex justify-between items-end border-b border-hairline/40 pb-4 last:border-0 last:pb-0"
                    >
                      <span className="text-body-md font-mono text-stone">{t(stat.label)}</span>
                      <Counter end={stat.value} delay={i * 0.2} />
                    </div>
                  ))}
                </div>
              </Card>
            </FadeIn>
          </div>
        </div>
      </Section>

      <Rule />

      {/* Other Categories */}
      <Section>
        <FadeIn>
          <SectionLabel>{t("Also Built For")}</SectionLabel>
        </FadeIn>
        <FadeIn delay={0.05}>
          <h2 className="mt-6 font-display text-headline-lg text-ink">
            {t("Explore other categories.")}
          </h2>
        </FadeIn>
        <div className="mt-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {others.map(([k, c], i) => (
            <FadeIn key={k} delay={i * 0.05}>
              <Link
                to="/solutions/$category"
                params={{ category: k }}
                className="block h-full group"
              >
                <Card className="h-full group-hover:bg-neutral transition-colors flex flex-col">
                  <Pill>{t(c.label)}</Pill>
                  <p className="mt-6 text-body-sm text-graphite line-clamp-3 flex-1">
                    {t(c.intro)}
                  </p>
                  <p className="mt-6 font-body text-body-sm text-ink border-b border-hairline inline-block pb-0.5 self-start">
                    {t("See playbook")} →
                  </p>
                </Card>
              </Link>
            </FadeIn>
          ))}
        </div>
      </Section>

      <CTASection />
    </>
  );
}

function StepBlock({
  step,
  index,
  onInView,
}: {
  step: PlaybookStep;
  index: number;
  onInView: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { margin: "-45% 0px -45% 0px" });
  const { t } = useTranslation();

  useEffect(() => {
    if (inView) {
      onInView();
    }
  }, [inView, onInView]);

  return (
    <div
      ref={ref}
      className="relative transition-opacity duration-300"
      style={{ opacity: inView ? 1 : 0.4 }}
    >
      <div className="lg:hidden mb-4">
        <span className="text-display-xl font-display text-neutral/50 absolute -top-12 -left-4 pointer-events-none select-none z-[-1]">
          {step.stepNumber}
        </span>
      </div>
      <SectionLabel className="mb-4">
        {step.stepNumber} — {t(step.heading)}
      </SectionLabel>
      <h3 className="font-display text-headline-md text-ink mb-4">{t(step.heading)}</h3>
      <p className="text-body-md text-graphite mb-8">{t(step.description)}</p>

      <div className="bg-neutral p-6 border border-hairline mb-8 lg:mb-0">
        <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone mb-4">
          {t(step.highlightsLabel)}
        </p>
        <ul className="space-y-3">
          {step.highlights.map((h) => (
            <li key={h} className="flex items-start gap-3 text-body-sm text-ink">
              <span className="w-1.5 h-1.5 mt-2 bg-signal shrink-0" />
              <span>{t(h)}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Mobile Mockup (hidden on lg) */}
      <div className="lg:hidden mt-8 -mx-6 px-6 pb-8 border-b border-hairline border-dashed">
        <PlaybookMockup mockup={step.mockup} />
      </div>
    </div>
  );
}

// Simple counter component for the final stats
function Counter({ end, delay }: { end: number; delay: number }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });

  useEffect(() => {
    if (!inView) return;
    const start = 0;
    const duration = 2000; // ms
    const startTime = performance.now() + delay * 1000;

    let raf: number;
    const animate = (time: number) => {
      if (time < startTime) {
        raf = requestAnimationFrame(animate);
        return;
      }
      const p = Math.min(1, (time - startTime) / duration);
      // easeOutExpo
      const ease = p === 1 ? 1 : 1 - Math.pow(2, -10 * p);
      setCount(Math.floor(ease * end));
      if (p < 1) {
        raf = requestAnimationFrame(animate);
      }
    };
    raf = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf);
  }, [end, inView, delay]);

  return (
    <span
      ref={ref}
      className="text-[32px] md:text-[40px] font-display text-ink tabular-nums leading-none"
    >
      {count.toLocaleString()}
    </span>
  );
}
