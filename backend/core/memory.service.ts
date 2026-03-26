import {
	BaseMessage,
	mapChatMessagesToStoredMessages,
	mapStoredMessagesToChatMessages,
} from '@langchain/core/messages';
import { BaseListChatMessageHistory } from '@langchain/core/chat_history';
import { prisma } from '../lib/prisma.js';

const MAX_HISTORY_MESSAGES = 20;

// Simple in-memory cache to avoid DB round-trips within the same request
const sessionCache = new Map<string, { messages: BaseMessage[]; ts: number }>();
const CACHE_TTL_MS = 60_000; // 1 minute

function pruneCache() {
	const now = Date.now();
	for (const [key, val] of sessionCache) {
		if (now - val.ts > CACHE_TTL_MS) sessionCache.delete(key);
	}
}

/**
 * Permanent Chat History implementation for LangChain using PostgreSQL.
 * Used for storing Multi-turn Conversation Context permanently so Anurag can view visitor questions.
 */
class PrismaChatMessageHistory extends BaseListChatMessageHistory {
	lc_namespace = ['langchain', 'stores', 'message', 'prisma'];
	private sessionId: string;

	constructor(sessionId: string) {
		super();
		this.sessionId = sessionId;
	}

	async getMessages(): Promise<BaseMessage[]> {
		// Check cache first
		const cached = sessionCache.get(this.sessionId);
		if (cached && Date.now() - cached.ts < CACHE_TTL_MS) {
			return cached.messages;
		}

		const session = await prisma.agentSession.findUnique({
			where: { sessionId: this.sessionId },
		});

		if (!session || !session.history) return [];

		const parsed =
			typeof session.history === 'string' ? JSON.parse(session.history) : session.history;
		const allMessages = mapStoredMessagesToChatMessages(parsed);

		// Trim to last N messages to keep prompts small
		const trimmed =
			allMessages.length > MAX_HISTORY_MESSAGES
				? allMessages.slice(-MAX_HISTORY_MESSAGES)
				: allMessages;

		// Update cache
		sessionCache.set(this.sessionId, { messages: trimmed, ts: Date.now() });

		return trimmed;
	}

	async addMessage(message: BaseMessage): Promise<void> {
		// Update cache immediately (avoid extra DB read)
		const cached = sessionCache.get(this.sessionId);
		const currentMessages = cached ? [...cached.messages] : await this.getMessages();

		currentMessages.push(message);

		// Trim before persisting
		const trimmed =
			currentMessages.length > MAX_HISTORY_MESSAGES
				? currentMessages.slice(-MAX_HISTORY_MESSAGES)
				: currentMessages;

		const stored = mapChatMessagesToStoredMessages(trimmed);

		await prisma.agentSession.upsert({
			where: { sessionId: this.sessionId },
			update: { history: stored as any },
			create: { sessionId: this.sessionId, history: stored as any },
		});

		// Refresh cache
		sessionCache.set(this.sessionId, { messages: trimmed, ts: Date.now() });
	}

	async clear(): Promise<void> {
		sessionCache.delete(this.sessionId);
		await prisma.agentSession.deleteMany({
			where: { sessionId: this.sessionId },
		});
	}
}

// Periodically prune expired cache entries
setInterval(pruneCache, CACHE_TTL_MS);

// Global factory to instantiate Postgres adapters
export function getMessageHistory(sessionId: string): PrismaChatMessageHistory {
	return new PrismaChatMessageHistory(sessionId);
}

export async function clearSessionMemory(sessionId: string) {
	const history = new PrismaChatMessageHistory(sessionId);
	await history.clear();
}

