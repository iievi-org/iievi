export function Rule({ className = "" }: { className?: string }) {
  return <hr className={`w-full border-0 border-t border-hairline ${className}`} />;
}
