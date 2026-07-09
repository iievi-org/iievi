import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { type PlaybookStep } from "@/lib/solutionPlaybookData";

interface PlaybookProgressProps {
  steps: PlaybookStep[];
  activeStepIndex: number;
}

export function PlaybookProgress({ steps, activeStepIndex }: PlaybookProgressProps) {
  const { t } = useTranslation();
  const containerRef = useRef<HTMLDivElement>(null);
  const activeItemRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current && activeItemRef.current) {
      const container = containerRef.current;
      const activeItem = activeItemRef.current;
      
      const containerWidth = container.offsetWidth;
      const itemOffset = activeItem.offsetLeft;
      const itemWidth = activeItem.offsetWidth;
      
      container.scrollTo({
        left: itemOffset - (containerWidth / 2) + (itemWidth / 2),
        behavior: "smooth"
      });
    }
  }, [activeStepIndex]);

  return (
    <div 
      ref={containerRef}
      className="flex flex-row items-center w-full overflow-x-auto no-scrollbar py-2"
    >
      {steps.map((step, index) => {
        const isActive = index === activeStepIndex;
        const isPast = index < activeStepIndex;
        const isLast = index === steps.length - 1;
        
        return (
          <div 
            key={step.stepNumber} 
            ref={isActive ? activeItemRef : null}
            className={`flex flex-row items-center group shrink-0 ${isLast ? '' : 'pr-4 xl:pr-8'}`}
          >
            {/* Timeline Node */}
            <div 
              className={`w-8 h-8 rounded-full flex items-center justify-center border text-mono-sm font-mono transition-colors duration-300 shrink-0
                ${isActive ? "bg-signal border-signal text-surface" : 
                  isPast ? "bg-ink border-ink text-surface" : 
                  "bg-transparent border-hairline text-stone"}`}
            >
              {step.stepNumber}
            </div>

            {/* Title */}
            <div className="mx-3 whitespace-nowrap">
              <p 
                className={`font-mono text-mono-sm uppercase tracking-[0.14em] transition-colors duration-300
                  ${isActive ? "text-signal" : 
                    isPast ? "text-ink" : 
                    "text-stone"}`}
              >
                {t(step.heading)}
              </p>
            </div>

            {/* Connector Line */}
            {!isLast && (
              <div 
                className={`h-px w-12 xl:w-24 transition-colors duration-300 shrink-0
                  ${isPast ? "bg-ink" : "bg-hairline/40"}`} 
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
