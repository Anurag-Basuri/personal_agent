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

export interface ActivityLogEntry {
	type: 'status' | 'tool_start' | 'tool_end';
	label: string;
	timestamp: number;
	duration?: number;
}

export interface ChatMessage {
	id: string;
	role: Role;
	content: string;
	toolCalls?: ToolCall[];
	activityLog?: ActivityLogEntry[];
	timestamp: string;
}

export type StreamPhase = 'idle' | 'routing' | 'thinking' | 'executing' | 'generating';

interface AgentState {
	// Admin State
	isAdmin: boolean;
	adminToken: string | null;

	// Current Session State
	messages: ChatMessage[];
	isTyping: string | boolean;
	isHistoryLoading: boolean;

	// Streaming State
	streamingMessageId: string | null;
	isStreaming: boolean;
	streamPhase: StreamPhase;
	streamStartTime: number | null;

	// UI State
	isSidebarOpen: boolean;

	// Actions
	addMessage: (msg: ChatMessage) => void;
	setMessages: (msgs: ChatMessage[]) => void;
	updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
	appendToMessage: (id: string, token: string) => void;
	pushActivityLog: (id: string, entry: ActivityLogEntry) => void;
	updateLastActivityDuration: (id: string, toolName: string, duration: number) => void;
	setTyping: (typing: string | boolean) => void;
	setSidebarOpen: (open: boolean) => void;
	setHistoryLoading: (loading: boolean) => void;
	resetChat: () => void;
	setAdminState: (isAdmin: boolean, token?: string | null) => void;

	// Streaming Actions
	startStream: (messageId: string) => void;
	setStreamPhase: (phase: StreamPhase) => void;
	finalizeStream: () => void;
}

export const useAgentStore = create<AgentState>(set => ({
	isAdmin: false,
	adminToken: typeof window !== 'undefined' ? localStorage.getItem('adminToken') : null,
	messages: [],
	isTyping: false,
	isHistoryLoading: false,
	isSidebarOpen: false,

	// Streaming defaults
	streamingMessageId: null,
	isStreaming: false,
	streamPhase: 'idle',
	streamStartTime: null,

	addMessage: msg => set(state => ({ messages: [...state.messages, msg] })),
	setMessages: msgs => set({ messages: msgs }),

	updateMessage: (id, updates) =>
		set(state => ({
			messages: state.messages.map(m => (m.id === id ? { ...m, ...updates } : m)),
		})),

	appendToMessage: (id, token) =>
		set(state => ({
			messages: state.messages.map(m =>
				m.id === id ? { ...m, content: m.content + token } : m,
			),
		})),

	pushActivityLog: (id, entry) =>
		set(state => ({
			messages: state.messages.map(m =>
				m.id === id
					? { ...m, activityLog: [...(m.activityLog || []), entry] }
					: m,
			),
		})),

	updateLastActivityDuration: (id, toolName, duration) =>
		set(state => ({
			messages: state.messages.map(m => {
				if (m.id !== id || !m.activityLog) return m;
				const updatedLog = [...m.activityLog];
				for (let i = updatedLog.length - 1; i >= 0; i--) {
					if (updatedLog[i].label.includes(toolName) && updatedLog[i].type === 'tool_start') {
						updatedLog[i] = { ...updatedLog[i], duration };
						break;
					}
				}
				return { ...m, activityLog: updatedLog };
			}),
		})),

	setTyping: typing => set({ isTyping: typing }),
	setSidebarOpen: open => set({ isSidebarOpen: open }),
	setHistoryLoading: loading => set({ isHistoryLoading: loading }),
	resetChat: () => set({
		messages: [],
		isTyping: false,
		isStreaming: false,
		streamingMessageId: null,
		streamPhase: 'idle',
		streamStartTime: null,
	}),
	setAdminState: (isAdmin, token) => {
		if (token) {
			localStorage.setItem('adminToken', token);
		} else if (isAdmin === false) {
			localStorage.removeItem('adminToken');
		}
		set({ isAdmin, adminToken: token ?? null });
	},

	// Streaming Actions
	startStream: (messageId) => set({
		streamingMessageId: messageId,
		isStreaming: true,
		streamPhase: 'routing',
		streamStartTime: Date.now(),
		isTyping: false,
	}),

	setStreamPhase: (phase) => set({ streamPhase: phase }),

	finalizeStream: () => set({
		streamingMessageId: null,
		isStreaming: false,
		streamPhase: 'idle',
		streamStartTime: null,
	}),
}));
