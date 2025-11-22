import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ThemeState {
  isDarkMode: boolean;
  toggleDarkMode: () => void;
  setDarkMode: (value: boolean) => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      isDarkMode: true, // Default to dark mode
      toggleDarkMode: () =>
        set((state) => {
          const newMode = !state.isDarkMode;
          // Update document class for Tailwind dark mode
          if (newMode) {
            document.documentElement.classList.add('dark');
          } else {
            document.documentElement.classList.remove('dark');
          }
          return { isDarkMode: newMode };
        }),
      setDarkMode: (value) =>
        set(() => {
          // Update document class for Tailwind dark mode
          if (value) {
            document.documentElement.classList.add('dark');
          } else {
            document.documentElement.classList.remove('dark');
          }
          return { isDarkMode: value };
        }),
    }),
    {
      name: 'autoarr-theme',
    }
  )
);
