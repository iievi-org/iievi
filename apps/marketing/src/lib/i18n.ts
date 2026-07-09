import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const resources = {
  en: {
    translation: {
      cta: {
        startIn5Minutes: "Start in 5 minutes",
        competitorsAutomating: "Your competitors are already automating.",
        joinBusinesses:
          "Join 2,400+ Global service businesses using IIEVI to handle every lead, booking, and follow-up — automatically, on WhatsApp.",
        getStartedFree: "Get Started Free",
        bookDemo: "Book a Demo",
        noCreditCard: "No credit card · 14-day free trial · Cancel anytime",
      },
      dashboard: {
        url: "app.iievi.in/dashboard",
        live: "Live",
        today: "Today",
        leads: "Leads",
        revenue: "Revenue",
        cpl: "CPL ↓",
        liveActivity: "Live activity",
        autoUpdating: "Auto-updating",
        thisWeek: "This week",
        vsLast: "+34% vs last",
        age: {
          now: "now",
          seconds: "{{count}}s",
          minutes: "{{count}}m",
        },
        pool: {
          newLead: {
            label: "New lead",
            detail: "Reema · Hair colour enquiry",
          },
          bookingConfirmed: {
            label: "Booking confirmed",
            detail: "4 PM with Priya · ₹2,800",
          },
          postScheduled: {
            label: "Post scheduled",
            detail: "Diwali offer · Instagram + Meta",
          },
          campaignLive: {
            label: "Campaign live",
            detail: "Glow Weekend · ₹500/day · 4 channels",
          },
          reviewCollected: {
            label: "Review collected",
            detail: "Anjali · 5★ · Google Maps",
          },
          followUpSent: {
            label: "Follow-up sent",
            detail: "12 lapsed customers · 30-day win-back",
          },
        },
      },
    },
  },
};

i18n.use(initReactI18next).init({
  resources,
  lng: "en",
  fallbackLng: "en",
  interpolation: {
    escapeValue: false, // react already safes from xss
  },
});

export default i18n;
