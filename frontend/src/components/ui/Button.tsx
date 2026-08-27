import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  variant?: "primary" | "secondary" | "outline" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  className?: string;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  className = "",
  disabled,
  ...props
}) => {
  const variantStyles = {
    primary: "bg-blue-600 hover:bg-blue-500 text-white shadow-sm border border-blue-400/20 active:scale-[0.98]",
    secondary: "bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700 active:scale-[0.98]",
    outline: "bg-transparent hover:bg-slate-850 text-slate-200 border border-slate-700 hover:border-slate-600",
    danger: "bg-rose-600 hover:bg-rose-500 text-white border border-rose-400/20 active:scale-[0.98]",
    ghost: "bg-transparent hover:bg-slate-800/60 text-slate-300 hover:text-white",
  };

  const sizeStyles = {
    sm: "px-3 py-1.5 text-xs font-medium rounded-lg",
    md: "px-4 py-2 text-sm font-medium rounded-lg",
    lg: "px-5 py-2.5 text-base font-semibold rounded-xl",
  };

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 transition-all duration-150 select-none disabled:opacity-50 disabled:pointer-events-none ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};
