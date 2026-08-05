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

interface AgentState {
	// Admin State
	isAdmin: boolean;
	adminToken: string | null;

	// Current Session State
	messages: ChatMessage[];
	isTyping: string | boolean;
	isHistoryLoading: boolean;

	// UI State
	isSidebarOpen: boolean;

	// Actions
	addMessage: (msg: ChatMessage) => void;
	setMessages: (msgs: ChatMessage[]) => void;
	setTyping: (typing: string | boolean) => void;
	setSidebarOpen: (open: boolean) => void;
	setHistoryLoading: (loading: boolean) => void;
	resetChat: () => void;
	setAdminState: (isAdmin: boolean, token?: string | null) => void;
}

export const useAgentStore = create<AgentState>(set => ({
	isAdmin: false,
	adminToken: typeof window !== 'undefined' ? localStorage.getItem('adminToken') : null,
	messages: [],
	isTyping: false,
	isHistoryLoading: false,
	isSidebarOpen: false,
	addMessage: msg => set(state => ({ messages: [...state.messages, msg] })),
	setMessages: msgs => set({ messages: msgs }),
	setTyping: typing => set({ isTyping: typing }),
	setSidebarOpen: open => set({ isSidebarOpen: open }),
	setHistoryLoading: loading => set({ isHistoryLoading: loading }),
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

