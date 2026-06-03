/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: { DEFAULT: "#0a0e1a", 1: "#0f1523", 2: "#141c2e", 3: "#1a2540", border: "#1e2d4a" },
        accent: { DEFAULT: "#3b82f6", dim: "#1d4ed8", glow: "#60a5fa" },
        success: "#10b981", warning: "#f59e0b", danger: "#ef4444",
        muted: "#64748b", text: { DEFAULT: "#e2e8f0", dim: "#94a3b8" },
      },
      fontFamily: {
        sans: ["'Inter'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
