import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '../stores/chatStore';
import { chatService } from '../services/chat';
import { websocketService } from '../services/websocket';
import { ChatMessage } from '../components/Chat/ChatMessage';
import { TypingIndicator } from '../components/Chat/TypingIndicator';
import { RequestStatus } from '../components/Chat/RequestStatus';
import { Send, Trash2, Search as SearchIcon, Wifi, WifiOff, Sparkles } from 'lucide-react';
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

  // Quick action suggestions
  const suggestions = [
    'Download the latest episode of...',
    'What movies are coming out this week?',
    'Show me my download queue',
    'Check the status of my servers',
  ];

  return (
    <div
      data-testid="chat-container"
      className="flex flex-col h-full min-h-0 bg-gradient-to-b from-background to-[hsl(280,50%,15%)]"
    >
      {/* Header */}
      <div className="flex-shrink-0 border-b border-primary/20 bg-card/50 backdrop-blur-md px-4 py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/20 border border-primary/30 shadow-[0_0_15px_rgba(168,85,247,0.3)]">
              <Sparkles className="w-5 h-5 text-primary drop-shadow-[0_0_8px_rgba(168,85,247,0.5)]" />
            </div>
            <h1 className="text-lg font-bold bg-gradient-to-r from-primary via-accent to-[hsl(290,90%,70%)] bg-clip-text text-transparent">
              AutoArr Assistant
            </h1>
          </div>

          <div className="flex items-center gap-2">
            {/* Connection Status */}
            <div
              data-testid="connection-status"
              className="flex items-center gap-1.5 px-2 py-1 glass-card"
              aria-label={`Connection status: ${connectionStatus}`}
            >
              {connectionStatus === 'connected' ? (
                <>
                  <Wifi className="w-3.5 h-3.5 text-status-success" />
                  <span className="text-xs text-status-success font-medium">Connected</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-3.5 h-3.5 text-status-warning" />
                  <span className="text-xs text-status-warning font-medium">
                    {connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
                  </span>
                </>
              )}
            </div>

            {/* Search Button */}
            <button
              onClick={() => setShowSearch(!showSearch)}
              className="p-1.5 hover:bg-muted rounded-lg transition-all duration-300 hover:shadow-glow-hover"
              aria-label="Search messages"
            >
              <SearchIcon className="w-4 h-4 text-muted-foreground hover:text-foreground" />
            </button>

            {/* Clear History Button */}
            <button
              onClick={handleClearHistory}
              className="p-1.5 hover:bg-muted rounded-lg transition-all duration-300 hover:shadow-glow-hover"
              aria-label="Clear history"
            >
              <Trash2 className="w-4 h-4 text-muted-foreground hover:text-foreground" />
            </button>
          </div>
        </div>

        {/* Search Component */}
        {showSearch && (
          <div className="mt-2">
            <ChatSearch onClose={() => setShowSearch(false)} />
          </div>
        )}
      </div>

      {/* Active Requests */}
      {activeRequests.length > 0 && (
        <div className="flex-shrink-0 border-b border-border bg-card/30 backdrop-blur-sm px-6 py-4 space-y-3">
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
        className="flex-1 overflow-y-auto px-4 py-4 min-h-0"
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            {/* Welcome Icon with Pulsing Glow */}
            <div className="relative mb-6">
              <div className="absolute inset-[-50%] animate-pulse rounded-full bg-primary/30 blur-2xl" />
              <div className="relative p-5 rounded-xl bg-card/50 border border-primary/30 backdrop-blur-sm shadow-[0_0_40px_rgba(168,85,247,0.4)]">
                <Sparkles className="w-10 h-10 text-primary drop-shadow-[0_0_20px_rgba(168,85,247,0.6)]" />
              </div>
            </div>

            <h2 className="mb-2 bg-gradient-to-r from-primary via-accent to-[hsl(290,90%,70%)] bg-clip-text text-2xl font-bold text-transparent">
              Welcome to AutoArr
            </h2>
            <p className="text-sm text-muted-foreground max-w-xl mb-6">
              Ask me to download content, check status, or manage your library.
            </p>

            {/* Quick Suggestions */}
            <div className="grid grid-cols-2 gap-3 max-w-2xl w-full">
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setInput(suggestion);
                    inputRef.current?.focus();
                  }}
                  className="rounded-lg border border-primary/20 bg-card/50 px-4 py-2.5 backdrop-blur-sm text-left text-sm text-muted-foreground hover:text-foreground transition-all duration-300 hover:scale-[1.02] hover:shadow-[0_0_20px_rgba(168,85,247,0.3)] hover:border-primary/40"
                >
                  {suggestion}
                </button>
              ))}
            </div>
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
      <div className="flex-shrink-0 border-t border-border bg-card/50 backdrop-blur-md px-4 py-3">
        <div className="flex gap-2 items-end">
          <div className="flex-1 glass-card p-0.5">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isProcessing}
              placeholder="Ask AutoArr to help..."
              className="w-full bg-transparent text-foreground placeholder-muted-foreground px-3 py-2 rounded-lg resize-none focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed textarea-auto-size text-sm"
              rows={1}
              aria-label="Message input"
              role="textbox"
              aria-multiline="true"
            />
          </div>
          <button
            onClick={handleSend}
            disabled={!input.trim() || isProcessing}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5 justify-center shadow-glow hover:shadow-glow-lg"
            aria-label="Send message"
          >
            {isProcessing ? (
              <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span className="font-medium text-sm">Send</span>
              </>
            )}
          </button>
        </div>

        {error && (
          <div
            className="mt-2 text-xs text-destructive bg-destructive/10 border border-destructive/20 px-3 py-2 rounded-lg"
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
