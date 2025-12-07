/**
 * Chat Service for API Integration
 *
 * Handles communication with the AutoArr backend API for:
 * - Intelligent chat assistant (help with SABnzbd, Sonarr, Radarr, Plex, AutoArr)
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
} from '../types/chat';
import { apiV1Url } from './api';

const REQUEST_TIMEOUT = 30000; // 30 seconds
const CHAT_TIMEOUT = 60000; // 60 seconds for chat (may need to fetch docs)

/**
 * Response from the intelligent chat endpoint
 */
export interface ChatMessageResponse {
  message: string;
  topic: string;
  intent: string;
  sources: Array<{ title: string; url: string }>;
  suggestions: string[];
  confidence: number;
  is_content_request: boolean;
  service_required?: string;
  setup_link?: string;
}

/**
 * Topic classification response
 */
export interface TopicClassification {
  topic: string;
  intent: string;
  confidence: number;
  entities: Record<string, unknown>;
  needs_docs: boolean;
}

/**
 * Supported chat topics
 */
export interface ChatTopicsResponse {
  topics: Array<{
    id: string;
    name: string;
    description: string;
    icon: string;
  }>;
  suggestions: string[];
}

class ChatService {
  private conversationHistory: Array<{ role: string; content: string }> = [];

  /**
   * Send a message to the intelligent chat assistant
   * @param message - User's message
   * @returns Response with message, topic, sources, and suggestions
   */
  async sendChatMessage(message: string): Promise<ChatMessageResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), CHAT_TIMEOUT);

    try {
      const response = await fetch(apiV1Url('/chat/message'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          history: this.conversationHistory.slice(-6), // Last 6 messages for context
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: 'An error occurred while processing your message',
        }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const data: ChatMessageResponse = await response.json();

      // Update conversation history
      this.conversationHistory.push({ role: 'user', content: message });
      this.conversationHistory.push({ role: 'assistant', content: data.message });

      // Keep history manageable
      if (this.conversationHistory.length > 20) {
        this.conversationHistory = this.conversationHistory.slice(-20);
      }

      return data;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error('Request timed out. The server is taking too long to respond.');
        }
        throw error;
      }

      throw new Error('An unexpected error occurred');
    }
  }

  /**
   * Classify a query without generating full response
   * @param message - User's message to classify
   * @returns Topic classification result
   */
  async classifyQuery(message: string): Promise<TopicClassification> {
    try {
      const response = await fetch(apiV1Url('/chat/classify'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Default classification on error
      return {
        topic: 'general_media',
        intent: 'help',
        confidence: 0.5,
        entities: {},
        needs_docs: false,
      };
    }
  }

  /**
   * Get supported chat topics
   * @returns List of topics and suggestions
   */
  async getTopics(): Promise<ChatTopicsResponse> {
    try {
      const response = await fetch(apiV1Url('/chat/topics'));

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch {
      // Return default topics on error
      return {
        topics: [
          { id: 'sabnzbd', name: 'SABnzbd', description: 'Download client', icon: 'download' },
          { id: 'sonarr', name: 'Sonarr', description: 'TV automation', icon: 'tv' },
          { id: 'radarr', name: 'Radarr', description: 'Movie automation', icon: 'film' },
          { id: 'plex', name: 'Plex', description: 'Media server', icon: 'server' },
          { id: 'autoarr', name: 'AutoArr', description: 'This app', icon: 'sparkles' },
        ],
        suggestions: [],
      };
    }
  }

  /**
   * Clear conversation history
   */
  clearHistory(): void {
    this.conversationHistory = [];
  }

  /**
   * Send a content request query to the backend (legacy endpoint for downloads)
   * @param query - User's natural language query
   * @returns Response with classification and search results
   */
  async sendMessage(query: string): Promise<ContentRequestResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
      const payload: ContentRequestPayload = { query };

      const response = await fetch(apiV1Url('/requests/content'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: 'An error occurred while processing your request',
        }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const data: ContentRequestResponse = await response.json();
      return data;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error('Request timed out. The server is taking too long to respond.');
        }
        throw error;
      }

      throw new Error('An unexpected error occurred');
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
    quality?: string
  ): Promise<ConfirmationResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
      const payload: ConfirmationPayload = {
        requestId,
        tmdbId,
        quality,
      };

      const response = await fetch(apiV1Url(`/requests/${requestId}/confirm`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: 'Failed to add content to library',
        }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const data: ConfirmationResponse = await response.json();
      return data;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error('Request timed out. Please try again.');
        }
        throw error;
      }

      throw new Error('Failed to confirm selection');
    }
  }

  /**
   * Get the current status of a content request
   * @param requestId - ID of the content request
   * @returns Request information with current status
   */
  async getRequestStatus(requestId: string): Promise<RequestInfo> {
    try {
      const response = await fetch(apiV1Url(`/requests/${requestId}/status`), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: 'Failed to fetch request status',
        }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const data: RequestInfo = await response.json();
      return data;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to get request status');
    }
  }

  /**
   * Cancel an in-progress content request
   * @param requestId - ID of the content request
   */
  async cancelRequest(requestId: string): Promise<void> {
    try {
      const response = await fetch(apiV1Url(`/requests/${requestId}`), {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: 'Failed to cancel request',
        }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to cancel request');
    }
  }
}

// Export singleton instance
export const chatService = new ChatService();
