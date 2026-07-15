import { forwardRef, type ButtonHTMLAttributes, type AnchorHTMLAttributes } from "react";
import { Link, type LinkProps } from "@tanstack/react-router";

type Variant = "primary" | "ghost" | "ghost-inverse";

const base =
  "inline-flex items-center justify-center gap-2 font-body text-label-sm uppercase tracking-[0.14em] px-[18px] py-[12px] transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal cursor-pointer select-none";

const variants: Record<Variant, string> = {
  primary: "bg-ink text-surface border border-ink hover:bg-surface hover:text-ink",
  ghost: "bg-transparent text-ink border border-hairline hover:bg-ink hover:text-surface",
  "ghost-inverse":
    "bg-transparent text-surface border border-surface hover:bg-surface hover:text-ink",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", className = "", ...rest }, ref) => (
    <button ref={ref} className={`${base} ${variants[variant]} ${className}`} {...rest} />
  ),
);
Button.displayName = "Button";

type ButtonLinkProps = Omit<LinkProps, "className"> & {
  variant?: Variant;
  className?: string;
  onClick?: (e: React.MouseEvent<HTMLAnchorElement>) => void;
};

export function ButtonLink({ variant = "primary", className = "", ...rest }: ButtonLinkProps) {
  return <Link className={`${base} ${variants[variant]} ${className}`} {...(rest as LinkProps)} />;
}

interface ButtonAnchorProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  variant?: Variant;
}

export function ButtonAnchor({ variant = "primary", className = "", ...rest }: ButtonAnchorProps) {
  return <a className={`${base} ${variants[variant]} ${className}`} {...rest} />;
}
