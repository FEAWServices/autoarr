/**
 * Zustand Store for Chat State Management
 *
 * Manages:
 * - Chat messages (user, assistant, system)
 * - Message history persistence
 * - Current request tracking
 * - Typing indicator state
 * - Request status updates
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { Message, RequestInfo, RequestStatus } from "../types/chat";

interface ChatStore {
  // State
  messages: Message[];
  isTyping: boolean;
  currentRequestId: string | null;
  currentRequests: Map<string, RequestInfo>;
  error: string | null;

  // Message Actions
  addMessage: (message: Message) => void;
  clearHistory: () => void;
  loadHistory: () => void;
  saveHistory: () => void;

  // Typing Actions
  setTyping: (isTyping: boolean) => void;

  // Request Actions
  setCurrentRequestId: (requestId: string | null) => void;
  updateRequestStatus: (requestId: string, request: RequestInfo) => void;
  getRequest: (requestId: string) => RequestInfo | undefined;
  removeRequest: (requestId: string) => void;

  // Error Actions
  setError: (error: string | null) => void;

  // Utility Actions
  getFilteredMessages: (filter?: {
    type?: "movie" | "tv";
    status?: RequestStatus;
    searchTerm?: string;
  }) => Message[];
}

const STORAGE_KEY = "autoarr-chat-history";
const STORAGE_VERSION = "1.0";
const MAX_RETENTION_DAYS = 30;

// Helper to clean old messages
const cleanOldMessages = (messages: Message[]): Message[] => {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - MAX_RETENTION_DAYS);

  return messages.filter((msg) => msg.timestamp >= cutoffDate);
};

// Load messages from localStorage
const loadFromStorage = (): Message[] => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];

    const data = JSON.parse(stored);
    if (data.version !== STORAGE_VERSION) return [];

    // Parse dates back to Date objects
    const messages = data.messages.map((msg: Message) => ({
      ...msg,
      timestamp: new Date(msg.timestamp),
    }));

    return cleanOldMessages(messages);
  } catch (error) {
    console.error("Failed to load chat history:", error);
    return [];
  }
};

// Save messages to localStorage
const saveToStorage = (messages: Message[]): void => {
  try {
    const data = {
      messages,
      version: STORAGE_VERSION,
      lastUpdated: new Date().toISOString(),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (error) {
    console.error("Failed to save chat history:", error);
  }
};

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      // Initial State
      messages: loadFromStorage(),
      isTyping: false,
      currentRequestId: null,
      currentRequests: new Map(),
      error: null,

      // Message Actions
      addMessage: (message: Message) => {
        set((state) => {
          const newMessages = [...state.messages, message];
          saveToStorage(newMessages);
          return { messages: newMessages };
        });
      },

      clearHistory: () => {
        set({ messages: [], currentRequests: new Map() });
        localStorage.removeItem(STORAGE_KEY);
      },

      loadHistory: () => {
        const messages = loadFromStorage();
        set({ messages });
      },

      saveHistory: () => {
        const { messages } = get();
        saveToStorage(messages);
      },

      // Typing Actions
      setTyping: (isTyping: boolean) => {
        set({ isTyping });
      },

      // Request Actions
      setCurrentRequestId: (requestId: string | null) => {
        set({ currentRequestId: requestId });
      },

      updateRequestStatus: (requestId: string, request: RequestInfo) => {
        set((state) => {
          const newRequests = new Map(state.currentRequests);
          newRequests.set(requestId, request);
          return { currentRequests: newRequests };
        });
      },

      getRequest: (requestId: string) => {
        const { currentRequests } = get();
        return currentRequests.get(requestId);
      },

      removeRequest: (requestId: string) => {
        set((state) => {
          const newRequests = new Map(state.currentRequests);
          newRequests.delete(requestId);
          return { currentRequests: newRequests };
        });
      },

      // Error Actions
      setError: (error: string | null) => {
        set({ error });
      },

      // Utility Actions
      getFilteredMessages: (filter) => {
        const { messages } = get();

        if (!filter) return messages;

        return messages.filter((msg) => {
          // Filter by search term
          if (filter.searchTerm) {
            const searchLower = filter.searchTerm.toLowerCase();
            if (!msg.content.toLowerCase().includes(searchLower)) {
              return false;
            }
          }

          // Filter by content type
          if (filter.type && msg.metadata?.classification) {
            if (msg.metadata.classification.type !== filter.type) {
              return false;
            }
          }

          // Filter by request status
          if (filter.status && msg.metadata?.requestStatus) {
            if (msg.metadata.requestStatus !== filter.status) {
              return false;
            }
          }

          return true;
        });
      },
    }),
    {
      name: "chat-storage",
      partialize: (state) => ({
        messages: state.messages,
      }),
    },
  ),
);

// Helper hook to add system message
export const useAddSystemMessage = () => {
  const addMessage = useChatStore((state) => state.addMessage);

  return (content: string) => {
    addMessage({
      id: `system-${Date.now()}`,
      type: "system",
      content,
      timestamp: new Date(),
    });
  };
};

// Helper hook to add user message
export const useAddUserMessage = () => {
  const addMessage = useChatStore((state) => state.addMessage);

  return (content: string, metadata?: Message["metadata"]) => {
    addMessage({
      id: `user-${Date.now()}`,
      type: "user",
      content,
      timestamp: new Date(),
      metadata,
    });
  };
};

// Helper hook to add assistant message
export const useAddAssistantMessage = () => {
  const addMessage = useChatStore((state) => state.addMessage);

  return (content: string, metadata?: Message["metadata"]) => {
    addMessage({
      id: `assistant-${Date.now()}`,
      type: "assistant",
      content,
      timestamp: new Date(),
      metadata,
    });
  };
};
