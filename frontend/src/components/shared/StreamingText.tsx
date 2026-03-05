'use client';

import { useEffect, useState } from 'react';

interface StreamingTextProps {
  /** The full text content to display */
  text: string;
  /** Whether the text is still being streamed */
  isStreaming?: boolean;
  /** Optional CSS class name */
  className?: string;
}

/**
 * StreamingText renders text with an optional blinking cursor to indicate
 * that content is still being streamed from the server.
 */
export default function StreamingText({
  text,
  isStreaming = false,
  className = '',
}: StreamingTextProps) {
  const [showCursor, setShowCursor] = useState(true);

  // Blink the cursor while streaming
  useEffect(() => {
    if (!isStreaming) {
      setShowCursor(false);
      return;
    }

    const interval = setInterval(() => {
      setShowCursor((prev) => !prev);
    }, 500);

    return () => clearInterval(interval);
  }, [isStreaming]);

  return (
    <span className={className}>
      {text}
      {isStreaming && (
        <span
          className={`inline-block w-[2px] h-[1em] bg-current align-text-bottom ml-0.5 ${
            showCursor ? 'opacity-100' : 'opacity-0'
          }`}
        />
      )}
    </span>
  );
}
