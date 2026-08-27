import React from "react";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "primary" | "success" | "warning" | "danger" | "neutral" | "outline" | "info" | "default";
  size?: "sm" | "md";
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "neutral",
  size = "md",
  className = "",
}) => {
  const variantStyles = {
    primary: "bg-blue-500/10 text-blue-400 border border-blue-500/30",
    info: "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30",
    success: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30",
    warning: "bg-amber-500/10 text-amber-400 border border-amber-500/30",
    danger: "bg-rose-500/10 text-rose-400 border border-rose-500/30",
    neutral: "bg-slate-800 text-slate-300 border border-slate-700",
    outline: "bg-transparent text-slate-300 border border-slate-700/80",
    default: "bg-slate-900 text-slate-200 border border-slate-700",
  };

  const sizeStyles = {
    sm: "px-2 py-0.5 text-xs font-medium rounded-md",
    md: "px-2.5 py-1 text-xs font-semibold rounded-lg",
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 tracking-wide ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </span>
  );
};
