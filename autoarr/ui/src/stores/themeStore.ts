/**
 * AutoArr Theme Store
 *
 * Zustand store for managing theme state with persistence.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { ThemePreset, ThemeState, ThemeImportResult } from '../theme/types';
import { BUILT_IN_PRESETS, getDefaultPreset, isBuiltInPreset } from '../theme/presets';
import { applyTheme, applyAccentHue, resetAccentHue } from '../theme/generator';

/**
 * Theme store interface
 */
interface ThemeStore extends ThemeState {
  // Computed
  activeTheme: ThemePreset | null;

  // Actions
  setTheme: (themeId: string) => void;
  setAccentHue: (hue: number | null) => void;
  addCustomTheme: (theme: ThemePreset) => void;
  removeCustomTheme: (themeId: string) => void;
  importTheme: (json: string) => ThemeImportResult;
  exportTheme: (themeId: string) => string | null;
  resetToDefault: () => void;

  // Internal
  _initializeTheme: () => void;
  _getTheme: (themeId: string) => ThemePreset | null;

  // Legacy compatibility
  isDarkMode: boolean;
  toggleDarkMode: () => void;
  setDarkMode: (value: boolean) => void;
}

/**
 * Get a theme by ID from either built-in or custom themes
 */
function findTheme(themeId: string, customThemes: ThemePreset[]): ThemePreset | null {
  // Check built-in first
  if (isBuiltInPreset(themeId)) {
    return BUILT_IN_PRESETS[themeId];
  }
  // Check custom themes
  return customThemes.find((t) => t.id === themeId) || null;
}

/**
 * Validate a theme preset structure
 */
function validateTheme(theme: unknown): theme is ThemePreset {
  if (typeof theme !== 'object' || theme === null) return false;
  const t = theme as Record<string, unknown>;

  // Required fields
  if (typeof t.id !== 'string' || !t.id) return false;
  if (typeof t.name !== 'string' || !t.name) return false;
  if (t.mode !== 'dark' && t.mode !== 'light') return false;
  if (typeof t.colors !== 'object' || t.colors === null) return false;

  // Validate colors has required fields
  const colors = t.colors as Record<string, unknown>;
  const requiredColors = ['mainBg', 'modalBg', 'buttonColor', 'accentColor', 'text'];
  for (const key of requiredColors) {
    if (typeof colors[key] !== 'string') return false;
  }

  return true;
}

/**
 * Create the theme store
 */
export const useThemeStore = create<ThemeStore>()(
  persist(
    (set, get) => ({
      // Initial state
      activeThemeId: 'autoarr-dark',
      accentHue: null,
      customThemes: [],

      // Computed: get active theme object
      get activeTheme() {
        const { activeThemeId, customThemes } = get();
        return findTheme(activeThemeId, customThemes);
      },

      // Legacy compatibility
      get isDarkMode() {
        const theme = get().activeTheme;
        return theme ? theme.mode === 'dark' : true;
      },

      /**
       * Set the active theme by ID
       */
      setTheme: (themeId: string) => {
        const { customThemes, accentHue } = get();
        const theme = findTheme(themeId, customThemes);

        if (!theme) {
          console.warn(`Theme not found: ${themeId}`);
          return;
        }

        // Apply theme to DOM
        applyTheme(theme);

        // Apply custom accent if set
        if (accentHue !== null) {
          applyAccentHue(accentHue);
        }

        // Update document dark mode class
        if (theme.mode === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }

        set({ activeThemeId: themeId });
      },

      /**
       * Set custom accent hue (0-360) or null to use theme default
       */
      setAccentHue: (hue: number | null) => {
        const { activeTheme } = get();

        if (hue !== null) {
          // Clamp hue to valid range
          const clampedHue = Math.max(0, Math.min(360, hue));
          applyAccentHue(clampedHue);
          set({ accentHue: clampedHue });
        } else {
          // Reset to theme default
          if (activeTheme) {
            resetAccentHue(activeTheme);
          }
          set({ accentHue: null });
        }
      },

      /**
       * Add a custom theme
       */
      addCustomTheme: (theme: ThemePreset) => {
        const { customThemes } = get();

        // Ensure unique ID
        const existingIds = new Set([
          ...Object.keys(BUILT_IN_PRESETS),
          ...customThemes.map((t) => t.id),
        ]);

        let finalId = theme.id;
        if (existingIds.has(finalId)) {
          finalId = `${theme.id}-${Date.now()}`;
        }

        const themeWithId = { ...theme, id: finalId };
        set({ customThemes: [...customThemes, themeWithId] });
      },

      /**
       * Remove a custom theme
       */
      removeCustomTheme: (themeId: string) => {
        const { customThemes, activeThemeId } = get();

        // Can't remove built-in themes
        if (isBuiltInPreset(themeId)) {
          console.warn('Cannot remove built-in theme');
          return;
        }

        const newCustomThemes = customThemes.filter((t) => t.id !== themeId);

        // If removing the active theme, switch to default
        if (activeThemeId === themeId) {
          const defaultTheme = getDefaultPreset();
          applyTheme(defaultTheme);
          set({
            customThemes: newCustomThemes,
            activeThemeId: defaultTheme.id,
          });
        } else {
          set({ customThemes: newCustomThemes });
        }
      },

      /**
       * Import a theme from JSON string
       */
      importTheme: (json: string): ThemeImportResult => {
        try {
          const data = JSON.parse(json);

          // Handle both direct preset and export format
          const preset = data.preset || data;

          if (!validateTheme(preset)) {
            return { success: false, error: 'Invalid theme structure' };
          }

          // Add to custom themes
          get().addCustomTheme(preset);

          return { success: true, theme: preset };
        } catch (e) {
          return {
            success: false,
            error: e instanceof Error ? e.message : 'Invalid JSON format',
          };
        }
      },

      /**
       * Export a theme as JSON string
       */
      exportTheme: (themeId: string): string | null => {
        const { customThemes, accentHue } = get();
        const theme = findTheme(themeId, customThemes);

        if (!theme) return null;

        const exportData = {
          version: '1.0' as const,
          type: 'autoarr-theme' as const,
          preset: theme,
          accentHue: accentHue,
          exportedAt: new Date().toISOString(),
        };

        return JSON.stringify(exportData, null, 2);
      },

      /**
       * Reset to default theme and settings
       */
      resetToDefault: () => {
        const defaultTheme = getDefaultPreset();
        applyTheme(defaultTheme);
        document.documentElement.classList.add('dark');
        set({
          activeThemeId: defaultTheme.id,
          accentHue: null,
        });
      },

      /**
       * Initialize theme on app start
       */
      _initializeTheme: () => {
        const { activeThemeId, customThemes, accentHue } = get();
        const theme = findTheme(activeThemeId, customThemes);

        if (theme) {
          applyTheme(theme);
          if (accentHue !== null) {
            applyAccentHue(accentHue);
          }
          if (theme.mode === 'dark') {
            document.documentElement.classList.add('dark');
          } else {
            document.documentElement.classList.remove('dark');
          }
        } else {
          // Fallback to default
          const defaultTheme = getDefaultPreset();
          applyTheme(defaultTheme);
          document.documentElement.classList.add('dark');
          set({ activeThemeId: defaultTheme.id });
        }
      },

      /**
       * Get theme by ID (internal helper)
       */
      _getTheme: (themeId: string): ThemePreset | null => {
        const { customThemes } = get();
        return findTheme(themeId, customThemes);
      },

      // Legacy compatibility methods
      toggleDarkMode: () => {
        const { activeTheme } = get();
        if (activeTheme?.mode === 'dark') {
          get().setTheme('autoarr-light');
        } else {
          get().setTheme('autoarr-dark');
        }
      },

      setDarkMode: (value: boolean) => {
        if (value) {
          get().setTheme('autoarr-dark');
        } else {
          get().setTheme('autoarr-light');
        }
      },
    }),
    {
      name: 'autoarr-theme-v2',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        activeThemeId: state.activeThemeId,
        accentHue: state.accentHue,
        customThemes: state.customThemes,
      }),
    }
  )
);

/**
 * Hook to get all available themes (built-in + custom)
 */
export function useAllThemes(): ThemePreset[] {
  const customThemes = useThemeStore((state) => state.customThemes);
  return [...Object.values(BUILT_IN_PRESETS), ...customThemes];
}

/**
 * Hook to get built-in themes only
 */
export function useBuiltInThemes(): ThemePreset[] {
  return Object.values(BUILT_IN_PRESETS);
}

/**
 * Hook to check if current theme is custom
 */
export function useIsCustomTheme(): boolean {
  const activeThemeId = useThemeStore((state) => state.activeThemeId);
  return !isBuiltInPreset(activeThemeId);
}
