import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#080C14",
        surface: {
          50: "#1E293B",
          100: "#172033",
          200: "#111827",
          300: "#0D131F",
        },
        brand: {
          primary: "#3B82F6",
          accent: "#6366F1",
          success: "#10B981",
          warning: "#F59E0B",
          danger: "#EF4444",
        },
      },
      fontFamily: {
        mono: ["var(--font-geist-mono)", "ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
        sans: ["var(--font-geist-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 25px -5px rgba(59, 130, 246, 0.25)",
        "glow-danger": "0 0 25px -5px rgba(239, 68, 68, 0.25)",
        "glow-success": "0 0 25px -5px rgba(16, 185, 129, 0.25)",
      },
    },
  },
  plugins: [],
};
export default config;
