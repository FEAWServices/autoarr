import type { ThemePreset } from '../types';

/**
 * Catppuccin Mocha - Soothing pastel theme
 *
 * Warm pastel colors on a dark base.
 * https://github.com/catppuccin/catppuccin
 */
export const catppuccin: ThemePreset = {
  id: 'catppuccin',
  name: 'Catppuccin Mocha',
  description: 'Soothing pastel dark theme',
  author: 'Catppuccin',
  version: '1.0.0',
  mode: 'dark',
  colors: {
    // Theme.Park compatible
    mainBg: '#1e1e2e',
    modalBg: '#313244',
    modalHeader: '#45475a',
    buttonColor: '#cba6f7',
    buttonText: '#1e1e2e',
    accentColor: '#cba6f7',
    text: '#cdd6f4',
    textMuted: '#6c7086',
    linkColor: '#89b4fa',
    linkColorHover: '#b4befe',
    // Extended
    success: '#a6e3a1',
    warning: '#f9e2af',
    error: '#f38ba8',
    info: '#89dceb',
    borderColor: 'rgba(108, 112, 134, 0.3)',
  },
  meta: {
    tags: ['dark', 'catppuccin', 'pastel', 'mocha', 'warm'],
    previewColors: ['#cba6f7', '#1e1e2e', '#cdd6f4', '#a6e3a1'],
  },
};
