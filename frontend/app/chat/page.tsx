'use client';

import { useEffect, useRef } from 'react';
import { Sidebar } from '../../components/layout/Sidebar';
import { Header } from '../../components/layout/Header';
import { ChatArea } from '../../components/chat/ChatArea';
import { Composer } from '../../components/chat/Composer';
import { useAgentStore } from '../../store/useAgentStore';
import { useAgentAPI } from '../../hooks/useAgentAPI';

export default function ChatInterface() {
  const { setSessionId, sessionId } = useAgentStore();
  const { getHistory } = useAgentAPI();
  const hasInitialized = useRef(false);

  useEffect(() => {
    if (!sessionId) {
      setSessionId(crypto.randomUUID());
    }
  }, [sessionId, setSessionId]);

  useEffect(() => {
    if (hasInitialized.current) return;
    hasInitialized.current = true;
    getHistory();
  }, [getHistory]);

  return (
    <main className="flex h-screen w-full overflow-hidden bg-background text-foreground selection:bg-primary/20">
      <Sidebar />
      <div className="flex h-full min-w-0 flex-1 flex-col bg-background">
        <Header />
        <ChatArea />
        <Composer />
      </div>
    </main>
  );
}

