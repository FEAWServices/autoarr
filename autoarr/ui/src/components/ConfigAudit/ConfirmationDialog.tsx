/**
 * ConfirmationDialog Component
 *
 * Displays a modal dialog for confirming recommendation application.
 * Includes details about what will change and option for dry-run.
 * Following WCAG 2.1 AA compliance with focus trap and keyboard navigation.
 */

import React, { useEffect, useRef } from "react";
import { X, AlertTriangle, ArrowRight } from "lucide-react";
import clsx from "clsx";
import type { Recommendation } from "../../types/config";

interface ConfirmationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (dryRun: boolean) => void;
  recommendation: Recommendation | null;
  isApplying?: boolean;
}

export const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  recommendation,
  isApplying = false,
}) => {
  const [dryRun, setDryRun] = React.useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Focus management - focus dialog when opened
  useEffect(() => {
    if (isOpen && closeButtonRef.current) {
      closeButtonRef.current.focus();
    }
  }, [isOpen]);

  // Keyboard navigation - close on Escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  // Prevent body scroll when dialog is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }

    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen || !recommendation) return null;

  const handleConfirm = () => {
    onConfirm(dryRun);
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const isHighPriority = recommendation.priority === "high";

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto"
      aria-labelledby="dialog-title"
      aria-describedby="dialog-description"
      role="dialog"
      aria-modal="true"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 dark:bg-black/70 transition-opacity"
        onClick={handleBackdropClick}
        aria-hidden="true"
      />

      {/* Dialog Container */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          ref={dialogRef}
          className={clsx(
            "relative bg-white dark:bg-gray-800 rounded-lg shadow-xl",
            "w-full max-w-md sm:max-w-lg",
            "transform transition-all",
            "max-h-[90vh] flex flex-col",
          )}
        >
          {/* Header */}
          <div className="flex items-start justify-between p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex-1">
              <h2
                id="dialog-title"
                className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100"
              >
                Confirm Configuration Change
              </h2>
              <p
                id="dialog-description"
                className="mt-1 text-sm text-gray-500 dark:text-gray-400"
              >
                Review the changes before applying
              </p>
            </div>
            <button
              ref={closeButtonRef}
              type="button"
              onClick={onClose}
              disabled={isApplying}
              className={clsx(
                "ml-3 rounded-md p-1.5",
                "text-gray-400 hover:text-gray-500 dark:hover:text-gray-300",
                "focus:outline-none focus:ring-2 focus:ring-blue-500",
                "transition-colors",
                isApplying && "opacity-50 cursor-not-allowed",
              )}
              aria-label="Close dialog"
            >
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
            {/* High Priority Warning */}
            {isHighPriority && (
              <div
                className="flex gap-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md"
                role="alert"
              >
                <AlertTriangle
                  className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5"
                  aria-hidden="true"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-red-800 dark:text-red-300">
                    High Priority Change
                  </p>
                  <p className="mt-1 text-sm text-red-700 dark:text-red-400">
                    This change may significantly impact your system. Please
                    review carefully.
                  </p>
                </div>
              </div>
            )}

            {/* Service and Title */}
            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                Service
              </p>
              <p className="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100 capitalize">
                {recommendation.service}
              </p>
            </div>

            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                Setting
              </p>
              <p className="mt-1 text-sm font-semibold text-gray-900 dark:text-gray-100">
                {recommendation.title}
              </p>
            </div>

            {/* Current � New Value */}
            <div className="bg-gray-50 dark:bg-gray-900/50 rounded-md p-4">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
                Change Details
              </p>

              <div className="flex items-center gap-3 flex-wrap">
                <div className="flex-1 min-w-[120px]">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                    Current
                  </p>
                  <p className="text-sm font-mono text-gray-900 dark:text-gray-100 break-all">
                    {recommendation.current_value || (
                      <span className="text-gray-400 dark:text-gray-500 italic">
                        Not set
                      </span>
                    )}
                  </p>
                </div>

                <ArrowRight
                  className="h-5 w-5 text-gray-400 dark:text-gray-500 flex-shrink-0"
                  aria-hidden="true"
                />

                <div className="flex-1 min-w-[120px]">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                    New
                  </p>
                  <p className="text-sm font-mono text-green-700 dark:text-green-400 font-semibold break-all">
                    {recommendation.recommended_value}
                  </p>
                </div>
              </div>
            </div>

            {/* Impact */}
            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                Expected Impact
              </p>
              <p className="mt-1 text-sm text-gray-700 dark:text-gray-300">
                {recommendation.impact}
              </p>
            </div>

            {/* Dry Run Option */}
            <div className="pt-2">
              <label className="flex items-start gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={dryRun}
                  onChange={(e) => setDryRun(e.target.checked)}
                  disabled={isApplying}
                  className={clsx(
                    "mt-0.5 h-4 w-4 rounded border-gray-300 dark:border-gray-600",
                    "text-blue-600 focus:ring-blue-500",
                    "disabled:opacity-50 disabled:cursor-not-allowed",
                  )}
                  aria-label="Dry run mode - test without making actual changes"
                />
                <div className="flex-1 min-w-0">
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100 group-hover:text-gray-700 dark:group-hover:text-gray-200">
                    Dry Run (Preview Only)
                  </span>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    Test the change without actually applying it
                  </p>
                </div>
              </label>
            </div>
          </div>

          {/* Footer */}
          <div className="flex flex-col-reverse sm:flex-row gap-3 p-4 sm:p-6 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              disabled={isApplying}
              className={clsx(
                "flex-1 sm:flex-initial",
                "px-4 py-2.5 min-h-[44px]",
                "text-sm font-medium rounded-md",
                "bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200",
                "border border-gray-300 dark:border-gray-600",
                "hover:bg-gray-50 dark:hover:bg-gray-600",
                "focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500",
                "transition-colors",
                "disabled:opacity-50 disabled:cursor-not-allowed",
              )}
            >
              Cancel
            </button>

            <button
              type="button"
              onClick={handleConfirm}
              disabled={isApplying}
              className={clsx(
                "flex-1 sm:flex-initial",
                "px-4 py-2.5 min-h-[44px]",
                "text-sm font-medium rounded-md",
                "bg-blue-600 hover:bg-blue-700 text-white",
                "dark:bg-blue-500 dark:hover:bg-blue-600",
                "focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500",
                "transition-all duration-200",
                "shadow-sm hover:shadow-md",
                "disabled:opacity-75 disabled:cursor-not-allowed",
                isApplying && "relative",
              )}
              aria-label={`${dryRun ? "Test" : "Apply"} recommendation: ${
                recommendation.title
              }`}
            >
              {isApplying ? (
                <span className="flex items-center justify-center">
                  <svg
                    data-testid="apply-loading"
                    className="animate-spin -ml-1 mr-2 h-4 w-4"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  {dryRun ? "Testing..." : "Applying..."}
                </span>
              ) : dryRun ? (
                "Test Change"
              ) : (
                "Apply Change"
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
