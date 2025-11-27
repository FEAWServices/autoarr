import type { ThemePreset } from '../types';

/**
 * Space Gray - Neutral Apple-style theme
 *
 * Clean, minimal gray theme with subtle blue accents.
 */
export const spaceGray: ThemePreset = {
  id: 'space-gray',
  name: 'Space Gray',
  description: 'Neutral Apple-style dark gray',
  author: 'Theme.Park',
  version: '1.0.0',
  mode: 'dark',
  colors: {
    // Theme.Park compatible
    mainBg: '#1c1c1e',
    modalBg: '#2c2c2e',
    modalHeader: '#3a3a3c',
    buttonColor: '#0a84ff',
    buttonText: '#ffffff',
    accentColor: '#0a84ff',
    text: '#ffffff',
    textMuted: '#8e8e93',
    linkColor: '#0a84ff',
    linkColorHover: '#409cff',
    // Extended
    success: '#30d158',
    warning: '#ffd60a',
    error: '#ff453a',
    info: '#64d2ff',
    borderColor: 'rgba(142, 142, 147, 0.2)',
  },
  meta: {
    tags: ['dark', 'gray', 'neutral', 'apple', 'minimal'],
    previewColors: ['#0a84ff', '#1c1c1e', '#ffffff', '#30d158'],
  },
};
