/**
 * useWebSocket Hook
 *
 * React hook for managing WebSocket connection and receiving real-time events
 * Features:
 * - Automatic connection management
 * - Connection state tracking
 * - Event subscription
 * - Cleanup on unmount
 */

import { useEffect, useState, useCallback, useRef } from "react";
import { getWebSocketService } from "../services/websocket";
import type {
  WebSocketConnectionState,
  WebSocketEventType,
} from "../types/activity";

interface UseWebSocketOptions {
  url?: string;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

interface UseWebSocketReturn {
  connectionState: WebSocketConnectionState;
  reconnectAttempts: number;
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  subscribe: <T = unknown>(
    eventType: WebSocketEventType,
    handler: (data: T) => void,
  ) => () => void;
}

/**
 * Custom hook for WebSocket connection
 */
export function useWebSocket(
  options: UseWebSocketOptions = {},
): UseWebSocketReturn {
  const {
    url = `ws://${window.location.hostname}:8000/ws`,
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
  } = options;

  const [connectionState, setConnectionState] =
    useState<WebSocketConnectionState>("disconnected");
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const serviceRef = useRef(
    getWebSocketService({
      url,
      reconnectInterval,
      maxReconnectAttempts,
    }),
  );

  // Update connection state when it changes
  useEffect(() => {
    const service = serviceRef.current;

    const unsubscribe = service.onStateChange((state) => {
      setConnectionState(state);
      setReconnectAttempts(service.getReconnectAttempts());
    });

    // Set initial state
    setConnectionState(service.getConnectionState());
    setReconnectAttempts(service.getReconnectAttempts());

    return unsubscribe;
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      serviceRef.current.connect();
    }

    // Cleanup on unmount
    return () => {
      if (autoConnect) {
        serviceRef.current.disconnect();
      }
    };
  }, [autoConnect]);

  const connect = useCallback(() => {
    serviceRef.current.connect();
  }, []);

  const disconnect = useCallback(() => {
    serviceRef.current.disconnect();
  }, []);

  const subscribe = useCallback(
    <T = unknown>(
      eventType: WebSocketEventType,
      handler: (data: T) => void,
    ): (() => void) => {
      return serviceRef.current.on<T>(eventType, handler);
    },
    [],
  );

  const isConnected = connectionState === "connected";

  return {
    connectionState,
    reconnectAttempts,
    isConnected,
    connect,
    disconnect,
    subscribe,
  };
}
