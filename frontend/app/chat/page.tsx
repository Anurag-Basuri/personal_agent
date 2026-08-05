'use client';

import { useEffect, useRef } from 'react';
import { useSession } from 'next-auth/react';
import { Sidebar } from '../../components/layout/Sidebar';
import { Header } from '../../components/layout/Header';
import { ChatArea } from '../../components/chat/ChatArea';
import { Composer } from '../../components/chat/Composer';
import { useAgentAPI } from '../../hooks/useAgentAPI';

export default function ChatInterface() {
  const { data: session, status } = useSession();
  const { getHistory } = useAgentAPI();
  const hasLoadedHistory = useRef(false);

  useEffect(() => {
    if (status !== 'authenticated') return;
    const apiToken = (session as any)?.apiToken;
    if (!apiToken) return;
    if (hasLoadedHistory.current) return;
    hasLoadedHistory.current = true;
    getHistory();
  }, [status, session, getHistory]);

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

