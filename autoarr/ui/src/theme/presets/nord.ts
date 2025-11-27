import type { ThemePreset } from '../types';

/**
 * Nord - Arctic, north-bluish color palette
 *
 * Clean and elegant Scandinavian-inspired theme.
 * https://www.nordtheme.com/
 */
export const nord: ThemePreset = {
  id: 'nord',
  name: 'Nord',
  description: 'Cool blue Scandinavian palette',
  author: 'Arctic Ice Studio',
  version: '1.0.0',
  mode: 'dark',
  colors: {
    // Theme.Park compatible
    mainBg: '#2e3440',
    modalBg: '#3b4252',
    modalHeader: '#434c5e',
    buttonColor: '#88c0d0',
    buttonText: '#2e3440',
    accentColor: '#88c0d0',
    text: '#eceff4',
    textMuted: '#d8dee9',
    linkColor: '#81a1c1',
    linkColorHover: '#88c0d0',
    // Extended
    success: '#a3be8c',
    warning: '#ebcb8b',
    error: '#bf616a',
    info: '#81a1c1',
    borderColor: 'rgba(76, 86, 106, 0.4)',
  },
  meta: {
    tags: ['dark', 'nord', 'blue', 'scandinavian', 'arctic'],
    previewColors: ['#88c0d0', '#2e3440', '#eceff4', '#a3be8c'],
  },
};
