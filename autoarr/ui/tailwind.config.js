/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // AutoArr brand colors - enhanced for modern UI
        primary: {
          50: "#f5f3ff",
          100: "#ede9fe",
          200: "#ddd6fe",
          300: "#c4b5fd",
          400: "#a78bfa",
          500: "#8b5cf6",
          DEFAULT: "#6366f1",
          600: "#7c3aed",
          700: "#6d28d9",
          800: "#5b21b6",
          900: "#4c1d95",
          950: "#2e1065",
        },
        accent: {
          DEFAULT: "#3b82f6",
          light: "#60a5fa",
          dark: "#1e40af",
        },
        background: {
          primary: "#0f1419",
          secondary: "#1a1f2e",
          tertiary: "#242938",
          elevated: "#2d3348",
        },
        text: {
          primary: "#f8fafc",
          secondary: "#94a3b8",
          muted: "#64748b",
        },
        status: {
          success: "#10b981",
          warning: "#f59e0b",
          error: "#ef4444",
          info: "#3b82f6",
          offline: "#ef4444",
        },
      },
      boxShadow: {
        glow: "0 0 40px rgba(99, 102, 241, 0.3)",
        "glow-lg": "0 0 60px rgba(99, 102, 241, 0.4)",
        "glow-xl": "0 0 80px rgba(99, 102, 241, 0.5)",
        glass: "0 8px 32px 0 rgba(31, 38, 135, 0.37)",
        "glass-hover": "0 12px 40px 0 rgba(31, 38, 135, 0.45)",
      },
      backgroundImage: {
        "gradient-primary": "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
        "gradient-secondary":
          "linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)",
        "gradient-hero": "linear-gradient(180deg, #0f1419 0%, #1a1f2e 100%)",
        "gradient-mesh":
          "radial-gradient(at 40% 20%, hsla(250, 70%, 50%, 0.3) 0px, transparent 50%), radial-gradient(at 80% 0%, hsla(260, 80%, 60%, 0.3) 0px, transparent 50%), radial-gradient(at 0% 50%, hsla(240, 60%, 40%, 0.3) 0px, transparent 50%)",
      },
      backdropBlur: {
        xs: "2px",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-in-out",
        "slide-up": "slideUp 0.4s ease-out",
        "slide-down": "slideDown 0.4s ease-out",
        "scale-in": "scaleIn 0.3s ease-out",
        float: "float 6s ease-in-out infinite",
        shimmer: "shimmer 2s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        slideDown: {
          "0%": { transform: "translateY(-10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        scaleIn: {
          "0%": { transform: "scale(0.9)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
        shimmer: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
      },
    },
  },
  plugins: [],
};
