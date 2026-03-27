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
	// Current Session State
	sessionId: string;
	messages: ChatMessage[];
	isTyping: boolean;

	// UI State
	isSidebarOpen: boolean;
	sessions: AgentSession[];
	sessionsLoading: boolean;

	// Actions
	setSessionId: (id: string) => void;
	addMessage: (msg: ChatMessage) => void;
	setTyping: (typing: boolean) => void;
	setSidebarOpen: (open: boolean) => void;
	setSessions: (sessions: AgentSession[]) => void;
	setSessionsLoading: (loading: boolean) => void;
	resetChat: () => void;
}

export const useAgentStore = create<AgentState>(set => ({
	sessionId: '',
	messages: [],
	isTyping: false,
	isSidebarOpen: false,
	sessions: [],
	sessionsLoading: false,

	setSessionId: id => set({ sessionId: id }),
	addMessage: msg => set(state => ({ messages: [...state.messages, msg] })),
	setTyping: typing => set({ isTyping: typing }),
	setSidebarOpen: open => set({ isSidebarOpen: open }),
	setSessions: sessions => set({ sessions }),
	setSessionsLoading: loading => set({ sessionsLoading: loading }),
	resetChat: () => set({ messages: [], isTyping: false }),
}));
