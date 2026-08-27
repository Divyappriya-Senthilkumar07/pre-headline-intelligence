import React from "react";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  variant?: "default" | "glass" | "glow" | "danger" | "success";
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = "default",
  className = "",
  ...props
}) => {
  const variantStyles = {
    default: "bg-surface-200 border border-surface-50/50 shadow-sm",
    glass: "glass-panel shadow-md",
    glow: "bg-surface-200 border border-brand-primary/40 shadow-glow",
    danger: "bg-surface-200 border border-brand-danger/40 shadow-glow-danger",
    success: "bg-surface-200 border border-brand-success/40 shadow-glow-success",
  };

  return (
    <div
      className={`rounded-xl p-5 transition-all duration-200 ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
