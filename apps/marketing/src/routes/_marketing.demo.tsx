import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { MessageCircle, Check } from "lucide-react";
import { Container } from "@/components/linen/Container";
import { Rule } from "@/components/linen/Rule";
import { Pill } from "@/components/linen/Pill";
import { ButtonAnchor } from "@/components/linen/Button";
import { FadeIn } from "@/components/linen/FadeIn";
import { SectionLabel } from "@/components/linen/SectionLabel";

export const Route = createFileRoute("/_marketing/demo")({
  head: () => ({
    meta: [
      { title: "Book a Demo — IIEVI" },
      {
        name: "description",
        content:
          "See IIEVI live on your WhatsApp number. 20-minute demo, real conversations, your questions answered.",
      },
      { property: "og:title", content: "Book a Demo — IIEVI" },
      { property: "og:description", content: "20-minute live demo with the IIEVI team." },
    ],
  }),
  component: DemoPage,
});

const SLOTS = ["10:00", "11:30", "14:00", "15:30", "17:00", "18:30"];
const DAYS = ["Mon 02", "Tue 03", "Wed 04", "Thu 05", "Fri 06"];

function DemoPage() {
  const [day, setDay] = useState(1);
  const [slot, setSlot] = useState<string | null>(null);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 min-h-[calc(100vh-5rem)]">
      <div className="border-r border-hairline p-8 md:p-16 flex items-center">
        <div className="max-w-md">
          <FadeIn>
            <SectionLabel>20-minute live demo</SectionLabel>
            <h1 className="mt-6 font-display text-headline-lg text-ink">
              See IIEVI replying on a real WhatsApp number.
            </h1>
          </FadeIn>
          <FadeIn delay={0.05}>
            <p className="mt-6 text-body-md text-graphite">
              Pick a slot below. We'll send a calendar invite and a WhatsApp link. On the call:
            </p>
          </FadeIn>
          <FadeIn delay={0.1}>
            <ul className="mt-8 space-y-4">
              {[
                "We message your demo number live — you watch the AI reply",
                "We walk through bookings, reviews, and dashboards",
                "We answer pricing and migration questions",
                "You decide if it's a fit. No hard sell.",
              ].map((t) => (
                <li key={t} className="flex items-start gap-3 text-body-sm text-graphite">
                  <Check size={16} className="text-signal mt-1 shrink-0" strokeWidth={1.5} />
                  <span>{t}</span>
                </li>
              ))}
            </ul>
          </FadeIn>
          <FadeIn delay={0.15}>
            <div className="mt-12">
              <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone mb-4">
                Prefer WhatsApp?
              </p>
              <ButtonAnchor href="https://wa.me/919876543210" variant="ghost">
                <MessageCircle size={14} strokeWidth={1.5} /> Message us directly
              </ButtonAnchor>
            </div>
          </FadeIn>
        </div>
      </div>

      <div className="p-8 md:p-16 flex items-center">
        <div className="w-full max-w-md">
          <FadeIn>
            <Pill>December 2026</Pill>
            <h2 className="mt-6 font-display text-headline-md text-ink">Pick a time.</h2>
          </FadeIn>
          <FadeIn delay={0.05}>
            <div className="mt-8 bg-neutral border border-hairline p-6">
              <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
                This Week — IST
              </p>
              <div className="mt-4 grid grid-cols-5 gap-2">
                {DAYS.map((d, i) => (
                  <button
                    key={d}
                    onClick={() => {
                      setDay(i);
                      setSlot(null);
                    }}
                    className={`py-3 font-body text-body-sm transition-colors cursor-pointer border ${
                      day === i
                        ? "border-2 border-signal text-ink"
                        : "border-hairline text-graphite hover:text-ink"
                    }`}
                  >
                    <span className="block font-mono text-mono-sm text-stone">
                      {d.split(" ")[0]}
                    </span>
                    {d.split(" ")[1]}
                  </button>
                ))}
              </div>
              <Rule className="my-6" />
              <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
                Available Slots
              </p>
              <div className="mt-4 grid grid-cols-3 gap-2">
                {SLOTS.map((s) => (
                  <button
                    key={s}
                    onClick={() => setSlot(s)}
                    className={`py-3 font-body text-body-sm transition-colors cursor-pointer border ${
                      slot === s
                        ? "bg-ink text-surface border-ink"
                        : "border-hairline text-ink hover:bg-ink hover:text-surface"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </FadeIn>
          {slot && (
            <FadeIn>
              <div className="mt-6 p-4 border border-hairline">
                <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
                  Selected
                </p>
                <p className="mt-2 text-body-md text-ink">
                  {DAYS[day]} December · {slot} IST
                </p>
                <button className="mt-4 w-full bg-ink text-surface py-3 px-4 font-body text-label-sm uppercase tracking-[0.14em] hover:bg-transparent hover:text-ink border border-ink transition-colors cursor-pointer">
                  Confirm Booking
                </button>
              </div>
            </FadeIn>
          )}
        </div>
      </div>
    </div>
  );
}
