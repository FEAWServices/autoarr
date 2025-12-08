/**
 * Unit tests for Sidebar component
 *
 * Regression tests to ensure AI service is displayed in sidebar status
 * Bug: AI service was missing from sidebar service status list
 * Fix: Added AI to the services array with /api/v1/settings/llm status check
 */

import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Import component after mocking
const { Sidebar } = await import('../../components/Sidebar');

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe('Sidebar AI Service Status - Regression', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    // Default mock: all services offline
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/health/')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ healthy: false }),
        });
      }
      if (url.includes('/api/v1/settings/llm')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              enabled: false,
              api_key_masked: null,
            }),
        });
      }
      return Promise.resolve({ ok: false });
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Service Status Display', () => {
    it('should display AI service in service status list', async () => {
      renderWithRouter(<Sidebar />);

      // Wait for the sidebar to render and services to load
      await waitFor(() => {
        const aiStatusIndicator = screen.getByTestId('sidebar-status-ai');
        expect(aiStatusIndicator).toBeInTheDocument();
      });

      // Verify it shows "AI" text
      const aiStatusIndicator = screen.getByTestId('sidebar-status-ai');
      expect(aiStatusIndicator).toHaveTextContent('AI');
    });

    it('should display all 5 services (SABnzbd, Sonarr, Radarr, Plex, AI)', async () => {
      renderWithRouter(<Sidebar />);

      await waitFor(() => {
        expect(screen.getByTestId('sidebar-status-sabnzbd')).toBeInTheDocument();
        expect(screen.getByTestId('sidebar-status-sonarr')).toBeInTheDocument();
        expect(screen.getByTestId('sidebar-status-radarr')).toBeInTheDocument();
        expect(screen.getByTestId('sidebar-status-plex')).toBeInTheDocument();
        expect(screen.getByTestId('sidebar-status-ai')).toBeInTheDocument();
      });
    });

    it('should show correct service count (x/5)', async () => {
      renderWithRouter(<Sidebar />);

      await waitFor(() => {
        const serviceStatus = screen
          .getByTestId('sidebar-status-ai')
          ?.closest('[data-component="SidebarServiceStatus"]');
        expect(serviceStatus).toHaveTextContent('/5)');
      });
    });
  });

  describe('AI Service Connection Status', () => {
    it('should show AI as connected when LLM is enabled with API key', async () => {
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/health/')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ healthy: false }),
          });
        }
        if (url.includes('/api/v1/settings/llm')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                enabled: true,
                api_key_masked: 'sk-or-v1-***',
              }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      renderWithRouter(<Sidebar />);

      await waitFor(() => {
        const aiStatusIndicator = screen.getByTestId('sidebar-status-ai');
        // When connected, should have green color
        expect(aiStatusIndicator).toHaveTextContent('AI');
        // The text should have green color class
        const textSpan = aiStatusIndicator.querySelector('span.text-green-500');
        expect(textSpan).toBeInTheDocument();
      });
    });

    it('should show AI as disconnected when LLM is disabled', async () => {
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/health/')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ healthy: false }),
          });
        }
        if (url.includes('/api/v1/settings/llm')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                enabled: false,
                api_key_masked: null,
              }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      renderWithRouter(<Sidebar />);

      await waitFor(() => {
        const aiStatusIndicator = screen.getByTestId('sidebar-status-ai');
        // When disconnected, should have red color
        const textSpan = aiStatusIndicator.querySelector('span.text-red-500');
        expect(textSpan).toBeInTheDocument();
      });
    });

    it('should show AI as disconnected when API key is missing', async () => {
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/health/')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ healthy: false }),
          });
        }
        if (url.includes('/api/v1/settings/llm')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                enabled: true,
                api_key_masked: null, // No API key configured
              }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      renderWithRouter(<Sidebar />);

      await waitFor(() => {
        const aiStatusIndicator = screen.getByTestId('sidebar-status-ai');
        // Should be red (disconnected) because no API key
        const textSpan = aiStatusIndicator.querySelector('span.text-red-500');
        expect(textSpan).toBeInTheDocument();
      });
    });

    it('should handle LLM API error gracefully', async () => {
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/health/')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ healthy: false }),
          });
        }
        if (url.includes('/api/v1/settings/llm')) {
          return Promise.reject(new Error('Network error'));
        }
        return Promise.resolve({ ok: false });
      });

      renderWithRouter(<Sidebar />);

      // Should still render without crashing
      await waitFor(() => {
        const aiStatusIndicator = screen.getByTestId('sidebar-status-ai');
        expect(aiStatusIndicator).toBeInTheDocument();
        // Should show as disconnected on error
        const textSpan = aiStatusIndicator.querySelector('span.text-red-500');
        expect(textSpan).toBeInTheDocument();
      });
    });
  });

  describe('Service Status Fetching', () => {
    it('should call health endpoints for all services', async () => {
      renderWithRouter(<Sidebar />);

      await waitFor(() => {
        // Verify all health endpoints were called
        expect(mockFetch).toHaveBeenCalledWith('/health/sabnzbd');
        expect(mockFetch).toHaveBeenCalledWith('/health/sonarr');
        expect(mockFetch).toHaveBeenCalledWith('/health/radarr');
        expect(mockFetch).toHaveBeenCalledWith('/health/plex');
      });
    });

    it('should call LLM settings endpoint for AI status', async () => {
      renderWithRouter(<Sidebar />);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/v1/settings/llm');
      });
    });
  });
});
