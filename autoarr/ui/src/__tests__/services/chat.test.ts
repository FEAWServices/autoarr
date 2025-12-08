/**
 * Unit tests for chat service API endpoints
 *
 * Regression tests to ensure API endpoint URLs use correct plural form
 * Bug: Frontend was calling /api/v1/request/content (singular)
 * Fix: Should call /api/v1/requests/content (plural)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock fetch before importing the service
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Import the service after mocking fetch
const { chatService } = await import('../../services/chat');

describe('ChatService API Endpoints - Regression', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    });
  });

  describe('Endpoint URL correctness (singular vs plural)', () => {
    it('sendMessage should call /api/v1/requests/content (plural)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            requestId: 'test-123',
            contentType: 'movie',
            status: 'pending',
            results: [],
          }),
      });

      await chatService.sendMessage('test query');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/requests/content'),
        expect.any(Object)
      );
      // Ensure it's NOT the singular form
      expect(mockFetch).not.toHaveBeenCalledWith(
        expect.stringContaining('/request/content'),
        expect.any(Object)
      );
    });

    it('confirmSelection should call /api/v1/requests/confirm (plural)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            success: true,
            status: 'added',
          }),
      });

      await chatService.confirmSelection('test-id', 12345);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/requests/confirm'),
        expect.any(Object)
      );
      expect(mockFetch).not.toHaveBeenCalledWith(
        expect.stringContaining('/request/confirm'),
        expect.any(Object)
      );
    });

    it('getRequestStatus should call /api/v1/requests/status (plural)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            status: 'processing',
          }),
      });

      await chatService.getRequestStatus('test-id');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/requests/status/'),
        expect.any(Object)
      );
      expect(mockFetch).not.toHaveBeenCalledWith(
        expect.stringContaining('/request/status/'),
        expect.any(Object)
      );
    });

    it('cancelRequest should call /api/v1/requests/cancel (plural)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      await chatService.cancelRequest('test-id');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/requests/cancel/'),
        expect.any(Object)
      );
      expect(mockFetch).not.toHaveBeenCalledWith(
        expect.stringContaining('/request/cancel/'),
        expect.any(Object)
      );
    });

    it('retryRequest should call /api/v1/requests/retry (plural)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            requestId: 'test-123',
            contentType: 'movie',
            status: 'pending',
            results: [],
          }),
      });

      await chatService.retryRequest('test-id');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/requests/retry/'),
        expect.any(Object)
      );
      expect(mockFetch).not.toHaveBeenCalledWith(
        expect.stringContaining('/request/retry/'),
        expect.any(Object)
      );
    });
  });

  describe('Request payload format', () => {
    it('sendMessage should include query in request body', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            requestId: 'test-123',
            contentType: 'movie',
            status: 'pending',
            results: [],
          }),
      });

      await chatService.sendMessage('Find the Matrix movie');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify({ query: 'Find the Matrix movie' }),
        })
      );
    });

    it('confirmSelection should include requestId, tmdbId, and optional quality', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            success: true,
            status: 'added',
          }),
      });

      await chatService.confirmSelection('req-123', 550, '1080p');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            requestId: 'req-123',
            tmdbId: 550,
            quality: '1080p',
          }),
        })
      );
    });
  });

  describe('Error handling', () => {
    it('should throw error with message on non-ok response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () =>
          Promise.resolve({
            detail: 'Server error occurred',
          }),
      });

      await expect(chatService.sendMessage('test')).rejects.toThrow('Server error occurred');
    });

    it('should throw timeout error when request times out', async () => {
      // Mock AbortError
      mockFetch.mockRejectedValueOnce(
        Object.assign(new Error('The operation was aborted'), { name: 'AbortError' })
      );

      await expect(chatService.sendMessage('test')).rejects.toThrow('Request timed out');
    });
  });
});
