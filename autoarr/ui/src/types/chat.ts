/**
 * TypeScript types for Chat functionality
 *
 * These types define the structure for chat messages, content search results,
 * and request tracking in the AutoArr chat interface.
 */

/**
 * Message type discriminator
 */
export type MessageType = 'user' | 'assistant' | 'system';

/**
 * Content type from classification
 */
export type ContentType = 'movie' | 'tv' | 'unknown';

/**
 * Request status lifecycle
 */
export type RequestStatus =
  | 'submitted'
  | 'classified'
  | 'searching'
  | 'pending_confirmation'
  | 'downloading'
  | 'completed'
  | 'failed'
  | 'cancelled';

/**
 * Content classification result from LLM
 * Matches backend ContentClassification model
 */
export interface ContentClassification {
  content_type: ContentType;
  title: string;
  year?: number | null;
  quality?: string | null;
  season?: number | null;
  episode?: number | null;
  confidence: number;
}

/**
 * Search result from TMDB
 */
export interface ContentSearchResult {
  tmdbId: number;
  title: string;
  originalTitle?: string;
  year: number;
  overview: string;
  posterPath?: string;
  backdropPath?: string;
  voteAverage?: number;
  voteCount?: number;
  mediaType: ContentType;
  releaseDate?: string;
  firstAirDate?: string;
}

/**
 * Request tracking information
 */
export interface RequestInfo {
  requestId: string;
  status: RequestStatus;
  title: string;
  type: ContentType;
  tmdbId?: number;
  progress?: number;
  eta?: string;
  error?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Source reference for documentation
 */
export interface SourceReference {
  title: string;
  url: string;
}

/**
 * Chat message metadata
 */
export interface MessageMetadata {
  // Content request flow
  classification?: ContentClassification;
  searchResults?: ContentSearchResult[];
  requestId?: string;
  requestStatus?: RequestStatus;
  error?: string;

  // Intelligent chat flow
  topic?: string;
  intent?: string;
  sources?: SourceReference[];
  suggestions?: string[];
  serviceRequired?: string;
  setupLink?: string;
}

/**
 * Core message structure
 */
export interface Message {
  id: string;
  type: MessageType;
  content: string;
  timestamp: Date;
  metadata?: MessageMetadata;
}

/**
 * Chat application state
 */
export interface ChatState {
  messages: Message[];
  isTyping: boolean;
  currentRequestId: string | null;
  error: string | null;
}

/**
 * WebSocket event types for real-time updates
 */
export type WebSocketEventType =
  | 'connection'
  | 'event'
  | 'ack'
  | 'request-submitted'
  | 'request-classified'
  | 'request-searching'
  | 'request-downloading'
  | 'request-completed'
  | 'request-failed'
  | 'download-progress'
  | 'download-started'
  | 'download-completed'
  | 'download-failed'
  | 'download-paused'
  | 'download-resumed'
  | 'download-state-changed'
  | 'recovery-attempted'
  | 'recovery-success'
  | 'recovery-failed'
  | 'config-audit-started'
  | 'config-audit-completed'
  | 'config-audit-failed';

/**
 * WebSocket event payload
 */
export interface WebSocketEvent {
  type: WebSocketEventType;
  event_type?: string;
  correlation_id?: string;
  requestId?: string;
  data?: {
    status?: RequestStatus;
    progress?: number;
    eta?: string;
    error?: string;
    title?: string;
    nzo_id?: string;
    filename?: string;
    category?: string;
    strategy?: string;
    message?: string;
    [key: string]: unknown;
  };
  metadata?: {
    source?: string;
    [key: string]: unknown;
  };
  timestamp?: string;
  message?: string;
  status?: string;
}

/**
 * API request payload for content request
 */
export interface ContentRequestPayload {
  query: string;
}

/**
 * API response for content request
 * Matches backend ContentRequestResponse model
 */
export interface ContentRequestResponse {
  id: number;
  correlation_id: string;
  query: string;
  classification: ContentClassification;
  status: string;
  search_results?: ContentSearchResult[];
  created_at: string;
}

/**
 * API request payload for confirmation
 */
export interface ConfirmationPayload {
  requestId: string;
  tmdbId: number;
  quality?: string;
}

/**
 * API response for confirmation
 */
export interface ConfirmationResponse {
  requestId: string;
  message: string;
  status: RequestStatus;
}

/**
 * Chat history filter options
 */
export interface ChatHistoryFilter {
  type?: ContentType;
  status?: RequestStatus;
  searchTerm?: string;
  dateFrom?: Date;
  dateTo?: Date;
}

/**
 * localStorage schema for chat persistence
 */
export interface ChatHistoryStorage {
  messages: Message[];
  version: string;
  lastUpdated: string;
}
