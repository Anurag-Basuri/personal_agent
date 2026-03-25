import { useState, useRef, useEffect, useCallback } from 'react';
import { apiClient } from '@/api';
import { AgentMessage, AgentApiResponse } from '../types/agent.types';

export function useAgentSession() {
	const [messages, setMessages] = useState<AgentMessage[]>([]);
	const [isLoading, setIsLoading] = useState(false);
	const [isOpen, setIsOpen] = useState(false);

	// Persistent Session ID Memory across reloads
	const sessionIdRef = useRef<string>('');

	useEffect(() => {
		if (typeof window !== 'undefined') {
			let sid = localStorage.getItem('agent_session_id');
			if (!sid) {
				sid = Math.random().toString(36).substring(2, 15);
				localStorage.setItem('agent_session_id', sid);
			}
			sessionIdRef.current = sid;
		}
	}, []);

	// Send message to the LangChain backend
	const sendMessage = useCallback(
		async (content: string) => {
			if (!content.trim() || isLoading) return;

			const userMsg: AgentMessage = {
				id: Date.now().toString(),
				role: 'user',
				content,
			};

			// Optimistic UI update
			setMessages(prev => [...prev, userMsg]);
			setIsLoading(true);

			try {
				const resData = await apiClient.post<AgentApiResponse>('/chat', {
					message: content,
					sessionId: sessionIdRef.current,
				});

				const assistantMsg: AgentMessage = {
					id: (Date.now() + 1).toString(),
					role: 'assistant',
					content: resData.reply,
				};

				setMessages(prev => [...prev, assistantMsg]);
			} catch (error: any) {
				console.error('[useAgentSession] Error:', error);
				const errMsg: AgentMessage = {
					id: (Date.now() + 1).toString(),
					role: 'assistant',
					content:
						error?.response?.data?.error?.message ||
						'Sorry, I am having trouble connecting right now. Please try again later.',
				};
				setMessages(prev => [...prev, errMsg]);
			} finally {
				setIsLoading(false);
			}
		},
		[isLoading],
	);

	const clearSession = useCallback(async () => {
		setMessages([]);
		if (sessionIdRef.current) {
			try {
				await apiClient.post('/chat/reset', { sessionId: sessionIdRef.current });
				// Generate new session ID locally too
				const newSid = Math.random().toString(36).substring(2, 15);
				localStorage.setItem('agent_session_id', newSid);
				sessionIdRef.current = newSid;
			} catch (e) {
				console.error('[useAgentSession] Failed to reset memory:', e);
			}
		}
	}, []);

	return {
		messages,
		isLoading,
		isOpen,
		setIsOpen,
		sendMessage,
		clearSession,
	};
}
