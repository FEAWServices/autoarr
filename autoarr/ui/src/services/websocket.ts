/**
 * WebSocket Service for Real-time Updates
 *
 * Provides real-time updates for:
 * - Content request status changes
 * - Download progress
 * - System notifications
 *
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Connection state management
 * - Event-based message handling
 */

import { WebSocketEvent, WebSocketEventType } from "../types/chat";

type ConnectionState = "connecting" | "connected" | "disconnected" | "error";

type EventHandler = (event: WebSocketEvent) => void;

interface WebSocketConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
  reconnectDecay?: number;
  maxReconnectAttempts?: number;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private reconnectAttempts = 0;
  private reconnectTimeoutId?: number;
  private eventHandlers: Map<WebSocketEventType | "all", EventHandler[]> =
    new Map();
  private stateChangeHandlers: Array<(state: ConnectionState) => void> = [];
  private connectionState: ConnectionState = "disconnected";

  constructor(config: WebSocketConfig) {
    this.config = {
      url: config.url,
      reconnectInterval: config.reconnectInterval || 1000,
      maxReconnectInterval: config.maxReconnectInterval || 30000,
      reconnectDecay: config.reconnectDecay || 1.5,
      maxReconnectAttempts: config.maxReconnectAttempts || Infinity,
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (
      this.ws?.readyState === WebSocket.OPEN ||
      this.ws?.readyState === WebSocket.CONNECTING
    ) {
      return;
    }

    this.setConnectionState("connecting");

    try {
      this.ws = new WebSocket(this.config.url);

      this.ws.onopen = () => {
        console.log("WebSocket connected");
        this.reconnectAttempts = 0;
        this.setConnectionState("connected");
      };

      this.ws.onmessage = (event) => {
        this.handleMessage(event.data);
      };

      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        this.setConnectionState("error");
      };

      this.ws.onclose = (event) => {
        console.log("WebSocket closed:", event.code, event.reason);
        this.setConnectionState("disconnected");

        // Attempt reconnection if not a normal closure
        if (event.code !== 1000 && event.code !== 1001) {
          this.scheduleReconnect();
        }
      };
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      this.setConnectionState("error");
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = undefined;
    }

    if (this.ws) {
      this.ws.close(1000, "Client disconnect");
      this.ws = null;
    }

    this.setConnectionState("disconnected");
  }

  /**
   * Send a message through WebSocket
   */
  send(data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn("WebSocket is not open. Message not sent:", data);
    }
  }

  /**
   * Register event handler for specific event type
   */
  on(eventType: WebSocketEventType | "all", handler: EventHandler): void {
    const handlers = this.eventHandlers.get(eventType) || [];
    handlers.push(handler);
    this.eventHandlers.set(eventType, handlers);
  }

  /**
   * Unregister event handler
   */
  off(eventType: WebSocketEventType | "all", handler: EventHandler): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      const filtered = handlers.filter((h) => h !== handler);
      this.eventHandlers.set(eventType, filtered);
    }
  }

  /**
   * Register connection state change handler
   */
  onStateChange(handler: (state: ConnectionState) => void): void {
    this.stateChangeHandlers.push(handler);
  }

  /**
   * Get current connection state
   */
  getState(): ConnectionState {
    return this.connectionState;
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return (
      this.ws?.readyState === WebSocket.OPEN &&
      this.connectionState === "connected"
    );
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(data: string): void {
    try {
      const event: WebSocketEvent = JSON.parse(data);

      // Call type-specific handlers
      const typeHandlers = this.eventHandlers.get(event.type) || [];
      typeHandlers.forEach((handler) => handler(event));

      // Call "all" handlers
      const allHandlers = this.eventHandlers.get("all") || [];
      allHandlers.forEach((handler) => handler(event));
    } catch (error) {
      console.error("Failed to parse WebSocket message:", error, data);
    }
  }

  /**
   * Schedule a reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      return;
    }

    const delay = Math.min(
      this.config.reconnectInterval *
        Math.pow(this.config.reconnectDecay, this.reconnectAttempts),
      this.config.maxReconnectInterval,
    );

    console.log(
      `Scheduling reconnection in ${delay}ms (attempt ${
        this.reconnectAttempts + 1
      })`,
    );

    this.reconnectTimeoutId = window.setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  /**
   * Update connection state and notify handlers
   */
  private setConnectionState(state: ConnectionState): void {
    if (this.connectionState !== state) {
      this.connectionState = state;
      this.stateChangeHandlers.forEach((handler) => handler(state));
    }
  }
}

// Create singleton instance
const WS_URL = "ws://localhost:8000/api/v1/ws";

export const websocketService = new WebSocketService({
  url: WS_URL,
  reconnectInterval: 1000,
  maxReconnectInterval: 30000,
  reconnectDecay: 1.5,
  maxReconnectAttempts: 10,
});

// Auto-connect on module load
if (typeof window !== "undefined") {
  websocketService.connect();

  // Cleanup on page unload
  window.addEventListener("beforeunload", () => {
    websocketService.disconnect();
  });
}

export type { ConnectionState };
