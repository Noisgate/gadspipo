import type { ReactNode } from "react";

function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

type ButtonProps = {
  children: ReactNode;
  href?: string;
  variant?: "primary" | "secondary";
  type?: "button" | "submit" | "reset";
  disabled?: boolean;
};

export function Button({
  children,
  href,
  variant = "primary",
  type = "button",
  disabled = false,
}: ButtonProps) {
  const className = cx("button", variant);

  if (href && !disabled) {
    return (
      <a className={className} href={href}>
        {children}
      </a>
    );
  }

  return (
    <button className={className} disabled={disabled} type={type}>
      {children}
    </button>
  );
}

type CardProps = {
  children: ReactNode;
  accent?: "default" | "soft";
};

export function Card({ children, accent = "default" }: CardProps) {
  return <div className={cx("card", accent === "soft" && "soft")}>{children}</div>;
}

type SectionHeadingProps = {
  eyebrow: string;
  title: string;
  description: string;
};

export function SectionHeading({
  eyebrow,
  title,
  description,
}: SectionHeadingProps) {
  return (
    <div className="section-heading">
      <p className="section-eyebrow">{eyebrow}</p>
      <h2 className="section-title">{title}</h2>
      <p className="section-description">{description}</p>
    </div>
  );
}

type StatusPillProps = {
  children: ReactNode;
  tone?: "neutral" | "outline" | "success" | "warning";
};

export function StatusPill({
  children,
  tone = "neutral",
}: StatusPillProps) {
  return <span className={cx("status-pill", tone)}>{children}</span>;
}
