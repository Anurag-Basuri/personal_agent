'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useSession, signOut } from 'next-auth/react';
import { useAgentStore, ChatMessage } from '../store/useAgentStore';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

function stripNavigateTags(text: string): string {
  return (text || '').replace(/\[NAVIGATE:.*?\]/g, '').trim();
}

export function useAgentAPI() {
  const router = useRouter();
  const { addMessage, setMessages, setTyping, setHistoryLoading, resetChat, isAdmin, adminToken } = useAgentStore();
  const { data: session, update: updateSession } = useSession();

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
      setTyping('Processing...');

      try {
        if (!hasValidToken()) {
          throw new Error('Session expired. Please log in again.');
        }

        const endpoint = isAdmin ? `${API_BASE}/api/admin/chat/` : `${API_BASE}/api/agent/chat/`;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000);

        try {
          let res = await fetch(endpoint, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
              message: content,
              currentUrl: window.location.href,
            }),
            signal: controller.signal,
          });

          if (res.status === 401) {
            const retried = await handleAuthError(res);
            if (retried) {
              res = await fetch(endpoint, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                  message: content,
                  currentUrl: window.location.href,
                }),
                signal: controller.signal,
              });
            } else {
              throw new Error('Session expired. Please log in again.');
            }
          }

        const text = await res.text();
        let data;
        try {
          data = JSON.parse(text);
        } catch (e) {
          throw new Error(`Server returned invalid response (Status ${res.status}): ${text.slice(0, 50)}...`);
        }

        if (!res.ok || !data.success) {
          throw new Error(data.message || 'API Error');
        }

        const replyText = data.data.reply || '';

        // Handle auto-navigation if the agent includes [NAVIGATE:/path]
        const navigateMatch = replyText.match(/\[NAVIGATE:(.*?)\]/);
        if (navigateMatch && navigateMatch[1]) {
          const path = navigateMatch[1].trim();
          if (path.startsWith('/')) {
            // Push route
            router.push(path);
          }
        }

        const agentMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: stripNavigateTags(replyText),
          timestamp: new Date().toISOString(),
        };
        addMessage(agentMsg);
        } finally {
          clearTimeout(timeoutId);
        }
      } catch (error: any) {
        const message = error.name === 'AbortError'
          ? 'Request timed out. The server took too long to respond. Please try again.'
          : (error.message || 'Failed to connect to agent backend.');
        const errorMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'system',
          content: `Error: ${message}`,
          timestamp: new Date().toISOString(),
        };
        addMessage(errorMsg);
      } finally {
        setTyping(false);
      }
    },
    [addMessage, setTyping, getAuthHeaders, isAdmin, hasValidToken, handleAuthError],
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
            // Hide internal tool result messages (not user-facing)
            if (msg.role === 'tool') return false;
            // Hide AI messages with no content (tool-calling intermediates)
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
