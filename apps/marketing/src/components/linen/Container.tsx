import { type ReactNode } from "react";

export function Container({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`max-w-[1280px] mx-auto px-6 md:px-10 ${className}`}>{children}</div>;
}

export function Section({
  children,
  className = "",
  inset = false,
  id,
}: {
  children: ReactNode;
  className?: string;
  inset?: boolean;
  id?: string;
}) {
  return (
    <section id={id} className={`${inset ? "bg-neutral" : ""} py-16 md:py-24 ${className}`}>
      <Container>{children}</Container>
    </section>
  );
}
