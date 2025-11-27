import type { ThemePreset } from '../types';

/**
 * Plex - Plex media server inspired theme
 *
 * Dark theme with orange accents matching the Plex app.
 */
export const plex: ThemePreset = {
  id: 'plex',
  name: 'Plex',
  description: 'Orange Plex media server style',
  author: 'Theme.Park',
  version: '1.0.0',
  mode: 'dark',
  colors: {
    // Theme.Park compatible
    mainBg: '#1f2326',
    modalBg: '#282c31',
    modalHeader: '#323639',
    buttonColor: '#e5a00d',
    buttonText: '#1f2326',
    accentColor: '#e5a00d',
    text: '#eaeaea',
    textMuted: '#999999',
    linkColor: '#e5a00d',
    linkColorHover: '#f4b526',
    // Extended
    success: '#4caf50',
    warning: '#e5a00d',
    error: '#e53935',
    info: '#cc7b19',
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  meta: {
    tags: ['dark', 'plex', 'orange', 'media'],
    previewColors: ['#e5a00d', '#1f2326', '#eaeaea', '#4caf50'],
  },
};
