/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      colors: {
        // ============================================
        // HSL-based Design System (from temp-branding)
        // ============================================
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',

        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
          glow: 'hsl(var(--primary-glow))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        sidebar: {
          DEFAULT: 'hsl(var(--sidebar-background))',
          foreground: 'hsl(var(--sidebar-foreground))',
          primary: 'hsl(var(--sidebar-primary))',
          'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
          accent: 'hsl(var(--sidebar-accent))',
          'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
          border: 'hsl(var(--sidebar-border))',
          ring: 'hsl(var(--sidebar-ring))',
        },

        // ============================================
        // Surface Colors (aliases for convenience)
        // ============================================
        surface: {
          base: 'var(--aa-surface-base)',
          raised: 'var(--aa-surface-raised)',
          elevated: 'var(--aa-surface-elevated)',
          overlay: 'var(--aa-surface-overlay)',
        },

        // ============================================
        // Content/Text Colors
        // ============================================
        content: {
          primary: 'var(--aa-text-primary)',
          secondary: 'var(--aa-text-secondary)',
          muted: 'var(--aa-text-muted)',
        },

        // ============================================
        // Status Colors
        // ============================================
        'status-success': 'var(--aa-success)',
        'status-warning': 'var(--aa-warning)',
        'status-error': 'var(--aa-error)',
        'status-info': 'var(--aa-info)',
      },

      // ============================================
      // Border Radius (more curved, modern look)
      // ============================================
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
        'theme-sm': 'var(--aa-radius-sm)',
        'theme-md': 'var(--aa-radius-md)',
        'theme-lg': 'var(--aa-radius-lg)',
        'theme-xl': 'var(--aa-radius-xl)',
      },

      // ============================================
      // Box Shadows with Glow Effects
      // ============================================
      boxShadow: {
        // Theme shadows
        'theme-sm': 'var(--aa-shadow-sm)',
        'theme-md': 'var(--aa-shadow-md)',
        'theme-lg': 'var(--aa-shadow-lg)',
        'theme-xl': 'var(--aa-shadow-xl)',
        'theme-glow': 'var(--aa-shadow-glow)',
        'theme-glow-lg': 'var(--aa-shadow-glow-lg)',
        // Purple glow effects (matching temp-branding)
        glow: '0 0 40px rgba(168, 85, 247, 0.3)',
        'glow-lg': '0 0 60px rgba(168, 85, 247, 0.4)',
        'glow-xl': '0 0 80px rgba(168, 85, 247, 0.5)',
        'glow-hover': '0 0 30px rgba(168, 85, 247, 0.3)',
        // Glass effect
        glass: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        'glass-hover': '0 12px 40px 0 rgba(31, 38, 135, 0.45)',
      },

      // ============================================
      // Background Images & Gradients
      // ============================================
      backgroundImage: {
        // Theme gradients
        'theme-gradient-primary': 'var(--aa-gradient-primary)',
        'theme-gradient-secondary': 'var(--aa-gradient-secondary)',
        'theme-gradient-hero': 'var(--aa-gradient-hero)',
        'theme-gradient-mesh': 'var(--aa-gradient-mesh)',
        // Direct gradients
        'gradient-primary': 'linear-gradient(135deg, hsl(280 85% 60%), hsl(320 85% 65%))',
        'gradient-secondary': 'linear-gradient(135deg, hsl(260 70% 50%), hsl(280 85% 60%))',
        'gradient-hero': 'linear-gradient(180deg, hsl(222 47% 11%), hsl(280 50% 15%))',
        'gradient-mesh':
          'radial-gradient(at 40% 20%, hsla(280, 85%, 60%, 0.3) 0px, transparent 50%), radial-gradient(at 80% 0%, hsla(290, 90%, 70%, 0.3) 0px, transparent 50%), radial-gradient(at 0% 50%, hsla(260, 70%, 50%, 0.3) 0px, transparent 50%)',
      },

      // ============================================
      // Backdrop Blur
      // ============================================
      backdropBlur: {
        xs: '2px',
        theme: 'var(--aa-glass-blur)',
      },

      // ============================================
      // Animations (smooth, engaging)
      // ============================================
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'slide-down': 'slideDown 0.4s ease-out',
        'scale-in': 'scaleIn 0.3s ease-out',
        float: 'float 6s ease-in-out infinite',
        shimmer: 'shimmer 2s linear infinite',
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.9)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
      },

      // ============================================
      // Spacing (generous padding like temp-branding)
      // ============================================
      spacing: {
        18: '4.5rem',
        22: '5.5rem',
      },
    },
  },
  plugins: [],
};
