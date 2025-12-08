import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ConnectionStatus } from '../components/ConnectionStatus';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock window.location.reload
const mockReload = vi.fn();
Object.defineProperty(window, 'location', {
  value: { reload: mockReload },
  writable: true,
});

describe('ConnectionStatus', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockFetch.mockReset();
    mockReload.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('initial state', () => {
    it('should not render when connected', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true });

      const { container } = render(<ConnectionStatus />);

      // Wait for initial check
      await act(async () => {
        await vi.runAllTimersAsync();
      });

      // Should not show modal when connected
      expect(container.firstChild).toBeNull();
    });

    it('should show modal after 2 consecutive failures', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<ConnectionStatus checkInterval={1000} />);

      // First failure - should not show yet
      await act(async () => {
        await vi.advanceTimersByTimeAsync(100);
      });
      expect(screen.queryByText('Connection Lost')).not.toBeInTheDocument();

      // Second check (after interval)
      await act(async () => {
        await vi.advanceTimersByTimeAsync(1000);
      });

      // Now should show after 2 failures
      expect(screen.getByText('Connection Lost')).toBeInTheDocument();
    });
  });

  describe('retry functionality', () => {
    it('should call fetch when retry button is clicked', async () => {
      // Setup: fail twice to show modal
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<ConnectionStatus checkInterval={1000} />);

      // Trigger 2 failures to show modal
      await act(async () => {
        await vi.advanceTimersByTimeAsync(1100);
      });

      expect(screen.getByText('Connection Lost')).toBeInTheDocument();

      // Reset mock to track retry call
      mockFetch.mockClear();
      mockFetch.mockRejectedValueOnce(new Error('Still down'));

      // Click retry
      const retryButton = screen.getByRole('button', { name: /retry/i });
      await act(async () => {
        fireEvent.click(retryButton);
        await vi.runAllTimersAsync();
      });

      // Should have called fetch for the retry
      expect(mockFetch).toHaveBeenCalledWith('/health', expect.any(Object));
    });

    it('should reload page when retry fails', async () => {
      // Setup: fail to show modal
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<ConnectionStatus checkInterval={1000} />);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(1100);
      });

      // Retry also fails
      mockFetch.mockRejectedValueOnce(new Error('Still down'));

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await act(async () => {
        fireEvent.click(retryButton);
        await vi.runAllTimersAsync();
      });

      // Should reload page on failed retry
      expect(mockReload).toHaveBeenCalled();
    });

    it('should hide modal when retry succeeds', async () => {
      // Setup: fail to show modal
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<ConnectionStatus checkInterval={1000} />);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(1100);
      });

      expect(screen.getByText('Connection Lost')).toBeInTheDocument();

      // Retry succeeds
      mockFetch.mockResolvedValueOnce({ ok: true });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await act(async () => {
        fireEvent.click(retryButton);
        await vi.runAllTimersAsync();
      });

      // Should NOT reload (connection restored)
      expect(mockReload).not.toHaveBeenCalled();

      // Modal should be hidden
      await waitFor(() => {
        expect(screen.queryByText('Connection Lost')).not.toBeInTheDocument();
      });
    });

    it('should show "Reconnecting..." text while retrying', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<ConnectionStatus checkInterval={1000} />);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(1100);
      });

      // Make retry hang
      mockFetch.mockImplementationOnce(
        () => new Promise((resolve) => setTimeout(() => resolve({ ok: true }), 5000))
      );

      const retryButton = screen.getByRole('button', { name: /retry/i });
      fireEvent.click(retryButton);

      // Should show "Reconnecting..." immediately
      expect(screen.getByText('Reconnecting...')).toBeInTheDocument();
    });
  });

  describe('dismiss functionality', () => {
    it('should hide modal when dismiss button is clicked', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<ConnectionStatus checkInterval={1000} />);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(1100);
      });

      expect(screen.getByText('Connection Lost')).toBeInTheDocument();

      const dismissButton = screen.getByRole('button', { name: /dismiss/i });
      fireEvent.click(dismissButton);

      expect(screen.queryByText('Connection Lost')).not.toBeInTheDocument();
    });

    it('should hide modal when X button is clicked', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<ConnectionStatus checkInterval={1000} />);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(1100);
      });

      const closeButton = screen.getByLabelText('Dismiss');
      fireEvent.click(closeButton);

      expect(screen.queryByText('Connection Lost')).not.toBeInTheDocument();
    });
  });

  describe('checkConnection return value', () => {
    it('should return true when connection succeeds', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true });

      // We need to test this indirectly through behavior
      // When retry succeeds (returns true), it should NOT reload
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<ConnectionStatus checkInterval={1000} />);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(1100);
      });

      // Now make retry succeed
      mockFetch.mockResolvedValueOnce({ ok: true });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await act(async () => {
        fireEvent.click(retryButton);
        await vi.runAllTimersAsync();
      });

      // Should NOT reload because checkConnection returned true
      expect(mockReload).not.toHaveBeenCalled();
    });

    it('should return false when connection fails', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<ConnectionStatus checkInterval={1000} />);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(1100);
      });

      // Retry also fails
      mockFetch.mockRejectedValueOnce(new Error('Still down'));

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await act(async () => {
        fireEvent.click(retryButton);
        await vi.runAllTimersAsync();
      });

      // Should reload because checkConnection returned false
      expect(mockReload).toHaveBeenCalled();
    });
  });

  describe('health endpoint', () => {
    it('should use custom health endpoint when provided', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true });

      render(<ConnectionStatus healthEndpoint="/api/custom-health" />);

      await act(async () => {
        await vi.runAllTimersAsync();
      });

      expect(mockFetch).toHaveBeenCalledWith('/api/custom-health', expect.any(Object));
    });

    it('should use default /health endpoint', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true });

      render(<ConnectionStatus />);

      await act(async () => {
        await vi.runAllTimersAsync();
      });

      expect(mockFetch).toHaveBeenCalledWith('/health', expect.any(Object));
    });
  });
});
