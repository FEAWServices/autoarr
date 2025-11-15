/**
 * Chat Service for API Integration
 *
 * Handles communication with the AutoArr backend API for:
 * - Content requests
 * - Confirmation of selections
 * - Request status tracking
 * - Request cancellation
 */

import {
  ContentRequestPayload,
  ContentRequestResponse,
  ConfirmationPayload,
  ConfirmationResponse,
  RequestInfo,
} from "../types/chat";

// Use environment variable with fallback to correct port (8088, not 8000)
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8088/api/v1";
const REQUEST_TIMEOUT = 30000; // 30 seconds

class ChatService {
  /**
   * Send a content request query to the backend
   * @param query - User's natural language query
   * @returns Response with classification and search results
   */
  async sendMessage(query: string): Promise<ContentRequestResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
      const payload: ContentRequestPayload = { query };

      const response = await fetch(`${API_BASE_URL}/request/content`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: "An error occurred while processing your request",
        }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const data: ContentRequestResponse = await response.json();
      return data;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof Error) {
        if (error.name === "AbortError") {
          throw new Error(
            "Request timed out. The server is taking too long to respond.",
          );
        }
        throw error;
      }

      throw new Error("An unexpected error occurred");
    }
  }

  /**
   * Confirm a content selection and add to library
   * @param requestId - ID of the content request
   * @param tmdbId - TMDB ID of the selected content
   * @param quality - Optional quality setting
   * @returns Confirmation response with status
   */
  async confirmSelection(
    requestId: string,
    tmdbId: number,
    quality?: string,
  ): Promise<ConfirmationResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
      const payload: ConfirmationPayload = {
        requestId,
        tmdbId,
        quality,
      };

      const response = await fetch(`${API_BASE_URL}/request/confirm`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: "Failed to add content to library",
        }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const data: ConfirmationResponse = await response.json();
      return data;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof Error) {
        if (error.name === "AbortError") {
          throw new Error("Request timed out. Please try again.");
        }
        throw error;
      }

      throw new Error("Failed to confirm selection");
    }
  }

  /**
   * Get the current status of a content request
   * @param requestId - ID of the content request
   * @returns Request information with current status
   */
  async getRequestStatus(requestId: string): Promise<RequestInfo> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/request/status/${requestId}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        },
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: "Failed to fetch request status",
        }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const data: RequestInfo = await response.json();
      return data;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error("Failed to get request status");
    }
  }

  /**
   * Cancel an in-progress content request
   * @param requestId - ID of the content request
   */
  async cancelRequest(requestId: string): Promise<void> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/request/cancel/${requestId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        },
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: "Failed to cancel request",
        }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error("Failed to cancel request");
    }
  }

  /**
   * Retry a failed content request
   * @param requestId - ID of the failed request
   * @returns New request response
   */
  async retryRequest(requestId: string): Promise<ContentRequestResponse> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/request/retry/${requestId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        },
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: "Failed to retry request",
        }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const data: ContentRequestResponse = await response.json();
      return data;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error("Failed to retry request");
    }
  }
}

// Export singleton instance
export const chatService = new ChatService();
