/**
 * Appearance Settings Page
 *
 * Dedicated page for theme customization at /settings/appearance
 */

import { ThemeSettings } from '../components/Settings/ThemeSettings';

export function Appearance() {
  return (
    <div className="p-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--text)] mb-2">Appearance</h1>
        <p className="text-[var(--text-muted)]">Customize the look and feel of AutoArr</p>
      </div>

      <ThemeSettings />
    </div>
  );
}
