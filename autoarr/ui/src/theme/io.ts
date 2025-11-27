/**
 * AutoArr Theme I/O
 *
 * Import/export utilities for theme files.
 */

import type { ThemePreset, ThemeExportFormat, ThemeImportResult } from './types';

/**
 * Export a theme to a downloadable JSON file
 */
export function downloadThemeAsFile(theme: ThemePreset, accentHue?: number | null): void {
  const exportData: ThemeExportFormat = {
    version: '1.0',
    type: 'autoarr-theme',
    preset: theme,
    accentHue: accentHue ?? undefined,
    exportedAt: new Date().toISOString(),
  };

  const json = JSON.stringify(exportData, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = `${theme.id}.autoarr-theme.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  URL.revokeObjectURL(url);
}

/**
 * Read a theme file and parse it
 */
export function readThemeFile(file: File): Promise<ThemeImportResult> {
  return new Promise((resolve) => {
    const reader = new FileReader();

    reader.onload = (event) => {
      try {
        const text = event.target?.result as string;
        const data = JSON.parse(text);

        // Handle both direct preset and export format
        const preset = data.preset || data;

        if (!isValidTheme(preset)) {
          resolve({ success: false, error: 'Invalid theme file structure' });
          return;
        }

        resolve({ success: true, theme: preset });
      } catch {
        resolve({ success: false, error: 'Failed to parse theme file' });
      }
    };

    reader.onerror = () => {
      resolve({ success: false, error: 'Failed to read file' });
    };

    reader.readAsText(file);
  });
}

/**
 * Parse a theme from JSON string
 */
export function parseThemeJSON(json: string): ThemeImportResult {
  try {
    const data = JSON.parse(json);

    // Handle both direct preset and export format
    const preset = data.preset || data;

    if (!isValidTheme(preset)) {
      return { success: false, error: 'Invalid theme structure' };
    }

    return { success: true, theme: preset };
  } catch {
    return { success: false, error: 'Invalid JSON format' };
  }
}

/**
 * Validate a theme object has required fields
 */
function isValidTheme(theme: unknown): theme is ThemePreset {
  if (typeof theme !== 'object' || theme === null) return false;

  const t = theme as Record<string, unknown>;

  // Check required top-level fields
  if (typeof t.id !== 'string' || !t.id) return false;
  if (typeof t.name !== 'string' || !t.name) return false;
  if (t.mode !== 'dark' && t.mode !== 'light') return false;

  // Check colors object
  if (typeof t.colors !== 'object' || t.colors === null) return false;

  const colors = t.colors as Record<string, unknown>;
  const requiredColors = ['mainBg', 'modalBg', 'buttonColor', 'accentColor', 'text'];

  for (const key of requiredColors) {
    if (typeof colors[key] !== 'string') return false;
  }

  return true;
}

/**
 * Generate a shareable URL with theme data (compressed)
 * Note: Only works for small themes due to URL length limits
 */
export function generateShareUrl(theme: ThemePreset): string | null {
  try {
    const minimalData = {
      id: theme.id,
      name: theme.name,
      mode: theme.mode,
      colors: theme.colors,
    };

    const json = JSON.stringify(minimalData);
    const encoded = btoa(encodeURIComponent(json));

    // Check if URL would be too long (most browsers limit to ~2000 chars)
    if (encoded.length > 1500) {
      return null;
    }

    return `${window.location.origin}/settings?theme=${encoded}`;
  } catch {
    return null;
  }
}

/**
 * Parse a theme from a share URL
 */
export function parseShareUrl(url: string): ThemeImportResult {
  try {
    const urlObj = new URL(url);
    const themeParam = urlObj.searchParams.get('theme');

    if (!themeParam) {
      return { success: false, error: 'No theme data in URL' };
    }

    const json = decodeURIComponent(atob(themeParam));
    return parseThemeJSON(json);
  } catch {
    return { success: false, error: 'Failed to parse theme URL' };
  }
}

/**
 * Copy theme JSON to clipboard
 */
export async function copyThemeToClipboard(
  theme: ThemePreset,
  accentHue?: number | null
): Promise<boolean> {
  try {
    const exportData: ThemeExportFormat = {
      version: '1.0',
      type: 'autoarr-theme',
      preset: theme,
      accentHue: accentHue ?? undefined,
      exportedAt: new Date().toISOString(),
    };

    const json = JSON.stringify(exportData, null, 2);
    await navigator.clipboard.writeText(json);
    return true;
  } catch {
    return false;
  }
}

/**
 * Read theme from clipboard
 */
export async function readThemeFromClipboard(): Promise<ThemeImportResult> {
  try {
    const text = await navigator.clipboard.readText();
    return parseThemeJSON(text);
  } catch {
    return { success: false, error: 'Failed to read from clipboard' };
  }
}
