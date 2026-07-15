import { Container } from "@/components/linen";

export default function OnboardingPage() {
  return (
    <Container className="flex min-h-screen flex-col items-start justify-center gap-4">
      <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">Welcome</p>
      <h1 className="font-display text-headline-lg text-ink">Let&apos;s set up your business</h1>
      <p className="max-w-prose font-body text-body-md text-graphite">
        The guided onboarding conversation lands in a later phase.
      </p>
    </Container>
  );
}
