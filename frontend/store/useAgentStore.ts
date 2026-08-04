'use client';

import { create } from 'zustand';

export type Role = 'user' | 'assistant' | 'system' | 'tool';

export interface ToolCall {
	id: string;
	name: string;
	args: any;
	result?: string;
	state: 'pending' | 'success' | 'error';
}

export interface ChatMessage {
	id: string;
	role: Role;
	content: string;
	toolCalls?: ToolCall[];
	timestamp: string;
}

export interface AgentSession {
	id: string;
	sessionId: string;
	createdAt: string;
	updatedAt: string;
}

interface AgentState {
	// Admin State
	isAdmin: boolean;
	adminToken: string | null;

	// Current Session State
	sessionId: string;
	messages: ChatMessage[];
	isTyping: string | boolean;

	// UI State
	isSidebarOpen: boolean;
	sessions: AgentSession[];
	isSessionsLoading: boolean;

	// Actions
	setSessionId: (id: string) => void;
	addMessage: (msg: ChatMessage) => void;
	setTyping: (typing: string | boolean) => void;
	setSidebarOpen: (open: boolean) => void;
	setSessions: (sessions: AgentSession[]) => void;
	setSessionsLoading: (loading: boolean) => void;
	resetChat: () => void;
	setAdminState: (isAdmin: boolean, token?: string | null) => void;
}

export const useAgentStore = create<AgentState>(set => ({
	isAdmin: false,
	adminToken: typeof window !== 'undefined' ? localStorage.getItem('adminToken') : null,
	sessionId: '',
	messages: [],
	isTyping: false,
	isSidebarOpen: false,
	sessions: [],
	isSessionsLoading: false,

	setSessionId: id => set({ sessionId: id }),
	addMessage: msg => set(state => ({ messages: [...state.messages, msg] })),
	setTyping: typing => set({ isTyping: typing }),
	setSidebarOpen: open => set({ isSidebarOpen: open }),
	setSessions: sessions => set({ sessions }),
	setSessionsLoading: loading => set({ isSessionsLoading: loading }),
	resetChat: () => set({ messages: [], isTyping: false }),
	setAdminState: (isAdmin, token) => {
		if (token) {
			localStorage.setItem('adminToken', token);
		} else if (isAdmin === false) {
			localStorage.removeItem('adminToken');
		}
		set({ isAdmin, adminToken: token ?? null });
	},
}));
