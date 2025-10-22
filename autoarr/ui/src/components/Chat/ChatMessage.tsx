import { Message } from "../../types/chat";
import { formatDistanceToNow } from "../../utils/date";
import { User, Bot, Info } from "lucide-react";
import { ContentCard } from "./ContentCard";

interface ChatMessageProps {
  message: Message;
  onConfirm?: (tmdbId: number) => void;
  onNoneOfThese?: () => void;
}

export const ChatMessage = ({
  message,
  onConfirm,
  onNoneOfThese,
}: ChatMessageProps) => {
  const isUser = message.type === "user";
  const isAssistant = message.type === "assistant";
  const isSystem = message.type === "system";

  if (isSystem) {
    return (
      <div data-testid="system-message" className="flex justify-center my-4">
        <div className="flex items-center gap-2 px-4 py-2 bg-background-tertiary rounded-full text-text-muted text-sm">
          <Info className="w-4 h-4" />
          <span>{message.content}</span>
        </div>
      </div>
    );
  }

  return (
    <div
      data-testid={`${message.type}-message`}
      className={`flex mb-4 ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`flex gap-3 max-w-[85%] ${
          isUser ? "flex-row-reverse" : "flex-row"
        }`}
      >
        {/* Avatar */}
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
            isUser ? "bg-gradient-primary" : "bg-background-tertiary"
          }`}
        >
          {isUser ? (
            <User className="w-4 h-4 text-white" />
          ) : (
            <Bot className="w-4 h-4 text-text-secondary" />
          )}
        </div>

        {/* Message Content */}
        <div
          className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}
        >
          <div
            className={`px-4 py-3 rounded-lg ${
              isUser
                ? "bg-gradient-primary text-white"
                : "bg-background-secondary text-text-primary"
            }`}
          >
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          </div>

          {/* Timestamp */}
          <span
            data-testid="message-timestamp"
            className="text-xs text-text-muted mt-1 px-1"
          >
            {formatDistanceToNow(message.timestamp.toISOString())}
          </span>

          {/* Content Cards for search results */}
          {isAssistant &&
            message.metadata?.searchResults &&
            message.metadata.searchResults.length > 0 && (
              <div className="mt-4 space-y-3 w-full">
                {message.metadata.searchResults.map((result) => (
                  <ContentCard
                    key={result.tmdbId}
                    content={result}
                    onAdd={onConfirm}
                  />
                ))}

                {/* None of these button */}
                {onNoneOfThese && (
                  <button
                    onClick={onNoneOfThese}
                    className="w-full px-4 py-2 bg-background-tertiary text-text-secondary rounded-lg hover:bg-background-hover transition-colors"
                    aria-label="None of these matches"
                  >
                    None of these
                  </button>
                )}
              </div>
            )}
        </div>
      </div>
    </div>
  );
};
