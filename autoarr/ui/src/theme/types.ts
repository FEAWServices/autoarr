/**
 * AutoArr Theme System - Type Definitions
 *
 * Theme.Park compatible naming conventions for arr ecosystem consistency.
 */

/**
 * Theme colors following Theme.Park conventions with AutoArr extensions
 */
export interface ThemeColors {
  // === Theme.Park Compatible ===
  /** Main application background */
  mainBg: string;
  /** Modal/card background */
  modalBg: string;
  /** Modal header/elevated surfaces */
  modalHeader: string;
  /** Primary button background */
  buttonColor: string;
  /** Button text color */
  buttonText: string;
  /** Main accent/brand color */
  accentColor: string;
  /** Primary text color */
  text: string;
  /** Muted/secondary text */
  textMuted: string;
  /** Link color */
  linkColor: string;
  /** Link hover color */
  linkColorHover: string;

  // === AutoArr Extended ===
  /** Success status color */
  success: string;
  /** Warning status color */
  warning: string;
  /** Error status color */
  error: string;
  /** Info status color */
  info: string;
  /** Border color */
  borderColor: string;
}

/**
 * Theme metadata for display and organization
 */
export interface ThemeMeta {
  /** Tags for filtering/categorization */
  tags: string[];
  /** Preview colors shown in theme card [accent, bg, text, status] */
  previewColors: [string, string, string, string];
}

/**
 * Complete theme preset definition
 */
export interface ThemePreset {
  /** Unique identifier */
  id: string;
  /** Display name */
  name: string;
  /** Short description */
  description: string;
  /** Theme author */
  author: string;
  /** Semantic version */
  version: string;
  /** Light or dark mode */
  mode: 'dark' | 'light';
  /** Color definitions */
  colors: ThemeColors;
  /** Metadata for UI */
  meta: ThemeMeta;
}

/**
 * Built-in theme IDs
 */
export type BuiltInThemeId =
  | 'autoarr-dark'
  | 'autoarr-light'
  | 'dracula'
  | 'nord'
  | 'plex'
  | 'overseerr'
  | 'space-gray'
  | 'catppuccin';

/**
 * Theme state persisted in localStorage
 */
export interface ThemeState {
  /** Currently active theme ID */
  activeThemeId: string;
  /** User's custom accent hue (0-360), null to use theme default */
  accentHue: number | null;
  /** User-imported custom themes */
  customThemes: ThemePreset[];
}

/**
 * JSON export format for sharing themes
 */
export interface ThemeExportFormat {
  /** Format version */
  version: '1.0';
  /** File type identifier */
  type: 'autoarr-theme';
  /** The theme preset */
  preset: ThemePreset;
  /** Optional custom accent hue */
  accentHue?: number;
  /** Export timestamp */
  exportedAt: string;
}

/**
 * Result of theme import operation
 */
export interface ThemeImportResult {
  success: boolean;
  error?: string;
  theme?: ThemePreset;
}

/**
 * Preset accent colors for quick selection
 */
export interface PresetAccent {
  name: string;
  hue: number;
}

/**
 * Default preset accent options
 */
export const PRESET_ACCENTS: PresetAccent[] = [
  { name: 'Indigo', hue: 239 },
  { name: 'Blue', hue: 217 },
  { name: 'Cyan', hue: 189 },
  { name: 'Teal', hue: 168 },
  { name: 'Green', hue: 142 },
  { name: 'Lime', hue: 85 },
  { name: 'Yellow', hue: 48 },
  { name: 'Orange', hue: 25 },
  { name: 'Red', hue: 0 },
  { name: 'Pink', hue: 330 },
  { name: 'Purple', hue: 280 },
  { name: 'Violet', hue: 263 },
];
