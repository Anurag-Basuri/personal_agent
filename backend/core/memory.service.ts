import { BaseMessage } from '@langchain/core/messages';
import { BaseListChatMessageHistory } from '@langchain/core/chat_history';

/**
 * In-memory Chat History implementation for LangChain.
 * Used for storing Multi-turn Conversation Context explicitly.
 */
class InMemoryChatMessageHistory extends BaseListChatMessageHistory {
	lc_namespace = ['langchain', 'stores', 'message', 'in_memory'];
	private messages: BaseMessage[] = [];

	constructor(messages?: BaseMessage[]) {
		super();
		this.messages = messages || [];
	}

	async getMessages(): Promise<BaseMessage[]> {
		return this.messages;
	}

	async addMessage(message: BaseMessage): Promise<void> {
		this.messages.push(message);
	}

	async clear(): Promise<void> {
		this.messages = [];
	}
}

// Global store to keep track of sessions
export const messageHistories: Record<string, InMemoryChatMessageHistory> = {};

/**
 * Retrieves or creates a new history session instance based on sessionId.
 * Keeps memory isolated per user socket/session.
 */
export function getMessageHistory(sessionId: string): InMemoryChatMessageHistory {
	if (!messageHistories[sessionId]) {
		messageHistories[sessionId] = new InMemoryChatMessageHistory();
	}
	return messageHistories[sessionId];
}

export function clearSessionMemory(sessionId: string) {
	if (messageHistories[sessionId]) {
		messageHistories[sessionId].clear();
		delete messageHistories[sessionId];
	}
}
