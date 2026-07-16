import type { Route } from "next";
import Link from "next/link";
import {
  type AnchorHTMLAttributes,
  type ButtonHTMLAttributes,
  forwardRef,
  type MouseEventHandler,
  type ReactNode,
} from "react";

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

// experimental.typedRoutes makes next/link's own prop types morph depending on
// whether .next/types has been generated (it's absent during CI's typecheck step,
// which runs before the web build), and Link's special handler typing clashes with
// exactOptionalPropertyTypes when anchor attrs are spread. An explicit prop set that
// covers real usages keeps route type-safety without either fragility.
interface ButtonLinkProps {
  href: Route;
  variant?: ButtonVariant;
  className?: string;
  children?: ReactNode;
  onClick?: MouseEventHandler<HTMLAnchorElement>;
  target?: string;
  rel?: string;
  "aria-label"?: string;
}

export function ButtonLink({
  variant = "primary",
  className = "",
  href,
  children,
  onClick,
  ...rest
}: ButtonLinkProps) {
  return (
    <Link
      href={href}
      className={`${base} ${variants[variant]} ${className}`}
      {...(onClick ? { onClick } : {})}
      {...rest}
    >
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
