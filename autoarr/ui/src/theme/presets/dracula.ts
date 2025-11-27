import type { ThemePreset } from '../types';

/**
 * Dracula - Popular dark theme
 *
 * The famous Dracula color scheme with purple/pink accents.
 * https://draculatheme.com/
 */
export const dracula: ThemePreset = {
  id: 'dracula',
  name: 'Dracula',
  description: 'Dark purple/pink vampire theme',
  author: 'Dracula Theme',
  version: '1.0.0',
  mode: 'dark',
  colors: {
    // Theme.Park compatible
    mainBg: '#282a36',
    modalBg: '#44475a',
    modalHeader: '#383a4a',
    buttonColor: '#bd93f9',
    buttonText: '#f8f8f2',
    accentColor: '#bd93f9',
    text: '#f8f8f2',
    textMuted: '#6272a4',
    linkColor: '#8be9fd',
    linkColorHover: '#a4f4ff',
    // Extended
    success: '#50fa7b',
    warning: '#f1fa8c',
    error: '#ff5555',
    info: '#8be9fd',
    borderColor: 'rgba(98, 114, 164, 0.3)',
  },
  meta: {
    tags: ['dark', 'dracula', 'purple', 'pink', 'popular'],
    previewColors: ['#bd93f9', '#282a36', '#f8f8f2', '#50fa7b'],
  },
};
