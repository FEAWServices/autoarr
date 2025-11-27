/**
 * AccentPicker Component
 *
 * Allows users to customize the accent color with a hue slider
 * and preset color buttons.
 */

import { RotateCcw } from 'lucide-react';
import { PRESET_ACCENTS } from '../../../theme/types';

interface AccentPickerProps {
  currentHue: number | null;
  onChange: (hue: number | null) => void;
}

export function AccentPicker({ currentHue, onChange }: AccentPickerProps) {
  // Use theme default (239 - indigo) if no custom hue
  const displayHue = currentHue ?? 239;

  return (
    <div className="space-y-4">
      {/* Hue slider */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium text-[var(--text)]">Accent Color</label>
          {currentHue !== null && (
            <button
              onClick={() => onChange(null)}
              className="flex items-center gap-1 text-xs text-[var(--text-muted)] hover:text-[var(--text)] transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
              Reset
            </button>
          )}
        </div>

        <div className="relative">
          {/* Rainbow gradient track */}
          <div
            className="h-3 rounded-full"
            style={{
              background: `linear-gradient(to right,
                hsl(0, 84%, 60%),
                hsl(60, 84%, 60%),
                hsl(120, 84%, 60%),
                hsl(180, 84%, 60%),
                hsl(240, 84%, 60%),
                hsl(300, 84%, 60%),
                hsl(360, 84%, 60%)
              )`,
            }}
          />

          {/* Slider input */}
          <input
            type="range"
            min="0"
            max="360"
            value={displayHue}
            onChange={(e) => onChange(Number(e.target.value))}
            className="absolute inset-0 w-full h-3 opacity-0 cursor-pointer"
          />

          {/* Current position indicator */}
          <div
            className="absolute top-1/2 -translate-y-1/2 w-5 h-5 rounded-full border-2 border-white shadow-lg pointer-events-none transition-all"
            style={{
              left: `calc(${(displayHue / 360) * 100}% - 10px)`,
              backgroundColor: `hsl(${displayHue}, 84%, 60%)`,
            }}
          />
        </div>

        <div className="flex justify-between mt-1 text-xs text-[var(--text-muted)]">
          <span>Red</span>
          <span>Green</span>
          <span>Cyan</span>
          <span>Blue</span>
          <span>Purple</span>
        </div>
      </div>

      {/* Preset accent buttons */}
      <div>
        <label className="block text-sm font-medium text-[var(--text)] mb-2">Preset Colors</label>
        <div className="grid grid-cols-6 gap-2">
          {PRESET_ACCENTS.map((accent) => (
            <button
              key={accent.name}
              onClick={() => onChange(accent.hue)}
              className={`
                w-full aspect-square rounded-full transition-transform hover:scale-110
                ${
                  currentHue === accent.hue
                    ? 'ring-2 ring-white ring-offset-2 ring-offset-[var(--main-bg-color)]'
                    : ''
                }
              `}
              style={{ backgroundColor: `hsl(${accent.hue}, 84%, 60%)` }}
              title={accent.name}
            />
          ))}
        </div>
      </div>

      {/* Live preview */}
      <div className="p-4 rounded-lg bg-[var(--modal-bg-color)] border border-[var(--aa-border)]">
        <p className="text-sm text-[var(--text-muted)] mb-3">Preview</p>
        <div className="flex items-center gap-3">
          <button
            className="px-4 py-2 rounded-lg text-white text-sm font-medium transition-all"
            style={{
              backgroundColor: `hsl(${displayHue}, 84%, 60%)`,
              boxShadow: `0 0 20px hsla(${displayHue}, 84%, 60%, 0.3)`,
            }}
          >
            Primary Button
          </button>
          <button
            className="px-4 py-2 rounded-lg text-sm font-medium border-2 transition-all"
            style={{
              borderColor: `hsl(${displayHue}, 84%, 60%)`,
              color: `hsl(${displayHue}, 84%, 60%)`,
            }}
          >
            Secondary
          </button>
          <div
            className="w-8 h-8 rounded-full"
            style={{
              backgroundColor: `hsl(${displayHue}, 84%, 60%)`,
              boxShadow: `0 0 15px hsla(${displayHue}, 84%, 60%, 0.5)`,
            }}
          />
        </div>
      </div>
    </div>
  );
}
