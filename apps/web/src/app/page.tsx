import { StatusPill } from "@/components/StatusPill";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-[1280px] flex-col items-start justify-center gap-6 px-6 md:px-10">
      <StatusPill label="Platform scaffold" />
      <h1 className="font-display text-headline-lg">IIEVI</h1>
      <p className="max-w-prose font-body text-body-md text-graphite">
        Application shell. The product dashboard is built in later phases — this
        page verifies the Linen design tokens, fonts, and strict TypeScript
        pipeline are wired correctly.
      </p>
    </main>
  );
}
