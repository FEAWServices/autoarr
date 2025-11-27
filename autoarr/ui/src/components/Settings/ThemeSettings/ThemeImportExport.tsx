/**
 * ThemeImportExport Component
 *
 * Handles importing and exporting theme files.
 */

import { useState, useRef } from 'react';
import { Upload, Download, Copy, Check, X, FileJson, AlertCircle } from 'lucide-react';
import { useThemeStore } from '../../../stores/themeStore';
import {
  downloadThemeAsFile,
  readThemeFile,
  parseThemeJSON,
  copyThemeToClipboard,
} from '../../../theme/io';

interface ThemeImportExportProps {
  onClose: () => void;
}

export function ThemeImportExport({ onClose }: ThemeImportExportProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [jsonInput, setJsonInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const { importTheme, activeTheme, accentHue } = useThemeStore();

  // Handle file selection
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    setSuccess(null);

    const result = await readThemeFile(file);
    if (result.success && result.theme) {
      importTheme(JSON.stringify(result.theme));
      setSuccess(`Imported "${result.theme.name}" successfully!`);
      setJsonInput('');
    } else {
      setError(result.error || 'Failed to import theme');
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Handle JSON paste import
  const handleJsonImport = () => {
    if (!jsonInput.trim()) {
      setError('Please paste theme JSON first');
      return;
    }

    setError(null);
    setSuccess(null);

    const result = parseThemeJSON(jsonInput);
    if (result.success && result.theme) {
      importTheme(jsonInput);
      setSuccess(`Imported "${result.theme.name}" successfully!`);
      setJsonInput('');
    } else {
      setError(result.error || 'Invalid theme JSON');
    }
  };

  // Handle export current theme
  const handleExport = () => {
    if (!activeTheme) return;
    downloadThemeAsFile(activeTheme, accentHue);
    setSuccess('Theme exported!');
  };

  // Handle copy to clipboard
  const handleCopy = async () => {
    if (!activeTheme) return;

    const success = await copyThemeToClipboard(activeTheme, accentHue);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-[var(--modal-bg-color)] rounded-xl shadow-xl border border-[var(--aa-border)]">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--aa-border)]">
          <h3 className="text-lg font-semibold text-[var(--text)]">Import / Export Themes</h3>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-[var(--modal-header-color)] transition-colors"
          >
            <X className="w-5 h-5 text-[var(--text-muted)]" />
          </button>
        </div>

        <div className="p-4 space-y-6">
          {/* Status messages */}
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-[var(--aa-error)]/20 text-[var(--aa-error)]">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}
          {success && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-[var(--aa-success)]/20 text-[var(--aa-success)]">
              <Check className="w-4 h-4 flex-shrink-0" />
              <span className="text-sm">{success}</span>
            </div>
          )}

          {/* Import section */}
          <div>
            <h4 className="text-sm font-medium text-[var(--text)] mb-3">Import Theme</h4>

            {/* File upload */}
            <div className="mb-3">
              <input
                ref={fileInputRef}
                type="file"
                accept=".json"
                onChange={handleFileSelect}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full flex items-center justify-center gap-2 p-3 border-2 border-dashed border-[var(--aa-border)] rounded-lg hover:border-[var(--accent-color)] hover:bg-[var(--modal-header-color)]/50 transition-colors"
              >
                <Upload className="w-5 h-5 text-[var(--text-muted)]" />
                <span className="text-sm text-[var(--text-muted)]">
                  Choose .json file or drag & drop
                </span>
              </button>
            </div>

            {/* JSON paste */}
            <div className="space-y-2">
              <label className="text-xs text-[var(--text-muted)]">Or paste theme JSON:</label>
              <textarea
                value={jsonInput}
                onChange={(e) => setJsonInput(e.target.value)}
                placeholder='{"id": "my-theme", "name": "My Theme", ...}'
                rows={4}
                className="w-full px-3 py-2 text-sm rounded-lg bg-[var(--main-bg-color)] border border-[var(--aa-border)] text-[var(--text)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-color)] resize-none font-mono"
              />
              <button
                onClick={handleJsonImport}
                disabled={!jsonInput.trim()}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--accent-color)] text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition-opacity"
              >
                <FileJson className="w-4 h-4" />
                Import from JSON
              </button>
            </div>
          </div>

          {/* Divider */}
          <div className="border-t border-[var(--aa-border)]" />

          {/* Export section */}
          <div>
            <h4 className="text-sm font-medium text-[var(--text)] mb-3">Export Current Theme</h4>
            <p className="text-xs text-[var(--text-muted)] mb-3">
              Export "{activeTheme?.name || 'Unknown'}" with your custom accent color settings.
            </p>

            <div className="flex gap-2">
              <button
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--modal-header-color)] text-[var(--text)] text-sm font-medium hover:bg-[var(--aa-border)] transition-colors"
              >
                <Download className="w-4 h-4" />
                Download .json
              </button>
              <button
                onClick={handleCopy}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--modal-header-color)] text-[var(--text)] text-sm font-medium hover:bg-[var(--aa-border)] transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4 text-[var(--aa-success)]" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Copy JSON
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end p-4 border-t border-[var(--aa-border)]">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-[var(--modal-header-color)] text-[var(--text)] text-sm font-medium hover:bg-[var(--aa-border)] transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
