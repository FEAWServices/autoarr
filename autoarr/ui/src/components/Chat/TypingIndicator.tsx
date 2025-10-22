import { Bot } from "lucide-react";

export const TypingIndicator = () => {
  return (
    <div
      data-testid="typing-indicator"
      className="flex mb-4"
      aria-label="Assistant is typing"
      aria-live="polite"
    >
      <div className="flex gap-3 max-w-[85%]">
        {/* Avatar */}
        <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-background-tertiary">
          <Bot className="w-4 h-4 text-text-secondary" />
        </div>

        {/* Typing Animation */}
        <div className="flex items-center px-4 py-3 bg-background-secondary rounded-lg">
          <div className="flex gap-1.5">
            <div
              className="w-2 h-2 bg-text-muted rounded-full animate-bounce"
              style={{ animationDelay: "0ms", animationDuration: "1.4s" }}
            />
            <div
              className="w-2 h-2 bg-text-muted rounded-full animate-bounce"
              style={{ animationDelay: "200ms", animationDuration: "1.4s" }}
            />
            <div
              className="w-2 h-2 bg-text-muted rounded-full animate-bounce"
              style={{ animationDelay: "400ms", animationDuration: "1.4s" }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
