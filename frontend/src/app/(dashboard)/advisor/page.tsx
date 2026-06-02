'use client';

import { Suspense, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import ChatPanel from '@/components/advisor/ChatPanel';
import MainPanel from '@/components/advisor/MainPanel';
import { fetchConsultingProfile } from '@/lib/consultingProfile';
import { useBlueprintWorkspaceStore } from '@/stores/blueprintWorkspaceStore';
import { useChatStore } from '@/stores/chatStore';
import { usePanelStore } from '@/stores/panelStore';

const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

function AdvisorContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session');
  const focusMode = useBlueprintWorkspaceStore((s) => s.focusMode);
  const currentPanel = usePanelStore((s) => s.currentPanel);
  const isBlueprint =
    currentPanel === 'interactive_architecture' || currentPanel === 'architecture_diagram';
  const blueprintFocus = focusMode && isBlueprint;

  useEffect(() => {
    fetchConsultingProfile().then((profile) => {
      if (profile) {
        useChatStore.setState({ consultingProfile: profile });
      }
    });
  }, []);

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
    <div className="flex h-full min-h-0 w-full flex-1">
      <div
        className={`flex h-full min-h-0 shrink-0 flex-col overflow-hidden transition-[width] duration-300 ease-out ${
          blueprintFocus ? 'w-0 max-w-0 opacity-0' : 'w-[30%] min-w-[280px] max-w-[420px] opacity-100'
        }`}
        aria-hidden={blueprintFocus}
      >
        <ChatPanel />
      </div>
      <div
        className={`flex h-full min-h-0 min-w-0 flex-1 flex-col transition-[width] duration-300 ease-out ${
          blueprintFocus ? 'w-full' : ''
        }`}
      >
        <MainPanel />
      </div>
    </div>
  );
}

export default function AdvisorPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-full min-h-0 flex-1 items-center justify-center text-gray-400">
          Loading...
        </div>
      }
    >
      <div className="flex h-full min-h-0 flex-1">
        <AdvisorContent />
      </div>
    </Suspense>
  );
}
