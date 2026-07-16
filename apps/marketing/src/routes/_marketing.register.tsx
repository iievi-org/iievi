import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { CheckCircle } from "lucide-react";
import { Container } from "@/components/linen/Container";
import { Input } from "@/components/linen/Input";
import { Button } from "@/components/linen/Button";
import { Rule } from "@/components/linen/Rule";
import { ChatMockup } from "@/components/linen/ChatMockup";
import { FadeIn } from "@/components/linen/FadeIn";
import { SectionLabel } from "@/components/linen/SectionLabel";

export const Route = createFileRoute("/_marketing/register")({
  head: () => ({
    meta: [
      { title: "Start Free — IIEVI" },
      {
        name: "description",
        content:
          "Create your IIEVI account in 30 seconds. No credit card, 14-day free trial of all features.",
      },
      { property: "og:title", content: "Start Free — IIEVI" },
      { property: "og:description", content: "Create your IIEVI account in 30 seconds." },
    ],
  }),
  component: RegisterPage,
});

function RegisterPage() {
  const [form, setForm] = useState({ name: "", business: "", email: "", phone: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [done, setDone] = useState(false);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const next: Record<string, string> = {};
    if (!form.name) next.name = "Required";
    if (!form.business) next.business = "Required";
    if (!form.email.includes("@")) next.email = "Enter a valid email";
    if (form.phone.replace(/\D/g, "").length < 10) next.phone = "Enter a 10-digit number";
    setErrors(next);
    if (Object.keys(next).length === 0) setDone(true);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 min-h-[calc(100vh-5rem)]">
      <div className="bg-neutral border-r border-hairline flex items-center justify-center p-8 md:p-16">
        <div className="w-full max-w-md">
          <FadeIn>
            <SectionLabel>Live preview</SectionLabel>
            <h2 className="mt-6 font-display text-headline-lg text-ink">
              This is what your customers will see.
            </h2>
            <p className="mt-4 text-body-sm text-graphite">
              IIEVI replies in 3 seconds on your WhatsApp number — in Hindi, English, or Hinglish.
            </p>
          </FadeIn>
          <div className="mt-10">
            <ChatMockup
              title="Sample on your number"
              messages={[
                { from: "user", text: "Hi, do you have an appointment today?", time: "Now" },
                {
                  from: "ai",
                  text: "Yes! 3 PM, 5 PM, or 6:30 PM are open. Which works best?",
                  time: "Now",
                },
                { from: "user", text: "5 PM please", time: "Now" },
                {
                  from: "ai",
                  text: "Booked ✓ See you at 5 PM today. Reminder 30 min before.",
                  time: "Now",
                },
              ]}
            />
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center p-8 md:p-16">
        <div className="w-full max-w-md">
          <Link to="/" className="font-display font-bold text-[22px] tracking-[-0.01em] text-ink">
            IIEVI
          </Link>
          {done ? (
            <div className="mt-12">
              <CheckCircle size={40} className="text-signal" strokeWidth={1.5} />
              <h1 className="mt-6 font-display text-headline-lg text-ink">You're in.</h1>
              <p className="mt-4 text-body-md text-graphite">
                Check your inbox at <span className="text-ink">{form.email}</span> for your
                dashboard link. Our team will WhatsApp you in 5 minutes to set up your number.
              </p>
              <div className="mt-8">
                <Link
                  to="/"
                  className="font-body text-label-sm uppercase tracking-[0.14em] text-ink border-b border-hairline pb-1"
                >
                  Back to home
                </Link>
              </div>
            </div>
          ) : (
            <>
              <h1 className="mt-10 font-display text-headline-lg text-ink">
                Start your 14-day free trial.
              </h1>
              <p className="mt-4 text-body-sm text-graphite">
                No credit card. Cancel anytime. Full Growth-plan features.
              </p>
              <button
                type="button"
                className="mt-8 w-full bg-neutral border border-hairline text-ink py-3 px-4 font-body text-body-sm hover:bg-ink hover:text-surface transition-colors cursor-pointer flex items-center justify-center gap-3"
              >
                <span className="font-bold text-base">G</span> Continue with Google
              </button>
              <div className="my-8 flex items-center gap-4">
                <Rule />
                <span className="font-mono text-mono-sm text-stone uppercase">Or</span>
                <Rule />
              </div>
              <form onSubmit={submit} className="flex flex-col gap-6">
                <Input
                  label="Full name"
                  name="name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  error={errors.name}
                />
                <Input
                  label="Business name"
                  name="business"
                  value={form.business}
                  onChange={(e) => setForm({ ...form, business: e.target.value })}
                  error={errors.business}
                />
                <Input
                  label="Email"
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  error={errors.email}
                />
                <Input
                  label="WhatsApp number"
                  name="phone"
                  placeholder="+91 98765 43210"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  error={errors.phone}
                />
                <Button type="submit" variant="primary" className="mt-4 w-full">
                  Create Account
                </Button>
                <p className="font-mono text-mono-sm text-stone">
                  By signing up you agree to our{" "}
                  <Link to="/terms" className="text-ink border-b border-hairline">
                    Terms
                  </Link>{" "}
                  and{" "}
                  <Link to="/privacy" className="text-ink border-b border-hairline">
                    Privacy Policy
                  </Link>
                  .
                </p>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
