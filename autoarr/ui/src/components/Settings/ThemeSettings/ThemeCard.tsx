/**
 * ThemeCard Component
 *
 * Displays a theme preset with preview colors and selection controls.
 */

import { Check, Moon, Sun, Trash2 } from 'lucide-react';
import type { ThemePreset } from '../../../theme/types';

interface ThemeCardProps {
  theme: ThemePreset;
  isActive: boolean;
  isCustom?: boolean;
  onSelect: () => void;
  onDelete?: () => void;
}

export function ThemeCard({
  theme,
  isActive,
  isCustom = false,
  onSelect,
  onDelete,
}: ThemeCardProps) {
  return (
    <div
      className={`
        relative rounded-xl border-2 transition-all duration-200
        hover:scale-[1.02] cursor-pointer
        ${
          isActive
            ? 'border-[var(--accent-color)] shadow-theme-glow'
            : 'border-[var(--aa-border)] hover:border-[var(--accent-color)]/50'
        }
      `}
      onClick={onSelect}
    >
      {/* Active indicator */}
      {isActive && (
        <div className="absolute -top-2 -right-2 w-6 h-6 bg-[var(--accent-color)] rounded-full flex items-center justify-center z-10">
          <Check className="w-4 h-4 text-white" />
        </div>
      )}

      {/* Color preview bar */}
      <div className="flex h-10 rounded-t-lg overflow-hidden">
        {theme.meta.previewColors.map((color, index) => (
          <div key={index} className="flex-1 transition-all" style={{ backgroundColor: color }} />
        ))}
      </div>

      {/* Theme info */}
      <div className="p-3 bg-[var(--modal-bg-color)] rounded-b-lg">
        <div className="flex items-center justify-between mb-1">
          <h4 className="font-medium text-[var(--text)] text-sm flex items-center gap-1.5">
            {theme.name}
            {theme.mode === 'dark' ? (
              <Moon className="w-3 h-3 text-[var(--text-muted)]" />
            ) : (
              <Sun className="w-3 h-3 text-[var(--text-muted)]" />
            )}
          </h4>

          {/* Delete button for custom themes */}
          {isCustom && onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="p-1 rounded hover:bg-[var(--aa-error)]/20 transition-colors"
              title="Delete theme"
            >
              <Trash2 className="w-3.5 h-3.5 text-[var(--aa-error)]" />
            </button>
          )}
        </div>

        <p className="text-xs text-[var(--text-muted)] line-clamp-1">{theme.description}</p>

        {/* Tags */}
        <div className="flex flex-wrap gap-1 mt-2">
          {theme.meta.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="px-1.5 py-0.5 text-[10px] rounded bg-[var(--modal-header-color)] text-[var(--text-muted)]"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
