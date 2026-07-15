import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import {
  type MockupData,
  type OnboardingData,
  type BusinessProfileData,
  type SecureApiData,
  type AiCommandData,
  type ContentGeneratorData,
  type PublishingData,
  type AiConversationData,
  type LeadPipelineData,
  type AdBudgetData,
  type TargetReachData,
} from "@/lib/solutionPlaybookData";
import { Check, ShieldCheck, Lock, Activity, Bot, User, ChevronDown } from "lucide-react";

interface PlaybookMockupProps {
  mockup: MockupData;
}

export function PlaybookMockup({ mockup }: PlaybookMockupProps) {
  return (
    <div className="w-full h-full flex items-center justify-center bg-neutral/50 border border-hairline p-6 min-h-[480px]">
      <div className="w-full max-w-md bg-surface border border-hairline shadow-sm overflow-hidden relative">
        <MockupContent mockup={mockup} />
      </div>
    </div>
  );
}

function MockupContent({ mockup }: { mockup: MockupData }) {
  switch (mockup.type) {
    case "onboarding":
      return <OnboardingMockup data={mockup.data} />;
    case "business-profile":
      return <BusinessProfileMockup data={mockup.data} />;
    case "secure-api":
      return <SecureApiMockup data={mockup.data} />;
    case "ai-command":
      return <AiCommandMockup data={mockup.data} />;
    case "content-generator":
      return <ContentGeneratorMockup data={mockup.data} />;
    case "publishing":
      return <PublishingMockup data={mockup.data} />;
    case "ai-conversation":
      return <AiConversationMockup data={mockup.data} />;
    case "lead-pipeline":
      return <LeadPipelineMockup data={mockup.data} />;
    case "ad-budget":
      return <AdBudgetMockup data={mockup.data} />;
    case "target-reach":
      return <TargetReachMockup data={mockup.data} />;
    default:
      return null;
  }
}

// ── Shared UI ────────────────────────────────────────────

function ApproveModifyButtons({ className = "" }: { className?: string }) {
  const { t } = useTranslation();
  return (
    <div className={`grid grid-cols-2 gap-3 mt-6 ${className}`}>
      <button className="bg-ink text-surface py-2.5 text-body-sm font-mono uppercase tracking-[0.14em] hover:bg-emerald-600 hover:text-white transition-colors cursor-pointer">
        {t("Approve")}
      </button>
      <button className="bg-ink text-surface py-2.5 text-body-sm font-mono uppercase tracking-[0.14em] hover:bg-amber-500 hover:text-gray-900 transition-colors cursor-pointer">
        {t("Modify")}
      </button>
    </div>
  );
}

// ── Shared Header ────────────────────────────────────────

function MockupHeader({ title }: { title: string }) {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-between px-5 py-3 border-b border-hairline bg-neutral">
      <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">{t(title)}</p>
      <div className="flex gap-1.5">
        <span className="w-2 h-2 rounded-full bg-hairline/40" />
        <span className="w-2 h-2 rounded-full bg-hairline/40" />
        <span className="w-2 h-2 rounded-full bg-hairline/40" />
      </div>
    </div>
  );
}

// ── Specific Mockups ─────────────────────────────────────

function OnboardingMockup({ data }: { data: OnboardingData }) {
  const { t } = useTranslation();
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <MockupHeader title="Welcome to IIEVI" />
      <div className="p-6 space-y-6">
        <div>
          <label className="block text-label-sm font-mono text-stone mb-2 uppercase tracking-[0.14em]">
            {t("Business Name")}
          </label>
          <div className="w-full border border-hairline px-3 py-2 text-body-sm text-ink bg-neutral/30">
            {t(data.businessName)}
          </div>
        </div>
        <div>
          <label className="block text-label-sm font-mono text-stone mb-2 uppercase tracking-[0.14em]">
            {t("Industry")}
          </label>
          <div className="w-full border border-hairline px-3 py-2 text-body-sm text-ink bg-neutral/30 flex justify-between items-center">
            {t(data.industry)}
            <ChevronDown size={14} className="text-stone" />
          </div>
        </div>
        <div>
          <label className="block text-label-sm font-mono text-stone mb-3 uppercase tracking-[0.14em]">
            {t("Primary Goal")}
          </label>
          <div className="space-y-3">
            {data.goals.map((goal, i) => (
              <div key={goal} className="flex items-center gap-3">
                <div
                  className={`w-4 h-4 rounded-full border flex items-center justify-center
                    ${i === data.selectedGoal ? "border-signal bg-signal/10" : "border-hairline"}`}
                >
                  {i === data.selectedGoal && <div className="w-2 h-2 rounded-full bg-signal" />}
                </div>
                <span className="text-body-sm text-ink">{t(goal)}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="pt-2">
          <button className="w-full bg-ink text-surface py-2.5 text-body-sm uppercase tracking-[0.14em] font-mono hover:bg-ink/90 transition-colors">
            {t("Continue")}
          </button>
        </div>
      </div>
    </motion.div>
  );
}

function BusinessProfileMockup({ data }: { data: BusinessProfileData }) {
  const { t } = useTranslation();
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
    >
      <MockupHeader title="Business Profile" />
      <div className="p-6 space-y-6">
        <div>
          <label className="block text-label-sm font-mono text-stone mb-2 uppercase tracking-[0.14em]">
            {t("Brand Voice")}
          </label>
          <div className="inline-block border border-hairline px-3 py-1.5 text-body-sm text-ink bg-neutral/50">
            {t(data.brandVoice)}
          </div>
        </div>
        <div>
          <label className="block text-label-sm font-mono text-stone mb-3 uppercase tracking-[0.14em]">
            {t("Products")}
          </label>
          <div className="space-y-2.5">
            {data.products.map((p, i) => (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.15 }}
                key={p}
                className="flex items-center gap-3"
              >
                <div className="w-4 h-4 bg-ink flex items-center justify-center shrink-0">
                  <Check size={12} className="text-surface" strokeWidth={3} />
                </div>
                <span className="text-body-sm text-ink truncate">{t(p)}</span>
              </motion.div>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-label-sm font-mono text-stone mb-2 uppercase tracking-[0.14em]">
            {t("Target Audience")}
          </label>
          <div className="text-body-sm text-ink">{t(data.targetAudience)}</div>
        </div>
        <div className="pt-4 border-t border-hairline">
          <div className="flex justify-between items-center mb-2">
            <span className="text-label-sm font-mono text-stone uppercase tracking-[0.14em]">
              {t("Profile Complete")}
            </span>
            <span className="text-mono-sm font-mono text-ink">{data.profileComplete}%</span>
          </div>
          <div className="h-1 bg-hairline/30 w-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${data.profileComplete}%` }}
              transition={{ duration: 1, delay: 0.5, ease: "easeOut" }}
              className="h-full bg-signal"
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function SecureApiMockup({ data }: { data: SecureApiData }) {
  const { t } = useTranslation();
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <MockupHeader title="Secure Integrations" />
      <div className="p-6">
        <div className="space-y-3 mb-8">
          {data.platforms.map((p, i) => (
            <div
              key={p.name}
              className="flex justify-between items-center border-b border-hairline/40 pb-3"
            >
              <span className="text-body-sm text-ink">{p.name}</span>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.15 + 0.3 }}
                className="flex items-center gap-1.5 text-stone text-mono-sm font-mono uppercase tracking-[0.14em]"
              >
                {t("Connected")} <Check size={14} className="text-signal" />
              </motion.div>
            </div>
          ))}
        </div>
        <div className="bg-neutral p-5 border border-hairline relative overflow-hidden">
          <ShieldCheck
            size={80}
            className="absolute -right-4 -bottom-4 text-hairline/20"
            strokeWidth={1}
          />
          <p className="text-label-sm font-mono text-stone mb-4 uppercase tracking-[0.14em]">
            {t("API Key Status")}
          </p>
          <div className="space-y-2.5 relative z-10">
            {data.statusItems.map((s, i) => (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.2 + 0.8 }}
                key={s}
                className="flex items-center gap-2"
              >
                <Lock size={12} className="text-signal" />
                <span className="text-body-sm text-ink">{t(s)}</span>
              </motion.div>
            ))}
          </div>
        </div>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          className="mt-6 flex justify-between items-center text-mono-sm font-mono text-ink"
        >
          <span className="uppercase tracking-[0.14em] text-stone">{t("Security Score")}</span>
          <span className="text-signal">{data.securityScore}%</span>
        </motion.div>
      </div>
    </motion.div>
  );
}

function AiCommandMockup({ data }: { data: AiCommandData }) {
  const { t } = useTranslation();
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
      <MockupHeader title="AI Command Center" />
      <div className="p-6">
        <label className="block text-label-sm font-mono text-stone mb-3 uppercase tracking-[0.14em]">
          {t("User Prompt")}
        </label>
        <div className="w-full border border-hairline bg-surface p-4 min-h-[100px] mb-6 shadow-inner relative">
          <p className="text-body-md text-ink animate-typewriter overflow-hidden whitespace-normal border-r-2 border-r-signal">
            {t(data.prompt)}
          </p>
        </div>
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 2.2 }}
          className="w-full bg-signal text-surface py-3 text-body-sm uppercase tracking-[0.14em] font-mono flex items-center justify-center gap-2"
        >
          <Bot size={16} />
          {t("Generate Campaign")}
        </motion.button>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2.8 }}
          className="mt-6 border-t border-hairline pt-6"
        >
          <div className="flex justify-between items-center mb-2">
            <span className="text-mono-sm font-mono text-stone uppercase tracking-[0.14em] flex items-center gap-2">
              <Activity size={12} className="animate-pulse text-signal" />
              {t("AI Thinking...")}
            </span>
          </div>
          <div className="h-1 w-full bg-hairline/30 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: "100%" }}
              transition={{ duration: 2, delay: 3, ease: "linear", repeat: Infinity }}
              className="h-full bg-signal"
            />
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}

function ContentGeneratorMockup({ data }: { data: ContentGeneratorData }) {
  const { t } = useTranslation();
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
    >
      <MockupHeader title="Content Generator" />
      <div className="p-6">
        <div className="mb-6 pb-4 border-b border-hairline">
          <p className="text-label-sm font-mono text-stone uppercase tracking-[0.14em] mb-1">
            {t("Campaign")}
          </p>
          <p className="text-body-md text-ink font-medium">{t(data.campaignName)}</p>
        </div>
        <div className="space-y-4">
          {data.channels.map((c, i) => (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.3 }}
              key={c}
              className="flex items-center gap-3 bg-neutral p-3 border border-hairline/50"
            >
              <div className="w-5 h-5 rounded-full bg-signal/10 flex items-center justify-center shrink-0">
                <Check size={12} className="text-signal" strokeWidth={3} />
              </div>
              <span className="text-body-sm text-ink">{t(c)}</span>
            </motion.div>
          ))}
        </div>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: data.channels.length * 0.3 + 0.5 }}
          className="mt-8 flex justify-between items-center px-4 py-2 border border-hairline bg-neutral/50"
        >
          <span className="text-mono-sm font-mono text-stone uppercase tracking-[0.14em]">
            {t("Status")}
          </span>
          <span className="text-mono-sm font-mono text-ink bg-signal/10 px-2 py-0.5 border border-signal/20">
            {t("Generated")}
          </span>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: data.channels.length * 0.3 + 1 }}
        >
          <ApproveModifyButtons />
        </motion.div>
      </div>
    </motion.div>
  );
}

function PublishingMockup({ data }: { data: PublishingData }) {
  const { t } = useTranslation();
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <MockupHeader title="Publishing Pipeline" />
      <div className="p-6">
        <div className="space-y-0 border border-hairline">
          {data.platforms.map((p, i) => (
            <div
              key={p.name}
              className="flex justify-between items-center p-3 border-b border-hairline last:border-0 relative overflow-hidden"
            >
              <span className="text-body-sm text-ink relative z-10">{p.name}</span>
              <motion.div
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.2 + 0.5 }}
                className="flex items-center gap-1.5 text-signal text-mono-sm font-mono uppercase tracking-[0.14em] relative z-10"
              >
                <Check size={14} /> {t(p.status)}
              </motion.div>
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: "100%" }}
                transition={{ duration: 0.4, delay: i * 0.2 + 0.1 }}
                className="absolute left-0 top-0 bottom-0 bg-signal/5 z-0"
              />
            </div>
          ))}
        </div>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: data.platforms.length * 0.2 + 1 }}
          className="mt-8 text-center"
        >
          <p className="text-mono-sm font-mono text-stone uppercase tracking-[0.14em] mb-2">
            {t("Est. Reach")}
          </p>
          <p className="text-[32px] font-display text-ink tabular-nums leading-none">
            {data.reach.toLocaleString()}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: data.platforms.length * 0.2 + 1.5 }}
        >
          <ApproveModifyButtons />
        </motion.div>
      </div>
    </motion.div>
  );
}

function AiConversationMockup({ data }: { data: AiConversationData }) {
  const { t } = useTranslation();
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
      <MockupHeader title="Incoming Lead" />
      <div className="p-5 flex flex-col gap-4">
        {/* Customer message */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="flex flex-col gap-1 items-start"
        >
          <div className="flex items-center gap-2 mb-1">
            <User size={12} className="text-stone" />
            <span className="text-mono-sm font-mono text-stone uppercase tracking-[0.14em]">
              {t("Customer")}
            </span>
          </div>
          <div className="bg-neutral border border-hairline px-4 py-2.5 text-body-sm text-ink max-w-[85%]">
            {t(data.customerMessage)}
          </div>
        </motion.div>

        {/* AI message */}
        <div className="flex flex-col gap-1 items-end mt-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5 }}
            className="flex items-center gap-2 mb-1"
          >
            <span className="text-mono-sm font-mono text-stone uppercase tracking-[0.14em]">
              {t("AI Assistant")}
            </span>
            <Bot size={12} className="text-signal" />
          </motion.div>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 2 }}
            className="bg-ink text-surface px-4 py-2.5 text-body-sm max-w-[85%] relative"
          >
            {/* We simulate typing by hiding parts of it, but simple fade is cleaner. Let's use typewriter CSS if we want, or just fade in. For AI, fade in is fine. */}
            {t(data.aiResponse)}
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 3 }}
          className="mt-4 pt-4 border-t border-hairline/40 text-right"
        >
          <span className="text-mono-sm font-mono text-stone uppercase tracking-[0.14em]">
            {t("Response Time")}: <span className="text-signal">{t(data.responseTime)}</span>
          </span>
        </motion.div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 3.5 }}>
          <ApproveModifyButtons />
        </motion.div>
      </div>
    </motion.div>
  );
}

function LeadPipelineMockup({ data }: { data: LeadPipelineData }) {
  const { t } = useTranslation();
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
    >
      <MockupHeader title="Lead Pipeline" />
      <div className="p-6">
        <div className="relative pl-6 space-y-6">
          <div className="absolute left-1.5 top-2 bottom-2 w-px bg-hairline/30" />
          {data.stages.map((stage, i) => {
            const isCompleted = i < data.activeStage;
            const isActive = i === data.activeStage;
            const isFuture = i > data.activeStage;

            return (
              <div key={stage} className="relative flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {/* Node */}
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: i * 0.3 }}
                    className={`absolute -left-6 w-3 h-3 rounded-full border-2 bg-surface
                      ${isCompleted ? "border-ink bg-ink" : isActive ? "border-signal bg-signal" : "border-hairline/50"}`}
                  />
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.3 + 0.1 }}
                    className={`text-body-sm ${isActive ? "text-signal font-medium" : isCompleted ? "text-ink" : "text-stone"}`}
                  >
                    {t(stage)}
                  </motion.span>
                </div>
                {/* Status icon */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.3 + 0.2 }}
                >
                  {isCompleted && <Check size={14} className="text-ink" />}
                  {isActive && <div className="w-2 h-2 rounded-full bg-signal animate-pulse" />}
                  {isFuture && (
                    <div className="w-1.5 h-1.5 rounded-full border border-hairline/50" />
                  )}
                </motion.div>
              </div>
            );
          })}

          {/* Active indicator line overlay */}
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: `${(data.activeStage / (data.stages.length - 1)) * 100}%` }}
            transition={{ duration: data.activeStage * 0.3, ease: "linear" }}
            className="absolute left-1.5 top-2 w-px bg-signal z-0"
            style={{ transformOrigin: "top" }}
          />
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: data.stages.length * 0.3 + 0.5 }}
          className="mt-8 pt-5 border-t border-hairline flex justify-between items-center"
        >
          <span className="text-mono-sm font-mono text-stone uppercase tracking-[0.14em]">
            {t("Lead Score")}
          </span>
          <div className="flex items-center gap-2">
            <span className="text-body-md font-display text-ink">{data.leadScore}/100</span>
            <div className="w-16 h-1.5 bg-hairline/30 rounded-full overflow-hidden">
              <div className="h-full bg-signal" style={{ width: `${data.leadScore}%` }} />
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}

function AdBudgetMockup({ data }: { data: AdBudgetData }) {
  const { t } = useTranslation();
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
    >
      <MockupHeader title="Campaign Budget & Goals" />
      <div className="p-6 space-y-6">
        <div>
          <label className="block text-label-sm font-mono text-stone mb-2 uppercase tracking-[0.14em]">
            {t("Campaign Objective")}
          </label>
          <div className="border border-hairline px-3 py-2 text-body-sm text-ink bg-neutral/50">
            {t(data.campaignObjective)}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-label-sm font-mono text-stone mb-2 uppercase tracking-[0.14em]">
              {t("Buying Type")}
            </label>
            <div className="border border-hairline px-3 py-2 text-body-sm text-ink bg-neutral/50">
              {t(data.buyingType)}
            </div>
          </div>
          <div>
            <label className="block text-label-sm font-mono text-stone mb-2 uppercase tracking-[0.14em]">
              {t("Budget Type")}
            </label>
            <div className="border border-hairline px-3 py-2 text-body-sm text-ink bg-neutral/50">
              {t(data.budgetType)}
            </div>
          </div>
        </div>
        <div>
          <label className="block text-label-sm font-mono text-stone mb-2 uppercase tracking-[0.14em]">
            {t("Budget Amount")}
          </label>
          <div className="border border-hairline px-3 py-2 text-body-md font-display text-ink bg-neutral/50 flex justify-between">
            <span>₹{data.amount}</span>
            <span className="text-stone font-body text-body-sm">/{t("day")}</span>
          </div>
        </div>

        <ApproveModifyButtons />
      </div>
    </motion.div>
  );
}

function TargetReachMockup({ data }: { data: TargetReachData }) {
  const { t } = useTranslation();
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <MockupHeader title="Target Audience" />
      <div className="p-6 space-y-5">
        <div>
          <label className="block text-label-sm font-mono text-stone mb-2 uppercase tracking-[0.14em]">
            {t("Locations")}
          </label>
          <div className="flex flex-wrap gap-2">
            {data.locations.map((loc) => (
              <span
                key={loc}
                className="inline-block border border-hairline px-2.5 py-1 text-body-sm text-ink bg-neutral/50"
              >
                {t(loc)}
              </span>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-label-sm font-mono text-stone mb-2 uppercase tracking-[0.14em]">
              {t("Age")}
            </label>
            <div className="border border-hairline px-3 py-1.5 text-body-sm text-ink bg-neutral/50">
              {data.ageRange}
            </div>
          </div>
          <div>
            <label className="block text-label-sm font-mono text-stone mb-2 uppercase tracking-[0.14em]">
              {t("Gender")}
            </label>
            <div className="border border-hairline px-3 py-1.5 text-body-sm text-ink bg-neutral/50">
              {t(data.gender)}
            </div>
          </div>
        </div>
        <div>
          <label className="block text-label-sm font-mono text-stone mb-2 uppercase tracking-[0.14em]">
            {t("Detailed Targeting")}
          </label>
          <div className="flex flex-wrap gap-2">
            {data.detailedTargeting.map((dt) => (
              <span
                key={dt}
                className="inline-block border border-hairline px-2.5 py-1 text-body-sm text-ink bg-neutral/50"
              >
                {t(dt)}
              </span>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-label-sm font-mono text-stone mb-2 uppercase tracking-[0.14em]">
            {t("Placements")}
          </label>
          <div className="border border-hairline px-3 py-1.5 text-body-sm text-ink bg-neutral/50">
            {t(data.placements)}
          </div>
        </div>

        <ApproveModifyButtons className="pt-2 border-t border-hairline/40" />
      </div>
    </motion.div>
  );
}
