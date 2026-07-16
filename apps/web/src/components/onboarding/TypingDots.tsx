/** Three-dot typing indicator, styled as an AI chat bubble. */
export function TypingDots() {
  return (
    <div
      className="flex w-fit items-center gap-1 border border-hairline bg-neutral px-3 py-3"
      aria-label="Assistant is typing"
      role="status"
    >
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 animate-bounce rounded-full bg-stone"
          style={{ animationDelay: `${i * 150}ms` }}
        />
      ))}
    </div>
  );
}
