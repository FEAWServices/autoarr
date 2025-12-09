/**
 * Toast Notification Service
 *
 * Wraps react-hot-toast to provide typed, consistent notifications
 * for WebSocket events and user actions.
 */

import toast from 'react-hot-toast';
import type { WebSocketEvent } from '../types/chat';

/**
 * Notification types with consistent styling
 */
export type NotificationType = 'success' | 'error' | 'info' | 'loading' | 'warning';

/**
 * Show a success notification
 */
export function showSuccess(message: string, duration = 4000): string {
  return toast.success(message, {
    duration,
    position: 'bottom-right',
    style: {
      background: '#10b981',
      color: '#fff',
      borderRadius: '0.5rem',
      padding: '1rem',
      maxWidth: '500px',
    },
    iconTheme: {
      primary: '#fff',
      secondary: '#10b981',
    },
  });
}

/**
 * Show an error notification
 */
export function showError(message: string, duration = 6000): string {
  return toast.error(message, {
    duration,
    position: 'bottom-right',
    style: {
      background: '#ef4444',
      color: '#fff',
      borderRadius: '0.5rem',
      padding: '1rem',
      maxWidth: '500px',
    },
    iconTheme: {
      primary: '#fff',
      secondary: '#ef4444',
    },
  });
}

/**
 * Show an info notification
 */
export function showInfo(message: string, duration = 4000): string {
  return toast(message, {
    duration,
    position: 'bottom-right',
    icon: 'ℹ️',
    style: {
      background: '#3b82f6',
      color: '#fff',
      borderRadius: '0.5rem',
      padding: '1rem',
      maxWidth: '500px',
    },
  });
}

/**
 * Show a warning notification
 */
export function showWarning(message: string, duration = 5000): string {
  return toast(message, {
    duration,
    position: 'bottom-right',
    icon: '⚠️',
    style: {
      background: '#f59e0b',
      color: '#fff',
      borderRadius: '0.5rem',
      padding: '1rem',
      maxWidth: '500px',
    },
  });
}

/**
 * Show a loading notification (persists until dismissed)
 */
export function showLoading(message: string): string {
  return toast.loading(message, {
    position: 'bottom-right',
    style: {
      background: '#6366f1',
      color: '#fff',
      borderRadius: '0.5rem',
      padding: '1rem',
      maxWidth: '500px',
    },
  });
}

/**
 * Dismiss a specific notification
 */
export function dismiss(toastId: string): void {
  toast.dismiss(toastId);
}

/**
 * Dismiss all notifications
 */
export function dismissAll(): void {
  toast.dismiss();
}

/**
 * Handle WebSocket event and show appropriate notification
 */
export function handleWebSocketNotification(event: WebSocketEvent): void {
  const eventType = event.event_type || event.type;

  switch (eventType) {
    // Download events
    case 'download_started':
      showInfo(`Download started: ${event.data?.filename || event.data?.title || 'Unknown'}`, 3000);
      break;

    case 'download_completed':
      showSuccess(
        `Download completed: ${event.data?.filename || event.data?.title || 'Unknown'}`,
        4000
      );
      break;

    case 'download_failed':
      showError(
        `Download failed: ${event.data?.filename || event.data?.title || 'Unknown'}${
          event.data?.error ? ` - ${event.data.error}` : ''
        }`,
        6000
      );
      break;

    case 'download_paused':
      showWarning(
        `Download paused: ${event.data?.filename || event.data?.title || 'Unknown'}`,
        4000
      );
      break;

    case 'download_resumed':
      showInfo(`Download resumed: ${event.data?.filename || event.data?.title || 'Unknown'}`, 3000);
      break;

    // Recovery events
    case 'recovery_attempted':
      showInfo(
        `Recovery attempted: ${event.data?.filename || event.data?.title || 'Unknown'}${
          event.data?.strategy ? ` (${event.data.strategy})` : ''
        }`,
        4000
      );
      break;

    case 'recovery_success':
      showSuccess(
        `Recovery successful: ${event.data?.filename || event.data?.title || 'Unknown'}${
          event.data?.message ? ` - ${event.data.message}` : ''
        }`,
        5000
      );
      break;

    case 'recovery_failed':
      showError(
        `Recovery failed: ${event.data?.filename || event.data?.title || 'Unknown'}${
          event.data?.error || event.data?.message
            ? ` - ${event.data.error || event.data.message}`
            : ''
        }`,
        6000
      );
      break;

    // Config audit events
    case 'config_audit_started':
      showInfo('Configuration audit started...', 3000);
      break;

    case 'config_audit_completed':
      showSuccess(
        `Configuration audit completed${event.data?.message ? `: ${event.data.message}` : ''}`,
        4000
      );
      break;

    case 'config_audit_failed':
      showError(
        `Configuration audit failed${event.data?.error ? `: ${event.data.error}` : ''}`,
        6000
      );
      break;

    // Content request events
    case 'request_created':
    case 'content_requested':
      showInfo(`Content request created: ${event.data?.title || 'Unknown'}`, 3000);
      break;

    case 'request_processed':
    case 'content_added':
      showSuccess(`Content added: ${event.data?.title || 'Unknown'}`, 4000);
      break;

    case 'request_failed':
    case 'content_request_failed':
      showError(`Content request failed${event.data?.error ? `: ${event.data.error}` : ''}`, 6000);
      break;

    default:
      // Don't show notifications for unknown event types
      console.debug('Unhandled WebSocket event for notification:', eventType);
  }
}

/**
 * Show a custom progress toast (for downloads)
 */
export function showProgress(title: string, progress: number, message?: string): string {
  const progressPercent = Math.round(progress);
  const progressBar =
    '█'.repeat(Math.floor(progressPercent / 5)) + '░'.repeat(20 - Math.floor(progressPercent / 5));

  return toast(`${title}\n${progressBar} ${progressPercent}%${message ? `\n${message}` : ''}`, {
    duration: Infinity,
    position: 'bottom-right',
    icon: '⬇️',
    style: {
      background: '#6366f1',
      color: '#fff',
      borderRadius: '0.5rem',
      padding: '1rem',
      maxWidth: '500px',
      whiteSpace: 'pre-line',
    },
  });
}

/**
 * Update an existing progress toast
 */
export function updateProgress(
  toastId: string,
  title: string,
  progress: number,
  message?: string
): void {
  const progressPercent = Math.round(progress);
  const progressBar =
    '█'.repeat(Math.floor(progressPercent / 5)) + '░'.repeat(20 - Math.floor(progressPercent / 5));

  if (progress >= 100) {
    toast.success(`${title} - Complete!`, {
      id: toastId,
      duration: 3000,
      position: 'bottom-right',
    });
  } else {
    toast(`${title}\n${progressBar} ${progressPercent}%${message ? `\n${message}` : ''}`, {
      id: toastId,
      duration: Infinity,
      position: 'bottom-right',
      icon: '⬇️',
      style: {
        background: '#6366f1',
        color: '#fff',
        borderRadius: '0.5rem',
        padding: '1rem',
        maxWidth: '500px',
        whiteSpace: 'pre-line',
      },
    });
  }
}
