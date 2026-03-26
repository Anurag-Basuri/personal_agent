import { Request, Response } from 'express';
import { z } from 'zod';
import { processUserMessage } from './agent.service.js';
import { clearSessionMemory } from './core/memory.service.js';
import { ApiResponse } from './utils/ApiResponse.js';
import { ApiError } from './utils/ApiError.js';
import { agentLogger } from './core/agent.logger.js';

// ─── Validation ─────────────────────────────────────────────────

const ChatMessageSchema = z.object({
	message: z.string().min(1, 'Message cannot be empty').max(1000, 'Message too long'),
	sessionId: z.string().min(1, 'Session ID is required'),
	currentUrl: z.string().optional(),
});

const ClearSessionSchema = z.object({
	sessionId: z.string().min(1, 'Session ID is required'),
});

// ─── Controllers ───────────────────────────────────────────────

export async function sendMessage(req: Request, res: Response): Promise<void> {
	try {
		const data = ChatMessageSchema.parse(req.body);
		if (process.env.NODE_ENV === 'development') console.log('[Agent] User Message:', data.message);

		const response = await processUserMessage(data.message, data.sessionId, data.currentUrl);

		if (process.env.NODE_ENV === 'development') console.log('[Agent] Assistant Reply:', response.reply);
		agentLogger.debug('CTRL', 'Agent Reply', {
			reply: response.reply,
			sessionId: response.sessionId,
		});

		ApiResponse.ok(
			res,
			{
				reply: response.reply,
				intents: [], // Legacy compatibility
				sessionId: response.sessionId,
			},
			'Message processed successfully by Agent',
		);
	} catch (error: any) {
		// Zod validation errors handled by global error handler if re-thrown
		if (error?.name === 'ZodError') {
			throw error;
		}

		// Categorize the error for structured logging
		const isRateLimit = error?.message?.includes('Quota') || error?.message?.includes('429');
		const isTimeout =
			error?.message?.includes('timeout') || error?.message?.includes('AbortError');
		const isNetworkErr =
			error?.message?.includes('fetch') || error?.message?.includes('ECONNREFUSED');

		const source = 'AgentController.sendMessage';

		agentLogger.error('CTRL', 'Request failed', error, {
			sessionId: req.body?.sessionId,
			category: isRateLimit
				? 'RATE_LIMIT'
				: isTimeout
					? 'TIMEOUT'
					: isNetworkErr
						? 'NETWORK'
						: 'INTERNAL',
		});

		if (isRateLimit) {
			throw new ApiError(
				429,
				"I'm currently experiencing high demand. Please try again in a few moments!",
				[source]
			);
		}

		// Throw a structured ApiError so the frontend gets the "what and where"
		throw new ApiError(500, error.message || 'Agent failed to process message', [source]);
	}
}

export async function resetSession(req: Request, res: Response): Promise<void> {
	try {
		const data = ClearSessionSchema.parse(req.body);
		await clearSessionMemory(data.sessionId);
		agentLogger.info('MEMORY', `Session memory cleared`, { sessionId: data.sessionId });
		ApiResponse.ok(res, { cleared: true }, 'Agent session memory cleared');
	} catch (error) {
		throw error;
	}
}
