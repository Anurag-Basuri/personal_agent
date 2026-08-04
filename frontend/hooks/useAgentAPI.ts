'use client';

import { useCallback } from 'react';
import { useSession } from 'next-auth/react';
import { useAgentStore, ChatMessage } from '../store/useAgentStore';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

export function useAgentAPI() {
  const { sessionId, addMessage, setTyping, setSessionsLoading, setSessions, resetChat, isAdmin, adminToken } = useAgentStore();
  const { data: session } = useSession();

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

  const sendMessage = useCallback(
    async (content: string) => {
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      };
      addMessage(userMsg);
      setTyping('Processing...');

      try {
        const endpoint = isAdmin ? `${API_BASE}/api/admin/chat/` : `${API_BASE}/api/agent/chat/`;
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({
            message: content,
            sessionId,
            currentUrl: window.location.href,
          }),
        });

        const data = await res.json();

        if (!res.ok || !data.success) {
          throw new Error(data.message || 'API Error');
        }

        const agentMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.data.reply,
          timestamp: new Date().toISOString(),
        };
        addMessage(agentMsg);
      } catch (error: any) {
        const errorMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'system',
          content: `Error: ${error.message || 'Failed to connect to agent backend.'}`,
          timestamp: new Date().toISOString(),
        };
        addMessage(errorMsg);
      } finally {
        setTyping(false);
      }
    },
    [sessionId, addMessage, setTyping, getAuthHeaders],
  );

  const getHistory = useCallback(async () => {
    setSessionsLoading(true);
    try {
      const endpoint = isAdmin ? `${API_BASE}/api/admin/chat/history` : `${API_BASE}/api/agent/chat/history`;
      const res = await fetch(endpoint, {
        headers: getAuthHeaders(),
      });
      const data = await res.json();
      if (res.ok && data.success && data.data.messages) {
        // Map backend history to UI state
        resetChat();
        data.data.messages.forEach((msg: any) => {
          addMessage({
            id: msg.id,
            role: msg.role === 'ai' || msg.role === 'tool' ? 'assistant' : msg.role,
            content: msg.content,
            timestamp: msg.created_at,
          });
        });
      }
    } catch (err) {
      console.error('Failed to fetch history:', err);
    } finally {
      setSessionsLoading(false);
    }
  }, [getAuthHeaders, addMessage, resetChat, setSessionsLoading]);

  // Keep fetchSessions for compatibility if UI still expects an array of sessions
  // but for the normal agent, there's only 1 continuous conversation.
  const fetchSessions = useCallback(async () => {
    // Normal users have a single session in this architecture
    setSessionsLoading(true);
    try {
      setSessions([
        {
          id: '1',
          sessionId: 'current_conversation',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        }
      ]);
    } finally {
      setSessionsLoading(false);
    }
  }, [setSessions, setSessionsLoading]);

  const resetSession = useCallback(async () => {
    try {
      const endpoint = isAdmin ? `${API_BASE}/api/admin/chat/reset` : `${API_BASE}/api/agent/chat/reset`;
      await fetch(endpoint, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ sessionId }),
      });
      resetChat();
    } catch (err) {
      console.error('Failed to reset session on server:', err);
    }
  }, [sessionId, getAuthHeaders, resetChat, isAdmin]);

  const deleteAll = useCallback(async () => {
    try {
      const endpoint = isAdmin ? `${API_BASE}/api/admin/chat/delete-all` : `${API_BASE}/api/agent/chat/delete-all`;
      const res = await fetch(endpoint, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        resetChat();
        return true;
      }
      return false;
    } catch (err) {
      console.error('Failed to delete all history:', err);
      return false;
    }
  }, [getAuthHeaders, resetChat, isAdmin]);

  return { sendMessage, fetchSessions, getHistory, resetSession, deleteAll };
}
