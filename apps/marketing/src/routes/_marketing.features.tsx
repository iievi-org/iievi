import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import {
  MessageSquare, Calendar, Star, Bell, Users, BarChart3, Globe,
  Zap, Shield, Clock, CreditCard, Tag, FileText, Phone, Image,
  Workflow, Languages, Headphones,
  Sparkles, Palette, CalendarClock, Megaphone, Target, Percent,
  Database, GraduationCap, TrendingUp,
} from "lucide-react";

import { Container, Section } from "@/components/linen/Container";
import { Rule } from "@/components/linen/Rule";
import { Card } from "@/components/linen/Card";
import { SectionLabel } from "@/components/linen/SectionLabel";
import { FadeIn } from "@/components/linen/FadeIn";
import { CTASection } from "@/components/linen/CTASection";
import { ChatMockup } from "@/components/linen/ChatMockup";

export const Route = createFileRoute("/_marketing/features")({
  head: () => ({
    meta: [
      { title: "Features — IIEVI | AI Business Automation" },
      { name: "description", content: "Everything you need to run your service business on autopilot — lead capture, bookings, reviews, payments, and 14 more features." },
      { property: "og:title", content: "Features — IIEVI" },
      { property: "og:description", content: "18 features built to run an Global service business on WhatsApp." },
    ],
  }),
  component: FeaturesPage,
});

const features = [
  { icon: MessageSquare, name: "Social-First AI", desc: "Replies on your Social Media Platform in Customer's Language." },
  { icon: Calendar, name: "Smart Bookings", desc: "Calendar that books itself, handles reschedules, and prevents double bookings." },
  { icon: Star, name: "Review Automation", desc: "Asks for Google reviews at the perfect moment after every service." },
  { icon: Bell, name: "Auto Reminders", desc: "24h and 2h pre-appointment nudges with reschedule links." },
  { icon: Users, name: "Customer CRM", desc: "Every conversation, booking, and spend in a clean customer profile." },
  { icon: BarChart3, name: "Live Dashboard", desc: "Revenue, leads, conversions, and AI performance — real time." },
  { icon: Globe, name: "Hindi + English + Hinglish", desc: "Native fluency across India's three default conversation languages." },
  { icon: Zap, name: "3-Second Response", desc: "Median first-reply time of 3 seconds, 24×7×365." },
  { icon: Shield, name: "Hand-off to Human", desc: "AI knows when to escalate — you take over mid-thread with full context." },
  { icon: Clock, name: "Out-of-Hours Cover", desc: "Confirms, books, and qualifies even when you're closed." },
  { icon: CreditCard, name: "UPI + Razorpay Pay", desc: "Take deposits or full payments inside the WhatsApp thread." },
  { icon: Tag, name: "Offers & Upsells", desc: "Conversational upsells trained on what your top-spenders buy." },
  { icon: FileText, name: "Quotes & Invoices", desc: "Send PDF quotes and GST invoices without leaving WhatsApp." },
  { icon: Phone, name: "Missed Call to Chat", desc: "Auto-replies on WhatsApp the moment a customer rings and hangs up." },
  { icon: Image, name: "Photo & Voice Notes", desc: "AI understands customer photos and voice messages — replies in kind." },
  { icon: Workflow, name: "Custom Workflows", desc: "Drag-build flows for onboarding, refunds, complaints, or anything." },
  { icon: Languages, name: "Brand Voice Training", desc: "Sounds like you, not a bot. Upload your past chats to train it." },
  { icon: Headphones, name: "Global Support", desc: "Phone, chat, and onsite training — from Mumbai, Bangalore, Delhi." },
  { icon: Palette, name: "Canva-Native Posts", desc: "Generate brand-perfect Canva designs from a one-line chat prompt." },
  { icon: Sparkles, name: "Multi-AI Tools", desc: "Best-of image, copy, and video models — picked per post, billed transparently." },
  { icon: CalendarClock, name: "One-Click Scheduling", desc: "Meta, Instagram, LinkedIn, TikTok — scheduled across all four in one go." },
  { icon: Megaphone, name: "Week-Long Campaigns", desc: "Describe a campaign once; we plan, draft, schedule, and report on the full week." },
  { icon: Target, name: "Budget & Targeting in Chat", desc: "Set ad spend, audiences, service packages, and locations — all conversationally." },
  { icon: Percent, name: "AI Booking Discounts", desc: "Auto-applied, time-sensitive discounts that close hesitant bookings in one reply." },
  { icon: TrendingUp, name: "CPL & CPC Analytics", desc: "Cost per lead, cost per conversion, AI tools spend — surfaced live, per channel." },
  { icon: Database, name: "Per-Tenant Data Isolation", desc: "Your leads and chats live in a dedicated tenant. No shared model training. Ever." },
  { icon: GraduationCap, name: "Comprehensive Onboarding", desc: "48-hour structured training programme on your menu, voice, policies, and FAQs." },
];



const integrations = [
  "WhatsApp Business", "Razorpay", "Google Calendar", "Justdial",
  "Practo", "Instagram", "Google My Business", "Stripe", "Zoho", "Tally",
];

function FeaturesPage() {
  const { t } = useTranslation();
  return (
    <>
      <Container>
        <div className="pt-16 md:pt-24 pb-12">
          <FadeIn><SectionLabel>{t("Features")}</SectionLabel></FadeIn>
          <FadeIn delay={0.05}>
            <h1 className="mt-6 font-display text-[44px] md:text-display-lg text-ink leading-[0.96] tracking-[-0.005em]">
              {t("Everything you need to run")}<br />{t("your business on autopilot.")}
            </h1>
          </FadeIn>
          <FadeIn delay={0.1}>
            <p className="mt-8 max-w-2xl text-body-md text-graphite">
              {t("Eighteen features. One WhatsApp number. No app to install, no staff training, no migration weekend. Turn it on and your business starts running itself.")}
            </p>
          </FadeIn>
        </div>
        <FadeIn delay={0.15}>
          <div className="border border-hairline bg-neutral aspect-[16/9] flex items-center justify-center">
            <ChatMockup
              title="Live conversation — Apollo Clinic"
              messages={[
                { from: "user", text: "Need to book a dermatologist consultation", time: "14:02" },
                { from: "ai", text: "Skin or hair concern? And which clinic — HSR or Indiranagar?", time: "14:02" },
                { from: "user", text: "Skin, HSR", time: "14:03" },
                { from: "ai", text: "Dr. Anjali Rao has 11:30 AM tomorrow or 5 PM today. Both are ₹600 + ₹50 booking. Which works?", time: "14:03" },
                { from: "user", text: "5 PM today", time: "14:03" },
                { from: "ai", text: "Booked ✓ Payment link: rzp.io/iievi/AX2 — see you at 5 PM today, HSR.", time: "14:03" },
              ]}
              className="m-8 w-[80%]"
            />
          </div>
        </FadeIn>
      </Container>

      <Section>
        <FadeIn><SectionLabel>{t("The Full Stack")}</SectionLabel></FadeIn>
        <div className="mt-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-hairline border border-hairline">
          {features.map((f) => (
            <div key={f.name} className="bg-surface p-8 hover:bg-neutral transition-colors border-t-2 border-t-signal/0 hover:border-t-signal">
              <f.icon size={24} className="text-signal" strokeWidth={1.5} />
              <h3 className="mt-6 font-body text-headline-sm font-medium text-ink">{f.name}</h3>
              <p className="mt-3 text-body-sm text-graphite">{f.desc}</p>
            </div>
          ))}
        </div>
      </Section>

      <Rule />

      <Section>
        <FadeIn><SectionLabel>{t("Integrates With")}</SectionLabel></FadeIn>
        <FadeIn delay={0.05}>
          <h2 className="mt-6 font-display text-headline-lg text-ink max-w-3xl">
            {t("Works with the tools you already use.")}
          </h2>
        </FadeIn>
        <div className="mt-12 flex flex-wrap items-center">
          {integrations.map((n, i) => (
            <div
              key={n}
              className={`px-6 py-4 ${i < integrations.length - 1 ? "border-r border-hairline" : ""}`}
            >
              <span className="font-display font-bold text-headline-sm text-stone hover:text-ink transition-colors cursor-default">
                {n}
              </span>
            </div>
          ))}
        </div>
      </Section>

      <CTASection />
    </>
  );
}

// Card unused but reserved for future tiles
void Card;
