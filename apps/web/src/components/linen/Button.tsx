import Link from "next/link";
import { type AnchorHTMLAttributes, type ButtonHTMLAttributes, type ComponentProps, forwardRef } from "react";

export type ButtonVariant = "primary" | "ghost" | "ghost-inverse";

const base =
  "inline-flex items-center justify-center gap-2 font-body text-label-sm uppercase tracking-[0.14em] px-[18px] py-[12px] transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal cursor-pointer select-none disabled:opacity-50 disabled:cursor-not-allowed";

const variants: Record<ButtonVariant, string> = {
  primary: "bg-ink text-surface border border-ink hover:bg-surface hover:text-ink",
  ghost: "bg-transparent text-ink border border-hairline hover:bg-ink hover:text-surface",
  "ghost-inverse": "bg-transparent text-surface border border-surface hover:bg-surface hover:text-ink",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", className = "", type = "button", ...rest }, ref) => (
    <button ref={ref} type={type} className={`${base} ${variants[variant]} ${className}`} {...rest} />
  ),
);
Button.displayName = "Button";

// `ComponentProps<typeof Link>` (not `LinkProps`) — with experimental.typedRoutes,
// LinkProps becomes generic; this captures the typed href + anchor props cleanly.
type ButtonLinkProps = ComponentProps<typeof Link> & {
  variant?: ButtonVariant;
};

export function ButtonLink({ variant = "primary", className = "", children, ...rest }: ButtonLinkProps) {
  return (
    <Link className={`${base} ${variants[variant]} ${className}`} {...rest}>
      {children}
    </Link>
  );
}

interface ButtonAnchorProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  variant?: ButtonVariant;
}

export function ButtonAnchor({ variant = "primary", className = "", ...rest }: ButtonAnchorProps) {
  return <a className={`${base} ${variants[variant]} ${className}`} {...rest} />;
}
