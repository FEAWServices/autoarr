/**
 * AutoArr Theme System
 *
 * Main entry point for the theme system.
 */

// Types
export type {
  ThemeColors,
  ThemeMeta,
  ThemePreset,
  ThemeState,
  ThemeExportFormat,
  ThemeImportResult,
  BuiltInThemeId,
  PresetAccent,
} from './types';

export { PRESET_ACCENTS } from './types';

// Presets
export {
  BUILT_IN_PRESETS,
  PRESET_LIST,
  getPreset,
  isBuiltInPreset,
  getDefaultPreset,
  getPresetsByMode,
  searchPresetsByTag,
  autoarrDark,
  autoarrLight,
  dracula,
  nord,
  plex,
  overseerr,
  spaceGray,
  catppuccin,
} from './presets';

// Generator
export {
  applyTheme,
  applyAccentHue,
  resetAccentHue,
  getCurrentThemeId,
  isDarkMode,
  generateThemeCSS,
} from './generator';

// I/O
export {
  downloadThemeAsFile,
  readThemeFile,
  parseThemeJSON,
  generateShareUrl,
  parseShareUrl,
  copyThemeToClipboard,
  readThemeFromClipboard,
} from './io';
