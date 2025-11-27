/**
 * ThemeSettings Component
 *
 * Main theme settings panel with theme selection, accent customization,
 * and import/export functionality.
 */

import { useState } from 'react';
import { Palette, Upload, RotateCcw } from 'lucide-react';
import { useThemeStore, useAllThemes } from '../../../stores/themeStore';
import { isBuiltInPreset } from '../../../theme/presets';
import { ThemeCard } from './ThemeCard';
import { AccentPicker } from './AccentPicker';
import { ThemeImportExport } from './ThemeImportExport';

export function ThemeSettings() {
  const [showImportExport, setShowImportExport] = useState(false);

  const { activeThemeId, accentHue, setTheme, setAccentHue, removeCustomTheme, resetToDefault } =
    useThemeStore();

  const allThemes = useAllThemes();
  const builtInThemes = allThemes.filter((t) => isBuiltInPreset(t.id));
  const customThemes = allThemes.filter((t) => !isBuiltInPreset(t.id));

  return (
    <div className="space-y-8">
      {/* Section Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-[var(--text)] flex items-center gap-2">
            <Palette className="w-5 h-5" />
            Appearance
          </h2>
          <p className="text-sm text-[var(--text-muted)] mt-1">
            Customize the look and feel of AutoArr
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setShowImportExport(true)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[var(--modal-header-color)] text-[var(--text)] text-sm font-medium hover:bg-[var(--aa-border)] transition-colors"
          >
            <Upload className="w-4 h-4" />
            Import / Export
          </button>
          <button
            onClick={resetToDefault}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[var(--modal-header-color)] text-[var(--text-muted)] text-sm font-medium hover:bg-[var(--aa-border)] transition-colors"
            title="Reset to default theme"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Built-in Themes */}
      <div>
        <h3 className="text-lg font-medium text-[var(--text)] mb-4">Built-in Themes</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {builtInThemes.map((theme) => (
            <ThemeCard
              key={theme.id}
              theme={theme}
              isActive={activeThemeId === theme.id}
              onSelect={() => setTheme(theme.id)}
            />
          ))}
        </div>
      </div>

      {/* Custom Themes */}
      {customThemes.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-[var(--text)] mb-4">Custom Themes</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {customThemes.map((theme) => (
              <ThemeCard
                key={theme.id}
                theme={theme}
                isActive={activeThemeId === theme.id}
                isCustom
                onSelect={() => setTheme(theme.id)}
                onDelete={() => removeCustomTheme(theme.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Accent Color Customization */}
      <div className="p-6 rounded-xl bg-[var(--modal-bg-color)] border border-[var(--aa-border)]">
        <AccentPicker currentHue={accentHue} onChange={setAccentHue} />
      </div>

      {/* Theme.Park Info */}
      <div className="p-4 rounded-lg bg-[var(--modal-header-color)]/50 border border-[var(--aa-border)]">
        <h4 className="text-sm font-medium text-[var(--text)] mb-2">Theme.Park Compatible</h4>
        <p className="text-xs text-[var(--text-muted)] mb-2">
          AutoArr themes are compatible with the Theme.Park ecosystem used by Sonarr, Radarr, and
          other arr apps. You can import themes from Theme.Park or create your own custom themes.
        </p>
        <a
          href="https://theme-park.dev/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-[var(--link-color)] hover:text-[var(--link-color-hover)] transition-colors"
        >
          Learn more about Theme.Park &rarr;
        </a>
      </div>

      {/* Import/Export Modal */}
      {showImportExport && <ThemeImportExport onClose={() => setShowImportExport(false)} />}
    </div>
  );
}

export default ThemeSettings;
