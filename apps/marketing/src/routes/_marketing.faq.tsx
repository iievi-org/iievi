import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Search } from "lucide-react";
import { Container, Section } from "@/components/linen/Container";
import { Rule } from "@/components/linen/Rule";
import { Tabs } from "@/components/linen/Tabs";
import { Accordion } from "@/components/linen/Accordion";
import { SectionLabel } from "@/components/linen/SectionLabel";
import { FadeIn } from "@/components/linen/FadeIn";
import { CTASection } from "@/components/linen/CTASection";

export const Route = createFileRoute("/_marketing/faq")({
  head: () => ({
    meta: [
      { title: "FAQ — IIEVI" },
      {
        name: "description",
        content:
          "Answers to the most common questions about IIEVI — setup, pricing, AI, security, and support.",
      },
      { property: "og:title", content: "FAQ — IIEVI" },
      { property: "og:description", content: "Common questions answered." },
    ],
  }),
  component: FAQPage,
});

const CATS = {
  getting: {
    label: "Getting Started",
    faqs: [
      {
        question: "How long does setup take?",
        answer:
          "About 5 minutes. Connect your WhatsApp Business number, upload your menu or service list, set your business hours. You're live.",
      },
      {
        question: "Do I need a new phone number?",
        answer:
          "No. IIEVI works on your existing WhatsApp Business number. Your customers see no change.",
      },
      {
        question: "Will it sound like a bot?",
        answer:
          "No. We train on your past chats, your voice, your menu. Most customers don't realise they're talking to an AI.",
      },
      {
        question: "What languages does it support?",
        answer:
          "Hindi, English, and Hinglish natively. Tamil, Telugu, Kannada, Bengali, Marathi, and Gujarati on Growth and above.",
      },
    ],
  },
  ai: {
    label: "AI & Accuracy",
    faqs: [
      {
        question: "What happens if the AI doesn't know an answer?",
        answer:
          "It hands the thread to you with full context. You can take over from your phone, reply, and hand back — IIEVI learns from your reply.",
      },
      {
        question: "Can I review what the AI is saying?",
        answer:
          "Yes. Every conversation is visible in your dashboard. You can edit replies, set guardrails, and approve high-stakes flows like refunds.",
      },
      {
        question: "Does the AI improve over time?",
        answer:
          "Yes — within your account only. We never train models on your customer data across accounts.",
      },
    ],
  },
  pricing: {
    label: "Pricing & Billing",
    faqs: [
      { question: "Is there a free trial?", answer: "14 days, full Growth plan, no credit card." },
      {
        question: "Can I cancel anytime?",
        answer: "Yes. No lock-in. Annual plans get a pro-rated refund.",
      },
      {
        question: "Do you support GST invoicing?",
        answer: "Yes — every invoice is GST-compliant. Add your GSTIN in settings.",
      },
    ],
  },
  security: {
    label: "Security & Privacy",
    faqs: [
      {
        question: "Where is my data stored?",
        answer:
          "On Global servers in Mumbai and Hyderabad. We're ISO 27001 certified and DPDP compliant.",
      },
      {
        question: "Do you sell or share customer data?",
        answer:
          "Never. We don't share customer data with anyone, and we don't train cross-account models on your conversations.",
      },
      {
        question: "What about WhatsApp compliance?",
        answer:
          "We're a Meta Business Partner. All messaging follows WhatsApp Business API policy.",
      },
    ],
  },
  support: {
    label: "Support",
    faqs: [
      {
        question: "How do I reach support?",
        answer:
          "Email on Starter, phone and chat on Growth, dedicated success manager on Scale. Global business hours, IST.",
      },
      {
        question: "Do you do onsite onboarding?",
        answer:
          "Included on Scale plan, optional add-on on Growth. Available in Mumbai, Bangalore, Delhi, Pune, Hyderabad, and Chennai.",
      },
    ],
  },
};

function FAQPage() {
  const [tab, setTab] = useState<keyof typeof CATS>("getting");

  return (
    <>
      <Container>
        <div className="pt-16 md:pt-24 pb-12 max-w-3xl">
          <FadeIn>
            <SectionLabel>Help</SectionLabel>
          </FadeIn>
          <FadeIn delay={0.05}>
            <h1 className="mt-6 font-display text-[44px] md:text-display-lg text-ink leading-[0.96]">
              Frequently asked, plainly answered.
            </h1>
          </FadeIn>
          <FadeIn delay={0.1}>
            <div className="mt-12 relative">
              <input
                type="text"
                placeholder="Search answers…"
                className="w-full bg-transparent border-0 border-t border-b border-hairline px-0 py-4 pr-10 font-body text-body-md text-ink placeholder:text-stone focus:outline-none focus:border-b-2 focus:border-b-signal"
              />
              <Search
                size={18}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-stone"
                strokeWidth={1.5}
              />
            </div>
          </FadeIn>
        </div>
      </Container>

      <Rule />
      <Container>
        <div className="py-6 overflow-x-auto">
          <Tabs
            value={tab}
            onChange={(v) => setTab(v as keyof typeof CATS)}
            options={Object.entries(CATS).map(([k, v]) => ({ value: k, label: v.label }))}
          />
        </div>
      </Container>
      <Rule />

      <Section>
        <div className="max-w-3xl">
          <Accordion items={CATS[tab].faqs} />
        </div>
      </Section>

      <CTASection />
    </>
  );
}
