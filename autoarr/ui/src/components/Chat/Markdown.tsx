import ReactMarkdown from 'react-markdown';
import type { Components } from 'react-markdown';

interface MarkdownProps {
  content: string;
  className?: string;
}

// Custom components for styling markdown elements
const components: Components = {
  // Headings
  h1: ({ children }) => <h1 className="text-xl font-bold mb-3 mt-4 first:mt-0">{children}</h1>,
  h2: ({ children }) => <h2 className="text-lg font-bold mb-2 mt-3 first:mt-0">{children}</h2>,
  h3: ({ children }) => (
    <h3 className="text-base font-semibold mb-2 mt-2 first:mt-0">{children}</h3>
  ),

  // Paragraphs
  p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,

  // Lists
  ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,

  // Inline code
  code: ({ children, className }) => {
    // Check if this is a code block (has language class) vs inline code
    const isCodeBlock = className?.includes('language-');
    if (isCodeBlock) {
      return (
        <code className="block bg-background/50 rounded-md p-3 my-2 text-sm overflow-x-auto font-mono">
          {children}
        </code>
      );
    }
    return (
      <code className="bg-background/50 px-1.5 py-0.5 rounded text-sm font-mono">{children}</code>
    );
  },

  // Code blocks
  pre: ({ children }) => (
    <pre className="bg-background/50 rounded-md p-3 my-2 overflow-x-auto">{children}</pre>
  ),

  // Links
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-primary hover:text-primary/80 underline underline-offset-2 transition-colors"
    >
      {children}
    </a>
  ),

  // Strong/Bold
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,

  // Emphasis/Italic
  em: ({ children }) => <em className="italic">{children}</em>,

  // Blockquotes
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-primary/50 pl-3 my-2 text-muted-foreground italic">
      {children}
    </blockquote>
  ),

  // Horizontal rule
  hr: () => <hr className="border-border my-4" />,
};

export const Markdown = ({ content, className = '' }: MarkdownProps) => {
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown components={components}>{content}</ReactMarkdown>
    </div>
  );
};
