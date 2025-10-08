/**
 * WebSocket Service
 *
 * Manages WebSocket connection to backend for real-time updates
 * Features:
 * - Auto-reconnection with exponential backoff
 * - Connection state management
 * - Event handler registration
 * - Heartbeat/ping mechanism
 * - Type-safe event handling
 */

import type {
  WebSocketConfig,
  WebSocketEvent,
  WebSocketEventType,
  WebSocketConnectionState,
} from "../types/activity";

type EventHandler<T = unknown> = (data: T) => void;

export class WebSocketService {
  private socket: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private eventHandlers: Map<WebSocketEventType, Set<EventHandler>>;
  private connectionState: WebSocketConnectionState = "disconnected";
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private stateChangeCallbacks: Set<(state: WebSocketConnectionState) => void>;

  constructor(config: WebSocketConfig) {
    this.config = {
      url: config.url,
      reconnectInterval: config.reconnectInterval || 3000,
      maxReconnectAttempts: config.maxReconnectAttempts || 10,
      heartbeatInterval: config.heartbeatInterval || 30000,
    };
    this.eventHandlers = new Map();
    this.stateChangeCallbacks = new Set();
  }

  /**
   * Connect to WebSocket server
   */
  public connect(): void {
    if (
      this.socket &&
      (this.socket.readyState === WebSocket.CONNECTING ||
        this.socket.readyState === WebSocket.OPEN)
    ) {
      return;
    }

    this.updateConnectionState("connecting");

    try {
      this.socket = new WebSocket(this.config.url);
      this.setupSocketListeners();
    } catch (error) {
      console.error("Failed to create WebSocket connection:", error);
      this.updateConnectionState("error");
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  public disconnect(): void {
    this.clearReconnectTimer();
    this.clearHeartbeatTimer();

    if (this.socket) {
      this.socket.close(1000, "Client disconnecting");
      this.socket = null;
    }

    this.updateConnectionState("disconnected");
  }

  /**
   * Register event handler for specific event type
   */
  public on<T = unknown>(
    eventType: WebSocketEventType,
    handler: EventHandler<T>,
  ): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }

    this.eventHandlers.get(eventType)!.add(handler as EventHandler);

    // Return unsubscribe function
    return () => {
      this.off(eventType, handler);
    };
  }

  /**
   * Remove event handler
   */
  public off<T = unknown>(
    eventType: WebSocketEventType,
    handler: EventHandler<T>,
  ): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.delete(handler as EventHandler);
    }
  }

  /**
   * Subscribe to connection state changes
   */
  public onStateChange(
    callback: (state: WebSocketConnectionState) => void,
  ): () => void {
    this.stateChangeCallbacks.add(callback);

    // Return unsubscribe function
    return () => {
      this.stateChangeCallbacks.delete(callback);
    };
  }

  /**
   * Get current connection state
   */
  public getConnectionState(): WebSocketConnectionState {
    return this.connectionState;
  }

  /**
   * Get reconnect attempts count
   */
  public getReconnectAttempts(): number {
    return this.reconnectAttempts;
  }

  /**
   * Setup WebSocket event listeners
   */
  private setupSocketListeners(): void {
    if (!this.socket) return;

    this.socket.onopen = () => {
      console.log("WebSocket connected");
      this.updateConnectionState("connected");
      this.reconnectAttempts = 0;
      this.startHeartbeat();
    };

    this.socket.onmessage = (event: MessageEvent) => {
      try {
        const message: WebSocketEvent = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };

    this.socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      this.updateConnectionState("error");
    };

    this.socket.onclose = (event) => {
      console.log("WebSocket closed:", event.code, event.reason);
      this.clearHeartbeatTimer();

      // Don't reconnect if closed intentionally by client
      if (event.code !== 1000) {
        this.updateConnectionState("reconnecting");
        this.scheduleReconnect();
      } else {
        this.updateConnectionState("disconnected");
      }
    };
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(message: WebSocketEvent): void {
    const handlers = this.eventHandlers.get(message.type);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(message.data);
        } catch (error) {
          console.error(`Error in ${message.type} handler:`, error);
        }
      });
    }
  }

  /**
   * Update connection state and notify callbacks
   */
  private updateConnectionState(state: WebSocketConnectionState): void {
    if (this.connectionState !== state) {
      this.connectionState = state;
      this.stateChangeCallbacks.forEach((callback) => {
        try {
          callback(state);
        } catch (error) {
          console.error("Error in state change callback:", error);
        }
      });
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error("Max reconnect attempts reached");
      this.updateConnectionState("error");
      return;
    }

    this.clearReconnectTimer();

    // Exponential backoff: 3s, 6s, 12s, 24s, 48s...
    const delay =
      this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts);
    const maxDelay = 60000; // Max 60 seconds
    const reconnectDelay = Math.min(delay, maxDelay);

    console.log(
      `Reconnecting in ${reconnectDelay}ms (attempt ${
        this.reconnectAttempts + 1
      }/${this.config.maxReconnectAttempts})`,
    );

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, reconnectDelay);
  }

  /**
   * Start heartbeat interval
   */
  private startHeartbeat(): void {
    this.clearHeartbeatTimer();

    this.heartbeatTimer = setInterval(() => {
      if (
        this.socket &&
        this.socket.readyState === WebSocket.OPEN &&
        this.connectionState === "connected"
      ) {
        // Send ping message
        try {
          this.socket.send(JSON.stringify({ type: "ping" }));
        } catch (error) {
          console.error("Failed to send heartbeat:", error);
        }
      }
    }, this.config.heartbeatInterval);
  }

  /**
   * Clear reconnect timer
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Clear heartbeat timer
   */
  private clearHeartbeatTimer(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }
}

// Singleton instance
let websocketInstance: WebSocketService | null = null;

/**
 * Get WebSocket service instance (singleton)
 */
export function getWebSocketService(
  config?: WebSocketConfig,
): WebSocketService {
  if (!websocketInstance && config) {
    websocketInstance = new WebSocketService(config);
  }

  if (!websocketInstance) {
    throw new Error("WebSocket service not initialized. Provide config first.");
  }

  return websocketInstance;
}

/**
 * Reset WebSocket service (useful for testing)
 */
export function resetWebSocketService(): void {
  if (websocketInstance) {
    websocketInstance.disconnect();
    websocketInstance = null;
  }
}
