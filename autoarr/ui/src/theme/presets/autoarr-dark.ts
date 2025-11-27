import type { ThemePreset } from '../types';

/**
 * AutoArr Dark - Default theme
 *
 * The signature AutoArr look with purple/indigo accents on a dark blue background.
 */
export const autoarrDark: ThemePreset = {
  id: 'autoarr-dark',
  name: 'AutoArr Dark',
  description: 'Default dark theme with purple/indigo accents',
  author: 'AutoArr Team',
  version: '1.0.0',
  mode: 'dark',
  colors: {
    // Theme.Park compatible
    mainBg: '#0f1419',
    modalBg: '#1a1f2e',
    modalHeader: '#242938',
    buttonColor: '#6366f1',
    buttonText: '#f8fafc',
    accentColor: '#6366f1',
    text: '#f8fafc',
    textMuted: '#64748b',
    linkColor: '#3b82f6',
    linkColorHover: '#60a5fa',
    // Extended
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6',
    borderColor: 'rgba(100, 116, 139, 0.2)',
  },
  meta: {
    tags: ['dark', 'default', 'purple', 'indigo'],
    previewColors: ['#6366f1', '#0f1419', '#f8fafc', '#10b981'],
  },
};
