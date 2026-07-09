import { Container } from "@/components/linen/Container";
import { ButtonLink } from "@/components/linen/Button";
import { useTranslation } from "react-i18next";

export function CTASection() {
  const { t } = useTranslation();
  return (
    <section className="bg-ink py-24 md:py-32">
      <Container>
        <div className="max-w-3xl">
          <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-surface/60">
            {t("Start in 5 minutes")}
          </p>
          <h2 className="mt-6 font-display text-display-lg text-surface">
            {t("Your competitors are already automating.")}
          </h2>
          <p className="mt-6 text-body-md text-surface/70 max-w-xl">
            {t("Join 2,400+ Global service businesses using IIEVI to handle every lead, booking, and follow-up — automatically, on WhatsApp.")}
          </p>
          <div className="mt-10 flex flex-wrap gap-4">
            <ButtonLink
              to="/register"
              variant="ghost-inverse"

            >
              {t("Get Started Free")}
            </ButtonLink>
            <ButtonLink to="/demo" variant="ghost-inverse">{t("Book a Demo")}</ButtonLink>
          </div>
          <p className="mt-8 font-mono text-mono-sm text-surface/60">
            {t("No credit card · 14-day free trial · Cancel anytime")}
          </p>
        </div>
      </Container>
    </section>
  );
}
