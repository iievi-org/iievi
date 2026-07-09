import { createFileRoute, Link } from "@tanstack/react-router";
import { Play, Star, AlertTriangle, ArrowRight, Minus, Check, Sparkles, CalendarClock, RefreshCw, Lock, ShieldCheck, Database, MapPin, GraduationCap } from "lucide-react";
import { Container, Section } from "@/components/linen/Container";
import { Rule } from "@/components/linen/Rule";
import { Pill } from "@/components/linen/Pill";
import { Button, ButtonLink } from "@/components/linen/Button";
import { Card } from "@/components/linen/Card";
import { SectionLabel } from "@/components/linen/SectionLabel";
import { Stat } from "@/components/linen/Stat";
import { FadeIn } from "@/components/linen/FadeIn";
import { CTASection } from "@/components/linen/CTASection";
import { ChatMockup } from "@/components/linen/ChatMockup";
import { DashboardMockup } from "@/components/linen/DashboardMockup";
import { GeneratingPostMockup } from "@/components/linen/GeneratingPostMockup";
import { SOLUTION_CATEGORIES, type PlaybookStep } from "@/lib/solutionPlaybookData";
import { PlaybookMockup } from "@/components/linen/PlaybookMockup";
import { PlaybookProgress } from "@/components/linen/PlaybookProgress";
import { useRef, useState, useEffect } from "react";
import { useInView } from "framer-motion";
import { useTranslation } from "react-i18next";


export const Route = createFileRoute("/_marketing/")({
  head: () => ({
    meta: [
      { title: "IIEVI — One Chat. Every Business Task." },
      {
        name: "description",
        content:
          "Social-First AI automation for Global service businesses. Capture leads, book appointments, and follow up — automatically.",
      },
      { property: "og:title", content: "IIEVI — One Chat. Every Business Task." },
      {
        property: "og:description",
        content: "Social-First AI automation for Global service businesses.",
      },
    ],
  }),
  component: Home,
});

const businesses = [
  "Lakme Salon",
  "Apollo Clinic",
  "Bombay Shaving",
  "Urban Plumbers",
  "Truefitt & Hill",
  "PetVille",
  "Studio11",
  "FitSpace",
];

const painPoints = [
  {
    title: "Leads ghost you within minutes",
    body:
      "67% of customers go to your competitor if you don't reply in 5 minutes. At 2 AM, on Diwali, during a haircut — you can't always reply.",
  },
  {
    title: "Bookings live in three places",
    body:
      "WhatsApp, Instagram DMs, phone calls — and a notebook at the counter. Double bookings and no-shows are eating your margin.",
  },
  {
    title: "Reviews never get asked for",
    body:
      "You delivered great service. You forgot to ask for a Google review. Your competitor with 4.2★ is outranking you on Maps.",
  },
  {
    title: "Posting on 4 platforms is a full-time job",
    body:
      "Instagram, Meta, LinkedIn, TikTok — each needs its own copy, its own image, its own time. Most weeks, nothing goes out.",
  },
];


const steps = [
  {
    n: "01",
    title: "Register with IIEVA",
    body: "Create your account in minutes, choose your plan, and access a complete AI-powered growth platform built for modern businesses.",
  },
  {
    n: "02",
    title: "Create your business profile",
    body: "Define your brand identity, upload your services, menu, pricing, FAQs, policies, business hours, locations, and customer information to train your AI agents.",
  },
  {
    n: "03",
    title: "Connect your tools",
    body: "Securely connect AI providers, social media accounts, WhatsApp Business, payment gateways, calendars, CRMs, email providers, and other business applications using API integrations.",
  },
  {
    n: "04",
    title: "Generate content with AI",
    body: "Create high-converting posts, images, videos, promotions, offers, and marketing campaigns tailored to your industry, audience, and business goals.",
  },
  {
    n: "05",
    title: "Launch and manage campaigns",
    body: "Publish content across multiple channels, boost campaigns, define target audiences, schedule posts, allocate budgets, and monitor campaign performance from one dashboard.",
  },
  {
    n: "06",
    title: "Capture and qualify leads",
    body: "AI agents engage visitors instantly, answer questions, collect requirements, qualify prospects, and move high-intent leads into your sales pipeline automatically.",
  },
  {
    n: "07",
    title: "AI closes the conversation",
    body: "From estimates and recommendations to discounts, bookings, appointments, payments, and confirmations, AI handles the entire customer journey end-to-end.",
  },
  {
    n: "08",
    title: "Follow-ups happen automatically",
    body: "Manage your calendar inside IIEVA while automated reminders, confirmations, review requests, upsell opportunities, and customer updates are delivered through email, WhatsApp, and social channels.",
  },
  {
    n: "09",
    title: "See the revenue grow",
    body: "Track leads, conversations, bookings, campaign performance, conversion rates, customer lifetime value, and revenue through real-time analytics and business intelligence dashboards.",
  },
];


const features = [
  {
    label: "Lead Capture",
    title: "Reply in 3 seconds, every time",
    bullets: [
      "Instant first response — never miss a lead at 2 AM",
      "Qualifies budget, location, and service interest",
      "Hands warm leads to you with full context",
    ],
    cta: "How lead capture works",
  },
  {
    label: "Smart Bookings",
    title: "Calendar that books itself",
    bullets: [
      "Syncs with Google Calendar and your staff schedules",
      "Handles reschedules and cancellations conversationally",
      "Auto-sends reminders 24h and 2h before the slot",
    ],
    cta: "See booking flow",
  },
  {
    label: "Review Engine",
    title: "Your 5-star reviews, on autopilot",
    bullets: [
      "Asks for reviews at the perfect moment after service",
      "One-tap link to Google, Justdial, and Practo",
      "Handles unhappy customers privately before they post",
    ],
    cta: "Grow your rating",
  },
];

const testimonials = [
  {
    quote:
      "We were losing 40 leads a week to slow replies. IIEVI books 60% of them automatically now. ROI in week one.",
    name: "Priya Mehta",
    business: "Glow Salon, Bandra",
    featured: false,
  },
  {
    quote:
      "I used to spend 3 hours every evening replying on WhatsApp. Now I do zero. The AI sounds exactly like me.",
    name: "Dr. Rajesh Kumar",
    business: "Dental Care Clinic, Indiranagar",
    featured: true,
  },
  {
    quote:
      "Our Google rating went from 3.8 to 4.7 in two months. The review automation just works.",
    name: "Arjun Patel",
    business: "Patel Auto Service, Ahmedabad",
    featured: false,
  },
];

function Home() {
  const { t } = useTranslation();
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const genericPlaybook = SOLUTION_CATEGORIES["pet-wellness"].playbook;

  return (
    <>
      {/* HERO */}
      <Container>
        <div className="pt-16 md:pt-24 pb-16 md:pb-20 grid grid-cols-1 lg:grid-cols-12 gap-12 items-end">
          <div className="lg:col-span-7">
            <FadeIn>
              <Pill>● Now available for Global service businesses</Pill>
            </FadeIn>
            <FadeIn delay={0.05}>
              <h1 className="mt-8 font-display text-[64px] md:text-display-lg text-ink leading-[0.96] tracking-[-0.005em]">
                One Chat.
                <br />
                Every Business Task.
              </h1>
            </FadeIn>
            <FadeIn delay={0.1}>
              <p className="mt-8 text-body-md text-graphite max-w-xl">
                IIEVI is the Social-First AI that captures every lead, books every appointment,
                and follows up with every customer — automatically. Built for Global salons,
                clinics, and service businesses.
              </p>
            </FadeIn>
            <FadeIn delay={0.15}>
              <div className="mt-10 flex flex-wrap gap-4">
                <ButtonLink to="/register" variant="primary">Get Started Free</ButtonLink>
                <ButtonLink to="/demo" variant="ghost">
                  <Play size={14} strokeWidth={1.5} /> Watch Demo
                </ButtonLink>
              </div>
            </FadeIn>
            <FadeIn delay={0.2}>
              <div className="mt-10 flex items-center gap-4">
                <div className="flex -space-x-2">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div
                      key={i}
                      className="w-8 h-8 rounded-full border border-hairline bg-neutral"
                      style={{
                        background: `linear-gradient(135deg, hsl(${i * 47}, 30%, 75%), hsl(${i * 47 + 30}, 25%, 65%))`,
                      }}
                    />
                  ))}
                </div>
                <div className="flex flex-col">
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <Star key={i} size={12} className="fill-ink text-ink" />
                    ))}
                  </div>
                  <p className="font-mono text-mono-sm text-stone mt-1">
                    Trusted by 2,400+ Global service businesses
                  </p>
                </div>
              </div>
            </FadeIn>
          </div>

          <div className="lg:col-span-5">
            <FadeIn delay={0.25}>
              <DashboardMockup />
              <Card variant="paper" className="mt-6 p-6 border-l-2 border-l-signal">
                <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
                  Latest from the feed
                </p>
                <p className="mt-2 text-body-sm text-ink">
                  Reema · Hair Colour · Tomorrow 4:00 PM with Priya · ₹2,800
                </p>
              </Card>
            </FadeIn>
          </div>

        </div>
      </Container>

      <Rule />

      {/* LOGO BAR */}
      <Container>
        <div className="py-10 flex flex-col md:flex-row items-center gap-8">
          <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone shrink-0">
            Businesses growing with IIEVI
          </p>
          <div className="overflow-hidden flex-1 relative">
            <div className="flex gap-12 linen-marquee w-max">
              {[...businesses, ...businesses].map((b, i) => (
                <span
                  key={i}
                  className="font-display font-bold text-headline-sm text-graphite whitespace-nowrap"
                >
                  {b}
                </span>
              ))}
            </div>
          </div>
        </div>
      </Container>

      <Rule />

      {/* PAIN POINTS */}
      <Section inset>
        <FadeIn>
          <SectionLabel>The Problem</SectionLabel>
          <h2 className="mt-6 font-display text-[36px] md:text-headline-lg text-ink max-w-3xl">
            Every lead you miss is money your competitor made.
          </h2>
        </FadeIn>
        <div className="mt-14 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {painPoints.map((p, i) => (

            <FadeIn key={p.title} delay={i * 0.06}>
              <Card className="border-t-2 border-t-signal h-full">
                <AlertTriangle size={24} className="text-signal" strokeWidth={1.5} />
                <h3 className="mt-6 font-display text-headline-md text-ink">{p.title}</h3>
                <p className="mt-4 text-body-sm text-graphite">{p.body}</p>
              </Card>
            </FadeIn>
          ))}
        </div>
        <FadeIn delay={0.2}>
          <p className="mt-14 font-display text-headline-md text-ink max-w-2xl">
            IIEVI handles all four. Automatically.

          </p>
        </FadeIn>
      </Section>

      <Rule />

      {/* HOW IT WORKS */}
      <Section>
        <FadeIn>
          <SectionLabel>How It Works</SectionLabel>
          <h2 className="mt-6 font-display text-[36px] md:text-headline-lg text-ink max-w-3xl">
            Six steps from sign-up to your first automated booking.
          </h2>
        </FadeIn>
        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-16">
          {steps.map((s, i) => (
            <FadeIn key={s.n} delay={i * 0.05}>
              <div className="relative">
                <span
                  aria-hidden
                  className="absolute -top-8 -left-2 font-display font-bold text-[120px] leading-none text-neutral pointer-events-none select-none"
                >
                  {s.n}
                </span>
                <div className="relative pt-4">
                  <p className="font-mono text-mono-sm text-stone uppercase tracking-[0.14em]">Step {s.n}</p>
                  <h3 className="mt-3 font-display text-headline-md text-ink">{s.title}</h3>
                  <p className="mt-3 text-body-sm text-graphite">{s.body}</p>
                </div>
              </div>
            </FadeIn>
          ))}
        </div>
      </Section>

      <Rule />

      {/* AI MARKETING DEPARTMENT */}


      {/* OPERATING METRICS */}
      <Section inset>
        <FadeIn>
          <SectionLabel>{t("Operating Metrics")}</SectionLabel>
          <h2 className="mt-6 font-display text-[36px] md:text-headline-lg text-ink max-w-3xl">
            {t("Know what every rupee returns.")}
          </h2>
          <p className="mt-6 max-w-2xl text-body-md text-graphite">
            {t("One dashboard for clients reached, conversations started, AI tools spend, cost per lead, cost per conversion, in-platform chats — and the AI booking discounts that close them faster.")}
          </p>
        </FadeIn>
        <div className="mt-14 grid grid-cols-2 md:grid-cols-3 gap-x-8 gap-y-10">
          <FadeIn delay={0.04}><Stat value="48,200" label="Clients reached / mo" /></FadeIn>
          <FadeIn delay={0.08}><Stat value="6,140" label="Conversations started" /></FadeIn>
          <FadeIn delay={0.12}><Stat value="₹94" label="Cost per lead" /></FadeIn>
          <FadeIn delay={0.16}><Stat value="₹312" label="Cost per conversion" /></FadeIn>
          <FadeIn delay={0.20}><Stat value="₹7,400" label="AI tools spend / mo" /></FadeIn>
          <FadeIn delay={0.24}><Stat value="11,820" label="In-platform chats" /></FadeIn>
        </div>
      </Section>

      <Rule />

      {/* DATA ISOLATION */}
      <Section>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          <div className="lg:col-span-7">
            <FadeIn>
              <SectionLabel>Data Isolation</SectionLabel>
              <h2 className="mt-6 font-display text-[36px] md:text-headline-lg text-ink">
                Your data stays yours. Always.
              </h2>
              <p className="mt-6 max-w-xl text-body-md text-graphite">
                Every business runs in its own isolated tenant. Your leads, your conversations,
                your campaign performance — never pooled, never used to train shared models,
                never visible to anyone outside your team.
              </p>
              <p className="mt-4 max-w-xl text-body-md text-graphite">
                We hold ourselves to the strictest data-isolation standard so that competing
                businesses on IIEVI can't see — and can never benefit from — each other's
                customers.
              </p>
            </FadeIn>
          </div>
          <div className="lg:col-span-5">
            <FadeIn delay={0.1}>
              <Card variant="paper" className="p-0">
                {[
                  { icon: Database, label: "Tenant-isolated database", body: "Per-business schema, encrypted keys, no cross-reads." },
                  { icon: Lock, label: "Encrypted at rest & in transit", body: "AES-256 + TLS 1.3 across every surface." },
                  { icon: ShieldCheck, label: "No cross-tenant model training", body: "We never train shared models on your conversations." },
                  { icon: MapPin, label: "Region-pinned in India", body: "Hosted in Mumbai. DPDP-compliant by design." },
                ].map((row, i, arr) => (
                  <div
                    key={row.label}
                    className={`flex gap-4 px-6 py-5 ${i < arr.length - 1 ? "border-b border-hairline" : ""}`}
                  >
                    <row.icon size={18} className="text-signal mt-0.5 shrink-0" strokeWidth={1.5} />
                    <div>
                      <p className="font-body text-body-sm text-ink font-medium">{row.label}</p>
                      <p className="mt-1 text-body-sm text-graphite">{row.body}</p>
                    </div>
                  </div>
                ))}
              </Card>
            </FadeIn>
          </div>
        </div>
      </Section>

      <Rule />

      {/* ONBOARDING */}
      <Section inset>
        <FadeIn>
          <SectionLabel>Onboarding</SectionLabel>
          <h2 className="mt-6 font-display text-[36px] md:text-headline-lg text-ink max-w-3xl">
            Trained on your business in 48 hours.
          </h2>
          <p className="mt-6 max-w-2xl text-body-md text-graphite">
            A comprehensive onboarding programme that teaches IIEVI your menu, your voice,
            your policies, and your customers — before you ever go live.
          </p>
        </FadeIn>
        <div className="mt-14 grid grid-cols-1 md:grid-cols-4 gap-px bg-hairline border border-hairline">
          {[
            { n: "01", t: "Menu & pricing", d: "Upload your full service list, packages, GST, and seasonal rates." },
            { n: "02", t: "Voice & tone", d: "Paste 50 past chats. We learn how you greet, joke, escalate, and close." },
            { n: "03", t: "Policies & FAQs", d: "Cancellation, refunds, deposits, escalation paths — encoded once." },
            { n: "04", t: "Go-live review", d: "We run 100 synthetic conversations with you before flipping the switch." },
          ].map((s) => (
            <div key={s.n} className="bg-neutral p-8">
              <GraduationCap size={20} className="text-signal" strokeWidth={1.5} />
              <p className="mt-6 font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">Step {s.n}</p>
              <h3 className="mt-2 font-display text-headline-sm text-ink">{s.t}</h3>
              <p className="mt-3 text-body-sm text-graphite">{s.d}</p>
            </div>
          ))}
        </div>
      </Section>

      <Rule />

      {/* FEATURES */}
      <Section>

        <FadeIn>
          <SectionLabel>Features</SectionLabel>
          <h2 className="mt-6 font-display text-[36px] md:text-headline-lg text-ink max-w-3xl">
            The whole business, on one thread.
          </h2>
        </FadeIn>
        <div className="mt-20 flex flex-col gap-24">
          {features.map((f, i) => {
            const reverse = i % 2 === 1;
            return (
              <FadeIn key={f.title}>
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
                  <div
                    className={`lg:col-span-7 ${reverse ? "lg:order-2" : ""}`}
                  >
                    <div className="border border-hairline bg-neutral aspect-[16/10] flex items-center justify-center">
                      <ChatMockup
                        title={f.label}
                        messages={[
                          { from: "user", text: i === 0 ? "Need a quote for AC repair urgent" : i === 1 ? "Move my Friday slot to Saturday" : "Done with the service, thanks!", time: "12:18" },
                          { from: "ai", text: i === 0 ? "We can be there by 6 PM today. ₹399 visit + parts. Confirm?" : i === 1 ? "Moved ✓ Saturday 4 PM with the same stylist. Reminder sent." : "Glad you loved it! 30s Google review: g.page/glow-salon ★★★★★", time: "12:18" },
                        ]}
                        className="m-6 w-[88%]"
                      />
                    </div>
                  </div>
                  <div className={`lg:col-span-5 ${reverse ? "lg:order-1" : ""}`}>
                    <SectionLabel>{f.label}</SectionLabel>
                    <h3 className="mt-4 font-display text-headline-md text-ink">{f.title}</h3>
                    <ul className="mt-6 space-y-3">
                      {f.bullets.map((b, j) => (
                        <li key={b} className="flex items-start gap-3 text-body-sm text-graphite">
                          {j === 0 ? (
                            <ArrowRight size={16} className="text-signal mt-1 shrink-0" strokeWidth={1.5} />
                          ) : (
                            <Minus size={16} className="text-stone mt-1 shrink-0" strokeWidth={1.5} />
                          )}
                          <span>{b}</span>
                        </li>
                      ))}
                    </ul>
                    <Link
                      to="/features"
                      className="mt-8 inline-block font-body text-body-sm text-ink border-b border-hairline hover:border-signal pb-0.5"
                    >
                      {f.cta} →
                    </Link>
                  </div>
                </div>
              </FadeIn>
            );
          })}
        </div>
      </Section>

      <Rule />

      {/* STATS */}
      <Section inset>
        <FadeIn>
          <SectionLabel>By the Numbers</SectionLabel>
          <h2 className="mt-6 font-display text-[36px] md:text-headline-lg text-ink max-w-3xl">
            Real impact on real Global businesses.
          </h2>
        </FadeIn>
        <div className="mt-14 grid grid-cols-2 md:grid-cols-4 gap-8">
          <FadeIn delay={0.05}><Stat value="3s" label="Average AI response" /></FadeIn>
          <FadeIn delay={0.1}><Stat value="₹1.38L" label="Avg. monthly recovered revenue" /></FadeIn>
          <FadeIn delay={0.15}><Stat value="60%" label="Leads booked automatically" /></FadeIn>
          <FadeIn delay={0.2}><Stat value="4.7" label="Avg. Google rating after 90 days" /></FadeIn>
        </div>
      </Section>

      <Rule />

      {/* TESTIMONIALS */}
      <Section>
        <FadeIn>
          <SectionLabel>Customers</SectionLabel>
          <h2 className="mt-6 font-display text-[36px] md:text-headline-lg text-ink max-w-3xl">
            What service businesses say after 30 days.
          </h2>
        </FadeIn>
        <div className="mt-14 grid grid-cols-1 md:grid-cols-3 gap-6">
          {testimonials.map((t, i) => (
            <FadeIn key={t.name} delay={i * 0.06}>
              <Card className={`h-full flex flex-col ${t.featured ? "border-2 border-signal" : ""}`}>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <Star key={s} size={14} className="fill-ink text-ink" />
                  ))}
                </div>
                <p className="mt-6 text-body-md text-ink flex-1">"{t.quote}"</p>
                <div className="mt-8 pt-6 border-t border-hairline">
                  <p className="font-body text-body-sm font-medium text-ink">{t.name}</p>
                  <p className="font-mono text-mono-sm text-stone mt-1">{t.business}</p>
                </div>
              </Card>
            </FadeIn>
          ))}
        </div>
        <FadeIn delay={0.3}>
          <div className="mt-12 flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-2 text-body-sm text-graphite">
              <Check size={16} className="text-signal" strokeWidth={1.5} />
              ISO 27001 certified
            </div>
            <div className="flex items-center gap-2 text-body-sm text-graphite">
              <Check size={16} className="text-signal" strokeWidth={1.5} />
              Hosted in India
            </div>
            <div className="flex items-center gap-2 text-body-sm text-graphite">
              <Check size={16} className="text-signal" strokeWidth={1.5} />
              GDPR & DPDP compliant
            </div>
          </div>
        </FadeIn>
      </Section>

      <Rule />



      <CTASection />
    </>
  );
}

// silence unused import warning for Button — used in mobile flows referenced elsewhere
void Button;

function StepBlock({ step, index, onInView }: { step: PlaybookStep; index: number; onInView: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { margin: "-45% 0px -45% 0px" });
  const { t } = useTranslation();

  useEffect(() => {
    if (inView) {
      onInView();
    }
  }, [inView, onInView]);

  return (
    <div ref={ref} className="relative transition-opacity duration-300" style={{ opacity: inView ? 1 : 0.4 }}>
      <div className="lg:hidden mb-4">
        <span className="text-display-xl font-display text-stone absolute -top-12 -left-4 pointer-events-none select-none z-[-1] opacity-20">
          {step.stepNumber}
        </span>
      </div>
      <SectionLabel className="mb-4">{step.stepNumber} — {t(step.heading)}</SectionLabel>
      <h3 className="font-display text-headline-md text-ink mb-4">{t(step.heading)}</h3>
      <p className="text-body-md text-graphite mb-8">{t(step.description)}</p>

      <div className="bg-surface p-6 border border-hairline mb-8 lg:mb-0">
        <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone mb-4">
          {t(step.highlightsLabel)}
        </p>
        <ul className="space-y-3">
          {step.highlights.map(h => (
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
