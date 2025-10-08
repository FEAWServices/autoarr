/**
 * Toast Notification Component
 *
 * Accessible toast notification system with:
 * - Success, error, info, warning types
 * - Auto-dismiss with configurable timeout
 * - Manual dismiss
 * - Screen reader announcements
 * - Stacking support
 * - WCAG 2.1 AA compliance
 */

import { useEffect, useState } from "react";
import { CheckCircle, AlertCircle, Info, AlertTriangle, X } from "lucide-react";
import { create } from "zustand";

export type ToastType = "success" | "error" | "info" | "warning";

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastStore {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, "id">) => void;
  removeToast: (id: string) => void;
  clearAll: () => void;
}

// Zustand store for toast management
export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (toast) => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    set((state) => ({
      toasts: [...state.toasts, { ...toast, id }],
    }));
  },
  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },
  clearAll: () => {
    set({ toasts: [] });
  },
}));

// Helper function to show toasts
export const toast = {
  success: (title: string, message?: string, duration = 4000) => {
    useToastStore
      .getState()
      .addToast({ type: "success", title, message, duration });
  },
  error: (title: string, message?: string, duration = 5000) => {
    useToastStore
      .getState()
      .addToast({ type: "error", title, message, duration });
  },
  info: (title: string, message?: string, duration = 4000) => {
    useToastStore
      .getState()
      .addToast({ type: "info", title, message, duration });
  },
  warning: (title: string, message?: string, duration = 4000) => {
    useToastStore
      .getState()
      .addToast({ type: "warning", title, message, duration });
  },
};

interface ToastItemProps {
  toast: Toast;
  onDismiss: (id: string) => void;
}

function ToastItem({ toast, onDismiss }: ToastItemProps) {
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    if (toast.duration && toast.duration > 0) {
      const timer = setTimeout(() => {
        setIsExiting(true);
        setTimeout(() => {
          onDismiss(toast.id);
        }, 300);
      }, toast.duration);

      return () => clearTimeout(timer);
    }
  }, [toast.duration, toast.id, onDismiss]);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => {
      onDismiss(toast.id);
    }, 300);
  };

  const getToastStyles = () => {
    switch (toast.type) {
      case "success":
        return "bg-green-900/90 border-green-700 text-green-100";
      case "error":
        return "bg-red-900/90 border-red-700 text-red-100";
      case "warning":
        return "bg-yellow-900/90 border-yellow-700 text-yellow-100";
      case "info":
      default:
        return "bg-blue-900/90 border-blue-700 text-blue-100";
    }
  };

  const getIcon = () => {
    const iconClass = "w-5 h-5 flex-shrink-0";
    switch (toast.type) {
      case "success":
        return <CheckCircle className={iconClass} aria-hidden="true" />;
      case "error":
        return <AlertCircle className={iconClass} aria-hidden="true" />;
      case "warning":
        return <AlertTriangle className={iconClass} aria-hidden="true" />;
      case "info":
      default:
        return <Info className={iconClass} aria-hidden="true" />;
    }
  };

  return (
    <div
      data-testid="toast-item"
      data-toast-type={toast.type}
      role="alert"
      aria-live={toast.type === "error" ? "assertive" : "polite"}
      aria-atomic="true"
      className={`
        ${getToastStyles()}
        border rounded-lg shadow-lg p-4 min-w-[300px] max-w-md
        transition-all duration-300 ease-in-out
        ${
          isExiting ? "opacity-0 translate-x-full" : "opacity-100 translate-x-0"
        }
      `}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div>{getIcon()}</div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-sm mb-1">{toast.title}</h3>
          {toast.message && (
            <p className="text-sm opacity-90">{toast.message}</p>
          )}

          {/* Action Button */}
          {toast.action && (
            <button
              onClick={toast.action.onClick}
              className="mt-2 px-3 py-1 bg-white/20 hover:bg-white/30 rounded text-sm font-medium transition-colors min-h-[32px]"
            >
              {toast.action.label}
            </button>
          )}
        </div>

        {/* Dismiss Button */}
        <button
          onClick={handleDismiss}
          className="flex-shrink-0 p-1 hover:bg-white/10 rounded transition-colors min-h-[28px] min-w-[28px]"
          aria-label="Dismiss notification"
          data-testid="toast-dismiss"
        >
          <X className="w-4 h-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}

export function ToastContainer() {
  const toasts = useToastStore((state) => state.toasts);
  const removeToast = useToastStore((state) => state.removeToast);

  if (toasts.length === 0) {
    return null;
  }

  return (
    <div
      data-testid="toast-container"
      className="fixed top-4 right-4 z-50 flex flex-col gap-3 pointer-events-none"
      aria-live="polite"
      aria-relevant="additions"
    >
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <ToastItem toast={toast} onDismiss={removeToast} />
        </div>
      ))}
    </div>
  );
}
