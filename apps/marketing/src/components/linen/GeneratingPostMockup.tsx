import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Check, Bot, Share2 } from "lucide-react";

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

export function GeneratingPostMockup() {
  const { t } = useTranslation();

  return (
    <div className="w-full bg-neutral/50 border border-hairline p-6 min-h-[480px] flex items-center justify-center">
      <div className="w-full max-w-md bg-surface border border-hairline shadow-sm overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-hairline bg-neutral">
          <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
            {t("Generating Post")}
          </p>
          <div className="flex gap-1.5">
            <span className="w-2 h-2 rounded-full bg-signal animate-pulse" />
            <span className="w-2 h-2 rounded-full bg-hairline/40" />
            <span className="w-2 h-2 rounded-full bg-hairline/40" />
          </div>
        </div>

        <div className="p-6">
          <div className="flex items-start gap-3 mb-6">
            <div className="w-8 h-8 rounded-full bg-signal/10 flex items-center justify-center shrink-0">
              <Bot size={16} className="text-signal" />
            </div>
            <div className="flex-1 bg-neutral p-4 border border-hairline/50 text-body-sm text-ink">
              <p className="font-medium mb-2">{t("Drafting Campaign: Summer Promo")}</p>
              <div className="h-2 bg-hairline/30 w-full overflow-hidden mt-2">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                  className="h-full bg-signal"
                />
              </div>
            </div>
          </div>

          <div className="mb-6">
            <p className="text-label-sm font-mono text-stone uppercase tracking-[0.14em] mb-3">
              {t("Publishing Channels")}
            </p>
            <div className="flex flex-wrap gap-2">
              {["Instagram", "Facebook", "LinkedIn", "TikTok"].map((platform) => (
                <button
                  key={platform}
                  className="flex items-center gap-2 border border-hairline px-3 py-1.5 text-body-sm hover:border-signal transition-colors cursor-pointer"
                >
                  <Share2 size={12} className="text-stone" />
                  {t(platform)}
                </button>
              ))}
            </div>
          </div>

          <ApproveModifyButtons />
        </div>
      </div>
    </div>
  );
}
