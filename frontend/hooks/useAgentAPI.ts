'use client';

import { useCallback } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { useAgentStore, ChatMessage } from '../store/useAgentStore';
import { useSSEStream } from './useSSEStream';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

function stripNavigateTags(text: string): string {
  return (text || '').replace(/\[NAVIGATE:.*?\]/g, '').trim();
}

export function useAgentAPI() {
  const {
    addMessage,
    setMessages,
    setTyping,
    setHistoryLoading,
    resetChat,
    isAdmin,
    adminToken,
    startStream,
  } = useAgentStore();
  const { data: session, update: updateSession } = useSession();
  const { streamMessage } = useSSEStream();

  const getAuthHeaders = useCallback((): HeadersInit => {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (isAdmin && adminToken) {
      headers['Authorization'] = `Bearer ${adminToken}`;
    } else {
      const apiToken = (session as any)?.apiToken;
      if (apiToken) {
        headers['Authorization'] = `Bearer ${apiToken}`;
      }
    }

    return headers;
  }, [session, isAdmin, adminToken]);

  const hasValidToken = useCallback((): boolean => {
    if (isAdmin && adminToken) return true;
    const apiToken = (session as any)?.apiToken;
    return !!apiToken;
  }, [session, isAdmin, adminToken]);

  const handleAuthError = useCallback(async (res: Response): Promise<boolean> => {
    if (res.status !== 401) return false;

    try {
      const refreshed = await updateSession();
      if (refreshed && (refreshed as any)?.apiToken) {
        return true;
      }
    } catch {
      // Session refresh failed
    }

    await signOut({ redirectTo: '/' });
    return false;
  }, [updateSession]);

  const sendMessage = useCallback(
    async (content: string) => {
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      };
      addMessage(userMsg);

      if (!hasValidToken()) {
        addMessage({
          id: crypto.randomUUID(),
          role: 'system',
          content: 'Error: Session expired. Please log in again.',
          timestamp: new Date().toISOString(),
        });
        return;
      }

      // Create a placeholder assistant message for streaming
      const assistantId = crypto.randomUUID();
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: 'assistant',
        content: '',
        activityLog: [],
        timestamp: new Date().toISOString(),
      };
      addMessage(assistantMsg);

      // Activate streaming state in the store
      startStream(assistantId);

      // Use the stream endpoint
      const endpoint = isAdmin
        ? `${API_BASE}/api/admin/chat/stream`
        : `${API_BASE}/api/agent/chat/stream`;

      await streamMessage(
        endpoint,
        getAuthHeaders(),
        {
          message: content,
          currentUrl: window.location.href,
        },
        assistantId,
      );
    },
    [addMessage, startStream, streamMessage, getAuthHeaders, isAdmin, hasValidToken],
  );

  const getHistory = useCallback(async () => {
    if (!hasValidToken()) return;

    setHistoryLoading(true);
    try {
      const endpoint = isAdmin ? `${API_BASE}/api/admin/chat/history` : `${API_BASE}/api/agent/chat/history`;
      const res = await fetch(endpoint, {
        headers: getAuthHeaders(),
      });

      if (res.status === 401) {
        await handleAuthError(res);
        return;
      }

      const text = await res.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch (e) {
        throw new Error('Failed to parse history response');
      }
      if (res.ok && data.success && data.data.messages) {
        const mapped: ChatMessage[] = data.data.messages
          .filter((msg: any) => {
            if (msg.role === 'tool') return false;
            if (msg.role === 'ai' && (!msg.content || msg.content.trim() === '')) return false;
            return true;
          })
          .map((msg: any) => ({
            id: msg.id,
            role: msg.role === 'human' ? 'user' : 'assistant',
            content: stripNavigateTags(msg.content),
            timestamp: msg.created_at,
          }));
        setMessages(mapped);
      }
    } catch (err) {
      console.error('Failed to fetch history:', err);
    } finally {
      setHistoryLoading(false);
    }
  }, [getAuthHeaders, setMessages, setHistoryLoading, isAdmin, hasValidToken, handleAuthError]);

  const resetSession = useCallback(async () => {
    resetChat();
    try {
      const endpoint = isAdmin ? `${API_BASE}/api/admin/chat/reset` : `${API_BASE}/api/agent/chat/reset`;
      await fetch(endpoint, {
        method: 'POST',
        headers: getAuthHeaders(),
      });
    } catch (err) {
      console.error('Failed to reset session on server:', err);
    }
  }, [getAuthHeaders, resetChat, isAdmin]);

  const deleteAll = useCallback(async () => {
    resetChat();
    try {
      const endpoint = isAdmin ? `${API_BASE}/api/admin/chat/delete-all` : `${API_BASE}/api/agent/chat/delete-all`;
      const res = await fetch(endpoint, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        return true;
      }
      return false;
    } catch (err) {
      console.error('Failed to delete all history:', err);
      return false;
    }
  }, [getAuthHeaders, resetChat, isAdmin]);

  return { sendMessage, getHistory, resetSession, deleteAll };
}
