/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // AutoArr brand colors from Lovable design
        primary: {
          DEFAULT: '#6366f1',
          dark: '#4f46e5',
          glow: '#8b5cf6',
          light: '#818cf8',
        },
        accent: {
          DEFAULT: '#3b82f6',
          light: '#60a5fa',
        },
        background: {
          primary: '#1a1f2e',
          secondary: '#242938',
          tertiary: '#2d3348',
        },
        text: {
          primary: '#f8fafc',
          secondary: '#94a3b8',
          muted: '#64748b',
        },
        status: {
          success: '#10b981',
          warning: '#f59e0b',
          error: '#ef4444',
          offline: '#ef4444',
        },
      },
      boxShadow: {
        glow: '0 0 40px rgba(99, 102, 241, 0.3)',
        'glow-lg': '0 0 60px rgba(99, 102, 241, 0.4)',
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #6366f1, #8b5cf6)',
        'gradient-hero': 'linear-gradient(180deg, #1a1f2e, #242938)',
      },
    },
  },
  plugins: [],
}
