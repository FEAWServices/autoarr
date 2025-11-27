/**
 * AutoArr Theme Presets Registry
 *
 * Central export for all built-in theme presets.
 */

import type { ThemePreset, BuiltInThemeId } from '../types';

// Import all presets
import { autoarrDark } from './autoarr-dark';
import { autoarrLight } from './autoarr-light';
import { dracula } from './dracula';
import { nord } from './nord';
import { plex } from './plex';
import { overseerr } from './overseerr';
import { spaceGray } from './space-gray';
import { catppuccin } from './catppuccin';

/**
 * Map of all built-in theme presets
 */
export const BUILT_IN_PRESETS: Record<BuiltInThemeId, ThemePreset> = {
  'autoarr-dark': autoarrDark,
  'autoarr-light': autoarrLight,
  dracula: dracula,
  nord: nord,
  plex: plex,
  overseerr: overseerr,
  'space-gray': spaceGray,
  catppuccin: catppuccin,
};

/**
 * Array of all built-in presets for iteration
 */
export const PRESET_LIST: ThemePreset[] = Object.values(BUILT_IN_PRESETS);

/**
 * Get a preset by ID
 */
export function getPreset(id: string): ThemePreset | undefined {
  return BUILT_IN_PRESETS[id as BuiltInThemeId];
}

/**
 * Check if an ID is a built-in preset
 */
export function isBuiltInPreset(id: string): id is BuiltInThemeId {
  return id in BUILT_IN_PRESETS;
}

/**
 * Get the default theme preset
 */
export function getDefaultPreset(): ThemePreset {
  return autoarrDark;
}

/**
 * Get all presets matching a mode
 */
export function getPresetsByMode(mode: 'dark' | 'light'): ThemePreset[] {
  return PRESET_LIST.filter((preset) => preset.mode === mode);
}

/**
 * Search presets by tag
 */
export function searchPresetsByTag(tag: string): ThemePreset[] {
  const lowerTag = tag.toLowerCase();
  return PRESET_LIST.filter((preset) =>
    preset.meta.tags.some((t) => t.toLowerCase().includes(lowerTag))
  );
}

// Re-export individual presets for direct import
export { autoarrDark, autoarrLight, dracula, nord, plex, overseerr, spaceGray, catppuccin };
