'use client';

import { useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAgentStore } from '@/store/useAgentStore';
import { useAgentAPI } from '@/hooks/useAgentAPI';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { ChatArea } from '@/components/chat/ChatArea';
import { Composer } from '@/components/chat/Composer';

export default function AdminChatPage() {
  const { isAdmin, adminToken } = useAgentStore();
  const router = useRouter();
  const { getHistory } = useAgentAPI();
  const hasLoadedHistory = useRef(false);

  useEffect(() => {
    if (!isAdmin || !adminToken) {
      router.push('/admin/login');
      return;
    }

    if (hasLoadedHistory.current) return;
    hasLoadedHistory.current = true;
    getHistory();
  }, [isAdmin, adminToken, router, getHistory]);

  if (!isAdmin || !adminToken) return null;

  return (
    <div className="flex h-screen bg-background overflow-hidden selection:bg-primary/30">
      <Sidebar />
      <div className="flex flex-1 flex-col w-full min-w-0">
        <Header />
        <ChatArea />
        <Composer />
      </div>
    </div>
  );
}
