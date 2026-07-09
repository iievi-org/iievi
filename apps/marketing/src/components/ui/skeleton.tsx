import { cn } from "@/lib/utils";

function Skeleton({ className, children, id, style, role, "aria-hidden": ariaHidden, "aria-label": ariaLabel, title }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("animate-pulse rounded-md bg-primary/10", className)} id={id} style={style} role={role} aria-hidden={ariaHidden} aria-label={ariaLabel} title={title}>{children}</div>;
}

export { Skeleton };
