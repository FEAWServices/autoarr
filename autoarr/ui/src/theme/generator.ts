/**
 * AutoArr Theme Generator
 *
 * Utilities for applying themes to the DOM by setting CSS custom properties.
 */

import type { ThemePreset, ThemeColors } from './types';

/**
 * Map of theme color keys to CSS variable names
 */
const COLOR_VAR_MAP: Record<keyof ThemeColors, string> = {
  mainBg: '--main-bg-color',
  modalBg: '--modal-bg-color',
  modalHeader: '--modal-header-color',
  buttonColor: '--button-color',
  buttonText: '--button-text',
  accentColor: '--accent-color',
  text: '--text',
  textMuted: '--text-muted',
  linkColor: '--link-color',
  linkColorHover: '--link-color-hover',
  success: '--aa-success',
  warning: '--aa-warning',
  error: '--aa-error',
  info: '--aa-info',
  borderColor: '--aa-border',
};

/**
 * Apply a theme preset to the document
 */
export function applyTheme(theme: ThemePreset): void {
  const root = document.documentElement;

  // Add loading class to prevent transition flash
  root.classList.add('theme-loading');

  // Apply all color variables
  for (const [key, cssVar] of Object.entries(COLOR_VAR_MAP)) {
    const colorKey = key as keyof ThemeColors;
    const value = theme.colors[colorKey];
    if (value) {
      root.style.setProperty(cssVar, value);
    }
  }

  // Set computed hover colors
  root.style.setProperty('--button-color-hover', adjustBrightness(theme.colors.buttonColor, 0.9));
  root.style.setProperty('--accent-color-hover', adjustBrightness(theme.colors.accentColor, 1.15));

  // Set text secondary (derive from text if not set)
  root.style.setProperty('--aa-text-secondary', theme.mode === 'dark' ? '#94a3b8' : '#64748b');

  // Set status light variants
  root.style.setProperty('--aa-success-light', adjustBrightness(theme.colors.success, 1.2));
  root.style.setProperty('--aa-warning-light', adjustBrightness(theme.colors.warning, 1.2));
  root.style.setProperty('--aa-error-light', adjustBrightness(theme.colors.error, 1.2));
  root.style.setProperty('--aa-info-light', adjustBrightness(theme.colors.info, 1.2));

  // Set border colors based on mode
  if (theme.mode === 'dark') {
    root.style.setProperty('--aa-border', 'rgba(100, 116, 139, 0.2)');
    root.style.setProperty('--aa-border-strong', 'rgba(100, 116, 139, 0.4)');
    root.style.setProperty('--aa-glass-bg', 'rgba(26, 31, 46, 0.8)');
    root.style.setProperty('--aa-glass-border', 'rgba(255, 255, 255, 0.1)');
  } else {
    root.style.setProperty('--aa-border', 'rgba(0, 0, 0, 0.1)');
    root.style.setProperty('--aa-border-strong', 'rgba(0, 0, 0, 0.2)');
    root.style.setProperty('--aa-glass-bg', 'rgba(255, 255, 255, 0.8)');
    root.style.setProperty('--aa-glass-border', 'rgba(0, 0, 0, 0.1)');
  }

  // Set gradients
  root.style.setProperty(
    '--aa-gradient-primary',
    `linear-gradient(135deg, ${theme.colors.accentColor} 0%, ${adjustBrightness(
      theme.colors.accentColor,
      1.15
    )} 100%)`
  );
  root.style.setProperty(
    '--aa-gradient-hero',
    `linear-gradient(180deg, ${theme.colors.mainBg} 0%, ${theme.colors.modalBg} 100%)`
  );

  // Update theme mode class
  root.classList.remove('theme-dark', 'theme-light');
  root.classList.add(`theme-${theme.mode}`);

  // Set color-scheme for native elements
  root.style.setProperty('color-scheme', theme.mode === 'light' ? 'light' : 'dark');

  // Set data attribute for theme identification
  root.setAttribute('data-theme', theme.id);

  // Remove loading class after a frame to enable transitions
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      root.classList.remove('theme-loading');
    });
  });
}

/**
 * Apply custom accent hue on top of current theme
 */
export function applyAccentHue(hue: number): void {
  const root = document.documentElement;
  root.style.setProperty('--accent-hue', hue.toString());

  // Update accent-dependent colors
  const saturation = 84;
  const lightness = 60;

  const accentColor = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
  const accentHover = `hsl(${hue}, ${saturation}%, ${lightness + 10}%)`;

  root.style.setProperty('--accent-custom', accentColor);
  root.style.setProperty('--accent-custom-hover', accentHover);
  root.style.setProperty(
    '--accent-custom-glow',
    `hsla(${hue}, ${saturation}%, ${lightness}%, 0.3)`
  );

  // Update glow shadows
  root.style.setProperty(
    '--aa-shadow-glow',
    `0 0 40px hsla(${hue}, ${saturation}%, ${lightness}%, 0.3)`
  );
  root.style.setProperty(
    '--aa-shadow-glow-lg',
    `0 0 60px hsla(${hue}, ${saturation}%, ${lightness}%, 0.4)`
  );

  // Update mesh gradient
  root.style.setProperty(
    '--aa-gradient-mesh',
    `radial-gradient(at 40% 20%, hsla(${hue}, 70%, 50%, 0.3) 0px, transparent 50%),
     radial-gradient(at 80% 0%, hsla(${hue + 10}, 80%, 60%, 0.3) 0px, transparent 50%),
     radial-gradient(at 0% 50%, hsla(${hue - 10}, 60%, 40%, 0.3) 0px, transparent 50%)`
  );
}

/**
 * Reset accent to theme default (remove custom hue)
 */
export function resetAccentHue(theme: ThemePreset): void {
  const root = document.documentElement;

  // Extract hue from theme's accent color
  const defaultHue = extractHueFromColor(theme.colors.accentColor);
  root.style.setProperty('--accent-hue', defaultHue.toString());

  // Reset to theme's accent color
  root.style.setProperty('--accent-custom', theme.colors.accentColor);
  root.style.setProperty('--accent-custom-hover', adjustBrightness(theme.colors.accentColor, 1.15));

  // Reset glow shadows
  const rgb = hexToRgb(theme.colors.accentColor);
  if (rgb) {
    root.style.setProperty('--aa-shadow-glow', `0 0 40px rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.3)`);
    root.style.setProperty(
      '--aa-shadow-glow-lg',
      `0 0 60px rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.4)`
    );
  }
}

/**
 * Get current theme ID from document
 */
export function getCurrentThemeId(): string | null {
  return document.documentElement.getAttribute('data-theme');
}

/**
 * Check if document is in dark mode
 */
export function isDarkMode(): boolean {
  return document.documentElement.classList.contains('theme-dark');
}

// ============================================
// Color Utility Functions
// ============================================

/**
 * Adjust brightness of a hex color
 */
function adjustBrightness(hex: string, factor: number): string {
  const rgb = hexToRgb(hex);
  if (!rgb) return hex;

  const adjust = (value: number) => Math.min(255, Math.max(0, Math.round(value * factor)));

  return rgbToHex(adjust(rgb.r), adjust(rgb.g), adjust(rgb.b));
}

/**
 * Convert hex color to RGB object
 */
function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  // Handle both #RGB and #RRGGBB formats
  const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
  const fullHex = hex.replace(shorthandRegex, (_m, r, g, b) => r + r + g + g + b + b);

  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(fullHex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
}

/**
 * Convert RGB values to hex color
 */
function rgbToHex(r: number, g: number, b: number): string {
  const toHex = (value: number) => {
    const hex = value.toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  };
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

/**
 * Extract hue from a hex color
 */
function extractHueFromColor(hex: string): number {
  const rgb = hexToRgb(hex);
  if (!rgb) return 239; // Default indigo hue

  const r = rgb.r / 255;
  const g = rgb.g / 255;
  const b = rgb.b / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const delta = max - min;

  let hue = 0;

  if (delta !== 0) {
    if (max === r) {
      hue = ((g - b) / delta) % 6;
    } else if (max === g) {
      hue = (b - r) / delta + 2;
    } else {
      hue = (r - g) / delta + 4;
    }
  }

  hue = Math.round(hue * 60);
  if (hue < 0) hue += 360;

  return hue;
}

/**
 * Generate CSS for a theme (useful for export/preview)
 */
export function generateThemeCSS(theme: ThemePreset): string {
  const lines: string[] = [`:root[data-theme="${theme.id}"] {`];

  for (const [key, cssVar] of Object.entries(COLOR_VAR_MAP)) {
    const colorKey = key as keyof ThemeColors;
    const value = theme.colors[colorKey];
    if (value) {
      lines.push(`  ${cssVar}: ${value};`);
    }
  }

  lines.push('}');
  return lines.join('\n');
}
