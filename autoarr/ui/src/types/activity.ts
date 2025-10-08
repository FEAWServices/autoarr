/**
 * TypeScript types for Activity and WebSocket events
 *
 * These types define the structure of activity logs and real-time events
 * from the backend WebSocket connection.
 */

/**
 * Activity log entry types
 */
export type ActivityType =
  | "download"
  | "search"
  | "import"
  | "config_change"
  | "error"
  | "audit"
  | "system";

/**
 * Service names that can generate activities
 */
export type ActivityService =
  | "sabnzbd"
  | "sonarr"
  | "radarr"
  | "plex"
  | "autoarr"
  | "system";

/**
 * Activity log severity levels
 */
export type ActivityLevel = "info" | "warning" | "error" | "success";

/**
 * Activity log entry
 */
export interface Activity {
  id: string;
  timestamp: string;
  type: ActivityType;
  service: ActivityService;
  level: ActivityLevel;
  title: string;
  description: string;
  metadata?: Record<string, unknown>;
  user?: string;
}

/**
 * Paginated activity response
 */
export interface ActivityListResponse {
  activities: Activity[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

/**
 * Activity filter options
 */
export interface ActivityFilters {
  type?: ActivityType[];
  service?: ActivityService[];
  level?: ActivityLevel[];
  startDate?: string;
  endDate?: string;
  search?: string;
}

/**
 * WebSocket event types
 */
export type WebSocketEventType =
  | "activity"
  | "audit_complete"
  | "config_applied"
  | "connection_status"
  | "error";

/**
 * Base WebSocket message
 */
export interface WebSocketMessage<T = unknown> {
  type: WebSocketEventType;
  timestamp: string;
  data: T;
}

/**
 * Activity WebSocket event
 */
export interface ActivityEvent extends WebSocketMessage<Activity> {
  type: "activity";
}

/**
 * Audit complete WebSocket event
 */
export interface AuditCompleteEvent
  extends WebSocketMessage<{
    audit_id: string;
    total_recommendations: number;
    services: string[];
  }> {
  type: "audit_complete";
}

/**
 * Config applied WebSocket event
 */
export interface ConfigAppliedEvent
  extends WebSocketMessage<{
    recommendation_id: number;
    service: string;
    success: boolean;
  }> {
  type: "config_applied";
}

/**
 * Connection status WebSocket event
 */
export interface ConnectionStatusEvent
  extends WebSocketMessage<{
    status: "connected" | "disconnected" | "error";
    message?: string;
  }> {
  type: "connection_status";
}

/**
 * Error WebSocket event
 */
export interface ErrorEvent
  extends WebSocketMessage<{
    code: string;
    message: string;
  }> {
  type: "error";
}

/**
 * Union type of all WebSocket events
 */
export type WebSocketEvent =
  | ActivityEvent
  | AuditCompleteEvent
  | ConfigAppliedEvent
  | ConnectionStatusEvent
  | ErrorEvent;

/**
 * WebSocket connection state
 */
export type WebSocketConnectionState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "error";

/**
 * WebSocket configuration options
 */
export interface WebSocketConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

/**
 * WebSocket store state
 */
export interface WebSocketState {
  connectionState: WebSocketConnectionState;
  lastError: string | null;
  reconnectAttempts: number;
  isConnected: boolean;
  lastHeartbeat: number | null;
}
