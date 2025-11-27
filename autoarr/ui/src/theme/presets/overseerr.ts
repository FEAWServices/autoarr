import type { ThemePreset } from '../types';

/**
 * Overseerr - Media request manager theme
 *
 * Purple/violet theme matching the Overseerr app.
 */
export const overseerr: ThemePreset = {
  id: 'overseerr',
  name: 'Overseerr',
  description: 'Purple media request theme',
  author: 'Theme.Park',
  version: '1.0.0',
  mode: 'dark',
  colors: {
    // Theme.Park compatible
    mainBg: '#111827',
    modalBg: '#1f2937',
    modalHeader: '#374151',
    buttonColor: '#a855f7',
    buttonText: '#ffffff',
    accentColor: '#a855f7',
    text: '#f3f4f6',
    textMuted: '#9ca3af',
    linkColor: '#a855f7',
    linkColorHover: '#c084fc',
    // Extended
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#6366f1',
    borderColor: 'rgba(75, 85, 99, 0.4)',
  },
  meta: {
    tags: ['dark', 'overseerr', 'purple', 'violet', 'media'],
    previewColors: ['#a855f7', '#111827', '#f3f4f6', '#10b981'],
  },
};
