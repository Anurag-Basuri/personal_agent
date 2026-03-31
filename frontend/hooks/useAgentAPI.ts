'use client';

import { useCallback } from 'react';
import { useAgentStore, ChatMessage, AgentSession } from '../store/useAgentStore';

const API_BASE = 'http://localhost:4000';

export function useAgentAPI() {
	const { sessionId, addMessage, setTyping, setSessionsLoading, setSessions } = useAgentStore();

	const sendMessage = useCallback(
		async (content: string) => {
			// 1. Add user message to UI immediately
			const userMsg: ChatMessage = {
				id: crypto.randomUUID(),
				role: 'user',
				content,
				timestamp: new Date().toISOString(),
			};
			addMessage(userMsg);
			setTyping(true);

			try {
				const res = await fetch(`${API_BASE}/chat`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					credentials: 'include',
					body: JSON.stringify({
						message: content,
						sessionId,
						currentUrl: window.location.href,
					}),
				});

				const data = await res.json();

				if (!data.success) {
					throw new Error(data.message || 'API Error');
				}

				// 2. Add assistant response to UI
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
		[sessionId, addMessage, setTyping],
	);

	const fetchSessions = useCallback(
		async (page = 1) => {
			setSessionsLoading(true);
			try {
				const res = await fetch(`${API_BASE}/admin/agent-sessions?page=${page}&limit=50`, {
					credentials: 'include'
				});
				const data = await res.json();
				if (data.success && data.data.items) {
					setSessions(data.data.items);
				}
			} catch (err) {
				console.error('Failed to fetch sessions:', err);
			} finally {
				setSessionsLoading(false);
			}
		},
		[setSessions, setSessionsLoading],
	);

	const resetSession = useCallback(async () => {
		try {
			await fetch(`${API_BASE}/chat/reset`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include',
				body: JSON.stringify({ sessionId }),
			});
		} catch (err) {
			console.error('Failed to reset session on server:', err);
		}
	}, [sessionId]);

	return { sendMessage, fetchSessions, resetSession };
}
