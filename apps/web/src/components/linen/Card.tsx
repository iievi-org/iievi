import { type HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "open" | "paper";
}

export function Card({ variant = "open", className = "", ...rest }: CardProps) {
  const bg = variant === "paper" ? "bg-neutral" : "bg-transparent";
  return <div className={`${bg} border border-hairline p-8 ${className}`} {...rest} />;
}
