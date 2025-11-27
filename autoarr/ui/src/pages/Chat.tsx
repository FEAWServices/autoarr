import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '../stores/chatStore';
import { chatService } from '../services/chat';
import { websocketService } from '../services/websocket';
import { ChatMessage } from '../components/Chat/ChatMessage';
import { TypingIndicator } from '../components/Chat/TypingIndicator';
import { RequestStatus } from '../components/Chat/RequestStatus';
import { MessageCircle, Send, Trash2, Search as SearchIcon, Wifi, WifiOff } from 'lucide-react';
import { ChatSearch } from '../components/Chat/ChatSearch';

export const Chat = () => {
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(websocketService.getState());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const {
    messages,
    isTyping,
    currentRequestId,
    currentRequests,
    error,
    addMessage,
    setTyping,
    setCurrentRequestId,
    updateRequestStatus,
    clearHistory,
    setError,
  } = useChatStore();

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // WebSocket connection monitoring
  useEffect(() => {
    const handleStateChange = (state: typeof connectionStatus) => {
      setConnectionStatus(state);
    };

    websocketService.onStateChange(handleStateChange);

    // Handle WebSocket events
    const handleWebSocketEvent = (event: {
      type: string;
      requestId: string;
      data: {
        status?: string;
        progress?: number;
        eta?: string;
        title?: string;
        error?: string;
      };
      timestamp: string;
    }) => {
      const { requestId, data } = event;

      // Update request status
      if (data.status) {
        const existingRequest = currentRequests.get(requestId);
        if (existingRequest) {
          updateRequestStatus(requestId, {
            ...existingRequest,
            status: data.status as never,
            progress: data.progress,
            eta: data.eta,
            error: data.error,
            updatedAt: event.timestamp,
          });
        }
      }

      // Add system message for important status changes
      if (event.type === 'request-completed' && data.title) {
        addMessage({
          id: `system-${Date.now()}`,
          type: 'system',
          content: `✓ Download completed: ${data.title}`,
          timestamp: new Date(event.timestamp),
        });
      } else if (event.type === 'request-failed' && data.title) {
        addMessage({
          id: `system-${Date.now()}`,
          type: 'system',
          content: `✗ Download failed: ${data.title}`,
          timestamp: new Date(event.timestamp),
        });
      }
    };

    websocketService.on('all', handleWebSocketEvent);

    return () => {
      websocketService.off('all', handleWebSocketEvent);
    };
  }, [currentRequests, updateRequestStatus, addMessage]);

  // Handle message sending
  const handleSend = async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput || isProcessing) return;

    setIsProcessing(true);
    setError(null);

    // Add user message
    addMessage({
      id: `user-${Date.now()}`,
      type: 'user',
      content: trimmedInput,
      timestamp: new Date(),
    });

    // Clear input
    setInput('');

    // Show typing indicator
    setTyping(true);

    try {
      // Send to API
      const response = await chatService.sendMessage(trimmedInput);

      setTyping(false);

      // Set current request ID
      setCurrentRequestId(response.requestId);

      // Add assistant response
      addMessage({
        id: `assistant-${Date.now()}`,
        type: 'assistant',
        content: response.message,
        timestamp: new Date(),
        metadata: {
          classification: response.classification,
          searchResults: response.searchResults,
          requestId: response.requestId,
        },
      });

      // If requires confirmation, initialize request tracking
      if (response.requiresConfirmation && response.classification) {
        updateRequestStatus(response.requestId, {
          requestId: response.requestId,
          status: 'pending_confirmation',
          title: response.classification.title,
          type: response.classification.type,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        });
      }
    } catch (err) {
      setTyping(false);
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);

      // Add error message
      addMessage({
        id: `assistant-${Date.now()}`,
        type: 'assistant',
        content: `Sorry, I encountered an error: ${errorMessage}`,
        timestamp: new Date(),
        metadata: {
          error: errorMessage,
        },
      });
    } finally {
      setIsProcessing(false);
      // Return focus to input
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  // Handle content confirmation
  const handleConfirm = async (tmdbId: number) => {
    if (!currentRequestId) return;

    setIsProcessing(true);

    try {
      const response = await chatService.confirmSelection(currentRequestId, tmdbId);

      // Add confirmation message
      addMessage({
        id: `assistant-${Date.now()}`,
        type: 'assistant',
        content: response.message,
        timestamp: new Date(),
        metadata: {
          requestId: response.requestId,
          requestStatus: response.status,
        },
      });

      // Update request status
      const existingRequest = currentRequests.get(currentRequestId);
      if (existingRequest) {
        updateRequestStatus(currentRequestId, {
          ...existingRequest,
          status: response.status,
          tmdbId,
          updatedAt: new Date().toISOString(),
        });
      }

      // Clear current request ID
      setCurrentRequestId(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to add content';

      addMessage({
        id: `assistant-${Date.now()}`,
        type: 'assistant',
        content: `Sorry, I couldn't add that: ${errorMessage}`,
        timestamp: new Date(),
        metadata: {
          error: errorMessage,
        },
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle "None of these"
  const handleNoneOfThese = () => {
    addMessage({
      id: `user-${Date.now()}`,
      type: 'user',
      content: "None of these match what I'm looking for",
      timestamp: new Date(),
    });

    addMessage({
      id: `assistant-${Date.now()}`,
      type: 'assistant',
      content:
        'I understand. Can you provide more details like the year, actors, or a more specific title?',
      timestamp: new Date(),
    });

    setCurrentRequestId(null);
  };

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Handle clear history
  const handleClearHistory = () => {
    if (window.confirm('Are you sure you want to clear all chat history? This cannot be undone.')) {
      clearHistory();
    }
  };

  const activeRequests = Array.from(currentRequests.values()).filter(
    (req) => req.status === 'downloading' || req.status === 'searching'
  );

  return (
    <div data-testid="chat-container" className="flex flex-col h-full bg-background-primary">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-background-tertiary bg-background-secondary px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <MessageCircle className="w-6 h-6 text-primary-default" />
            <div>
              <h1 className="text-2xl font-bold text-white">Chat</h1>
              <p className="text-sm text-text-muted">
                Ask me to add movies or TV shows to your library
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Connection Status */}
            <div
              data-testid="connection-status"
              className="flex items-center gap-2 px-3 py-1.5 bg-background-tertiary rounded-full"
              aria-label={`Connection status: ${connectionStatus}`}
            >
              {connectionStatus === 'connected' ? (
                <>
                  <Wifi className="w-4 h-4 text-status-success" />
                  <span className="text-xs text-status-success">Connected</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-4 h-4 text-status-warning" />
                  <span className="text-xs text-status-warning">
                    {connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
                  </span>
                </>
              )}
            </div>

            {/* Search Button */}
            <button
              onClick={() => setShowSearch(!showSearch)}
              className="p-2 hover:bg-background-tertiary rounded-lg transition-colors"
              aria-label="Search messages"
            >
              <SearchIcon className="w-5 h-5 text-text-secondary" />
            </button>

            {/* Clear History Button */}
            <button
              onClick={handleClearHistory}
              className="p-2 hover:bg-background-tertiary rounded-lg transition-colors"
              aria-label="Clear history"
            >
              <Trash2 className="w-5 h-5 text-text-secondary" />
            </button>
          </div>
        </div>

        {/* Search Component */}
        {showSearch && (
          <div className="mt-4">
            <ChatSearch onClose={() => setShowSearch(false)} />
          </div>
        )}
      </div>

      {/* Active Requests */}
      {activeRequests.length > 0 && (
        <div className="flex-shrink-0 border-b border-background-tertiary bg-background-secondary px-6 py-4 space-y-3">
          {activeRequests.map((request) => (
            <RequestStatus
              key={request.requestId}
              request={request}
              onCancel={() => {
                chatService.cancelRequest(request.requestId);
              }}
            />
          ))}
        </div>
      )}

      {/* Messages Area */}
      <div
        data-testid="messages-list"
        className="flex-1 overflow-y-auto px-6 py-6"
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <MessageCircle className="w-16 h-16 text-text-muted mb-4" />
            <h2 className="text-xl font-semibold text-text-primary mb-2">Start a Conversation</h2>
            <p className="text-text-secondary max-w-md">
              Ask me to add movies or TV shows to your library. For example: "Add Inception" or "I
              want to watch Breaking Bad"
            </p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                onConfirm={handleConfirm}
                onNoneOfThese={handleNoneOfThese}
              />
            ))}
            {isTyping && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 border-t border-background-tertiary bg-background-secondary px-6 py-4">
        <div className="flex gap-3 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isProcessing}
            placeholder="Request a movie or show..."
            className="flex-1 bg-background-tertiary text-text-primary placeholder-text-muted px-4 py-3 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-default disabled:opacity-50 disabled:cursor-not-allowed textarea-auto-size"
            rows={1}
            aria-label="Message input"
            role="textbox"
            aria-multiline="true"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isProcessing}
            className="px-6 py-3 bg-gradient-primary text-white rounded-lg hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 min-w-[100px] justify-center"
            aria-label="Send message"
          >
            {isProcessing ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <Send className="w-5 h-5" />
                <span>Send</span>
              </>
            )}
          </button>
        </div>

        {error && (
          <div
            className="mt-3 text-sm text-status-error bg-red-500/10 px-4 py-2 rounded"
            role="alert"
            aria-live="assertive"
          >
            {error}
          </div>
        )}
      </div>
    </div>
  );
};
