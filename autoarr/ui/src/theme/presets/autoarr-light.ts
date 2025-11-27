import type { ThemePreset } from '../types';

/**
 * AutoArr Light - Light theme variant
 *
 * Clean light theme with the same purple/indigo accents.
 */
export const autoarrLight: ThemePreset = {
  id: 'autoarr-light',
  name: 'AutoArr Light',
  description: 'Light theme with purple/indigo accents',
  author: 'AutoArr Team',
  version: '1.0.0',
  mode: 'light',
  colors: {
    // Theme.Park compatible
    mainBg: '#f8fafc',
    modalBg: '#ffffff',
    modalHeader: '#f1f5f9',
    buttonColor: '#6366f1',
    buttonText: '#ffffff',
    accentColor: '#6366f1',
    text: '#0f172a',
    textMuted: '#64748b',
    linkColor: '#3b82f6',
    linkColorHover: '#2563eb',
    // Extended
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6',
    borderColor: 'rgba(0, 0, 0, 0.1)',
  },
  meta: {
    tags: ['light', 'purple', 'indigo', 'clean'],
    previewColors: ['#6366f1', '#f8fafc', '#0f172a', '#10b981'],
  },
};
