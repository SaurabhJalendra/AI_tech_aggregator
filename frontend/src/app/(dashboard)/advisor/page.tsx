'use client';

import { Suspense, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import ChatPanel from '@/components/advisor/ChatPanel';
import MainPanel from '@/components/advisor/MainPanel';
import { useChatStore } from '@/stores/chatStore';

const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

function AdvisorContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session');

  useEffect(() => {
    if (!sessionId) return;

    const store = useChatStore.getState();
    store.clearMessages();
    store.setSessionId(sessionId);

    fetch(`${apiBase}/sessions/${sessionId}/messages`, {
      headers: {
        Authorization: 'Bearer dev@example.com',
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to fetch session messages: ${res.status}`);
        return res.json();
      })
      .then((messages: Array<{ role: 'user' | 'assistant'; content: string; panel_commands?: unknown[] }>) => {
        const store = useChatStore.getState();
        for (const msg of messages) {
          if (msg.role === 'user') {
            store.addUserMessage(msg.content);
          } else if (msg.role === 'assistant') {
            const id = store.addAssistantMessage();
            store.appendStreamChunk(id, msg.content);
          }
        }
      })
      .catch((err) => {
        console.error('Failed to load conversation history:', err);
      });
  }, [sessionId]);

  return (
    <>
      <ChatPanel />
      <MainPanel />
    </>
  );
}

export default function AdvisorPage() {
  return (
    <Suspense fallback={<div className="flex h-full items-center justify-center text-gray-400">Loading...</div>}>
      <AdvisorContent />
    </Suspense>
  );
}
