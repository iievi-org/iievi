import { createFileRoute, Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { Container, Section } from "@/components/linen/Container";
import { Rule } from "@/components/linen/Rule";
import { Pill } from "@/components/linen/Pill";
import { Card } from "@/components/linen/Card";
import { FadeIn } from "@/components/linen/FadeIn";
import { CTASection } from "@/components/linen/CTASection";
import { SOLUTION_CATEGORIES } from "@/lib/solutionPlaybookData";
import { ArrowRight } from "lucide-react";

export const Route = createFileRoute("/_marketing/solutions/")({
  head: () => ({
    meta: [
      { title: "Solutions — IIEVI" },
      { name: "description", content: "Industry-specific AI automation playbooks." },
      { property: "og:title", content: "Solutions on IIEVI" },
      { property: "og:description", content: "Industry-specific AI automation playbooks." },
    ],
  }),
  component: SolutionsLandingPage,
});

function SolutionsLandingPage() {
  const { t } = useTranslation();

  return (
    <>
      {/* HERO */}
      <Container>
        <div className="pt-16 md:pt-24 pb-16 md:pb-24 max-w-4xl">
          <FadeIn>
            <Pill>{t("Playbooks")}</Pill>
          </FadeIn>
          <FadeIn delay={0.05}>
            <h1 className="mt-8 font-display text-[56px] md:text-display-lg text-ink leading-[0.96]">
              {t("What problems do we solve?")}
            </h1>
          </FadeIn>
          <FadeIn delay={0.1}>
            <p className="mt-8 text-body-md text-graphite max-w-2xl">
              {t(
                "Every service business has unique challenges, but the core problems are the same: lost leads, missed follow-ups, and empty calendars. Explore our industry-specific playbooks to see how IIEVI solves them.",
              )}
            </p>
          </FadeIn>
        </div>
      </Container>

      <Rule />

      {/* CATEGORY GRID */}
      <Section inset>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Object.entries(SOLUTION_CATEGORIES).map(([slug, data], index) => (
            <FadeIn key={slug} delay={index * 0.05}>
              <Link
                to="/solutions/$category"
                params={{ category: slug }}
                className="block h-full group"
              >
                <Card
                  variant="paper"
                  className="h-full flex flex-col hover:border-signal transition-colors"
                >
                  <Pill variant="outline">{t(data.label)}</Pill>
                  <h3 className="mt-6 font-display text-headline-sm text-ink group-hover:text-signal transition-colors">
                    {t(data.headline)}
                  </h3>
                  <p className="mt-4 text-body-sm text-graphite flex-1 line-clamp-3">
                    {t(data.intro)}
                  </p>
                  <div className="mt-8 pt-4 border-t border-hairline flex items-center justify-between font-mono text-mono-sm uppercase tracking-[0.14em] text-ink">
                    <span>{t("See Playbook")}</span>
                    <ArrowRight
                      size={14}
                      className="group-hover:translate-x-1 transition-transform"
                    />
                  </div>
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
