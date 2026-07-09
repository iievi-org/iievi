import { useState } from "react";
import { useTranslation } from "react-i18next";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Search, Zap, CreditCard, MessageSquare, Shield, Settings, Users, ChevronRight } from "lucide-react";
import { Container, Section } from "@/components/linen/Container";
import { Rule } from "@/components/linen/Rule";
import { SectionLabel } from "@/components/linen/SectionLabel";
import { FadeIn } from "@/components/linen/FadeIn";

export const Route = createFileRoute("/_marketing/help")({
  head: () => ({
    meta: [
      { title: "Help Center — IIEVI" },
      { name: "description", content: "Guides, troubleshooting, and answers for using IIEVI." },
      { property: "og:title", content: "Help Center — IIEVI" },
      { property: "og:description", content: "Find guides and answers." },
    ],
  }),
  component: HelpPage,
});

const LOREM = `Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Curabitur pretium tincidunt lacus. Nulla gravida orci a odio. Nullam varius, turpis et commodo pharetra, est eros bibendum elit, nec luctus magna felis sollicitudin mauris. Integer in mauris eu nibh euismod gravida. Duis ac tellus et risus vulputate vehicula.`;

const WIKI_DATA = [
  {
    category: "Getting started",
    icon: Zap,
    articles: [
      { id: "gs-1", title: "Quickstart Guide", content: LOREM },
      { id: "gs-2", title: "Connecting WhatsApp", content: LOREM },
      { id: "gs-3", title: "Inviting Team Members", content: LOREM },
    ]
  },
  {
    category: "Conversations & AI",
    icon: MessageSquare,
    articles: [
      { id: "ai-1", title: "How the AI works", content: LOREM },
      { id: "ai-2", title: "Training your assistant", content: LOREM },
      { id: "ai-3", title: "Handling escalations", content: LOREM },
    ]
  },
  {
    category: "Billing & invoices",
    icon: CreditCard,
    articles: [
      { id: "bill-1", title: "Understanding your invoice", content: LOREM },
      { id: "bill-2", title: "Payment methods", content: LOREM },
    ]
  },
  {
    category: "Settings & integrations",
    icon: Settings,
    articles: [
      { id: "set-1", title: "General Settings", content: LOREM },
      { id: "set-2", title: "CRM Integrations", content: LOREM },
    ]
  },
  {
    category: "Security & privacy",
    icon: Shield,
    articles: [
      { id: "sec-1", title: "Data Isolation", content: LOREM },
      { id: "sec-2", title: "Compliance", content: LOREM },
    ]
  },
  {
    category: "Team & permissions",
    icon: Users,
    articles: [
      { id: "team-1", title: "Roles and access", content: LOREM },
      { id: "team-2", title: "Activity logs", content: LOREM },
    ]
  },
];

function HelpPage() {
  const { t } = useTranslation();
  const [activeArticleId, setActiveArticleId] = useState(WIKI_DATA[0].articles[0].id);

  const flatArticles = WIKI_DATA.flatMap(c => c.articles);
  const currentIndex = flatArticles.findIndex(a => a.id === activeArticleId);
  
  const previousArticle = currentIndex > 0 ? flatArticles.at(currentIndex - 1) : null;
  const nextArticle = currentIndex >= 0 && currentIndex < flatArticles.length - 1 ? flatArticles.at(currentIndex + 1) : null;

  const activeCategory = WIKI_DATA.find(c => c.articles.some(a => a.id === activeArticleId));
  const activeArticle = activeCategory?.articles.find(a => a.id === activeArticleId);

  return (
    <>
      <Container>
        <div className="pt-16 md:pt-24 pb-12 max-w-3xl">
          <FadeIn><SectionLabel>{t("How can we help you?")}</SectionLabel></FadeIn>
          <FadeIn delay={0.05}>
            <h1 className="mt-6 font-display text-[44px] md:text-display-lg text-ink leading-[0.96]">
              {t("Help Center")}
            </h1>
          </FadeIn>
          <FadeIn delay={0.1}>
            <div className="mt-12 relative">
              <input
                type="text"
                placeholder="Search guides, troubleshooting, billing…"
                className="w-full bg-transparent border-0 border-t border-b border-hairline px-0 py-5 pr-10 font-body text-body-md text-ink placeholder:text-stone focus:outline-none focus:border-b-2 focus:border-b-signal"
              />
              <Search size={20} className="absolute right-2 top-1/2 -translate-y-1/2 text-stone" strokeWidth={1.5} />
            </div>
          </FadeIn>
        </div>
      </Container>

      <Rule />

      <Section>
        <div className="flex flex-col lg:flex-row gap-12 lg:gap-24 relative">
          
          {/* Sidebar */}
          <div className="w-full lg:w-[320px] shrink-0">
            <div className="lg:sticky lg:top-32 space-y-8">
              {WIKI_DATA.map((category) => (
                <div key={category.category}>
                  <div className="flex items-center gap-3 mb-4">
                    <category.icon size={18} className="text-signal" strokeWidth={2} />
                    <h3 className="font-display text-headline-sm text-ink">{category.category}</h3>
                  </div>
                  <ul className="space-y-3 pl-7 border-l border-hairline ml-[9px]">
                    {category.articles.map((article) => {
                      const isActive = article.id === activeArticleId;
                      return (
                        <li key={article.id}>
                          <button
                            onClick={() => {
                              setActiveArticleId(article.id);
                              window.scrollTo({ top: 0, behavior: "smooth" });
                            }}
                            className={`text-left w-full text-body-sm transition-colors duration-200 ${
                              isActive ? "text-signal font-medium" : "text-graphite hover:text-ink"
                            }`}
                          >
                            {article.title}
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ))}
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 max-w-[720px] min-h-[60vh]">
            {activeArticle && activeCategory && (
              <FadeIn key={activeArticle.id}>
                <div className="flex items-center gap-2 text-mono-sm font-mono text-stone uppercase tracking-[0.04em] mb-6">
                  <span>{activeCategory.category}</span>
                  <ChevronRight size={14} />
                  <span className="text-ink">{activeArticle.title}</span>
                </div>
                
                <h2 className="font-display text-headline-lg text-ink mb-8">
                  {activeArticle.title}
                </h2>
                
                <div className="text-body-md text-graphite leading-[1.7] space-y-6">
                  {activeArticle.content.split('\n\n').map((paragraph, idx) => (
                    <p key={idx}>{paragraph}</p>
                  ))}
                  
                  {/* Sample sequential structure placeholder inside the article */}
                  <div className="my-10 p-6 bg-neutral border border-hairline">
                    <h4 className="font-display text-headline-sm text-ink mb-4">{t("In this guide")}</h4>
                    <ol className="list-decimal list-inside space-y-2 text-body-sm text-graphite">
                      <li>{t("Introduction and prerequisites")}</li>
                      <li>{t("Step-by-step configuration")}</li>
                      <li>{t("Testing your setup")}</li>
                      <li>{t("Troubleshooting common issues")}</li>
                    </ol>
                  </div>
                </div>
                
                {/* Navigation Footer */}
                <div className="mt-16 pt-8 border-t border-hairline flex items-center justify-between">
                  {previousArticle ? (
                    <button 
                      onClick={() => {
                        setActiveArticleId(previousArticle.id);
                        window.scrollTo({ top: 0, behavior: "smooth" });
                      }}
                      className="text-body-sm text-graphite hover:text-ink transition-colors flex items-center gap-2 text-left"
                    >
                      &larr; <span className="underline underline-offset-4 decoration-hairline">{previousArticle.title}</span>
                    </button>
                  ) : (
                    <div />
                  )}
                  {nextArticle ? (
                    <button 
                      onClick={() => {
                        setActiveArticleId(nextArticle.id);
                        window.scrollTo({ top: 0, behavior: "smooth" });
                      }}
                      className="text-body-sm text-graphite hover:text-ink transition-colors flex items-center gap-2 text-right"
                    >
                      <span className="underline underline-offset-4 decoration-hairline">{nextArticle.title}</span> &rarr;
                    </button>
                  ) : (
                    <div />
                  )}
                </div>
              </FadeIn>
            )}
          </div>

        </div>
      </Section>
    </>
  );
}
