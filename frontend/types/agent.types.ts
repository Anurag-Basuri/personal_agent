export type AgentRole = 'user' | 'assistant';

export interface AgentMessage {
	id: string;
	role: AgentRole;
	content: string;
}

export interface AgentApiResponse {
	reply: string;
	sessionId: string;
}
