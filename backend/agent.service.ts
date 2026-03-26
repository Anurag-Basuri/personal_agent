import { getBoundLLMs, llmInfo } from './core/llm.factory.js';
import { agentTools } from './tools/index.js';
import { SYSTEM_PERSONA } from './core/prompts.js';
import { getMessageHistory } from './core/memory.service.js';
import { HumanMessage, SystemMessage, ToolMessage } from '@langchain/core/messages';
import { getBasePortfolioContext } from './rag/context.builder.js';
import { agentLogger } from './core/agent.logger.js';

const LLM_TIMEOUT_MS = 20_000; // 20 seconds — faster failure detection

/** Race an LLM call against a timeout. */
async function invokeWithTimeout(llm: any, messages: any[], label: string): Promise<any> {
	return Promise.race([
		llm.invoke(messages),
		new Promise((_, reject) =>
			setTimeout(() => {
				const timeoutErr = new Error(`${label} timed out after ${LLM_TIMEOUT_MS / 1000}s`);
				(timeoutErr as any).isTimeout = true;
				reject(timeoutErr);
			}, LLM_TIMEOUT_MS),
		),
	]).catch(err => {
		// Log specific errors for better debugging if available
		if (err?.message?.includes('400')) {
			agentLogger.error('LLM', `🚨 ${label} returned 400 Bad Request`, err, {
				hint: 'Check model name or message format',
				messagesCount: messages.length,
			});
		}
		throw err;
	});
}

export interface AgentResponse {
	reply: string;
	sessionId: string;
}

export async function processUserMessage(
	message: string,
	sessionId: string,
	currentUrl?: string,
): Promise<AgentResponse> {
	const requestStartTime = Date.now();

	agentLogger.info('SYSTEM', `━━━ New Request ━━━`, {
		sessionId,
		llmMode: llmInfo.mode,
		primary: llmInfo.primaryProvider || 'NONE',
		fallback: llmInfo.fallbackProvider || 'NONE',
		currentUrl: currentUrl || 'N/A',
		messagePreview: message.substring(0, 80),
	});

	const { primary, fallback } = getBoundLLMs(agentTools);

	const memory = getMessageHistory(sessionId);
	const history = await memory.getMessages();
	agentLogger.debug('MEMORY', `Loaded ${history.length} messages from session history`, {
		sessionId,
	});

	const portfolioContext = await getBasePortfolioContext();
	const locationContext = currentUrl
		? `\n[SCREEN CONTEXT]\nThe user is currently looking at the page: ${currentUrl}. If they use words like "this" or "here", they are referring to this page.\n[END SCREEN CONTEXT]`
		: '';

	const systemPrompt = new SystemMessage(
		`${SYSTEM_PERSONA}\n\n[PORTFOLIO CONTEXT]\n${portfolioContext}\n[END CONTEXT]${locationContext}`,
	);

	const turnMessages = [systemPrompt, ...history, new HumanMessage(message)];
	// NOTE: Human message is persisted AFTER the response loop to avoid duplicates

	const approxChars = turnMessages.reduce((acc, m) => acc + String(m.content).length, 0);
	agentLogger.debug('LLM', `Estimated prompt size: ${approxChars} characters`, { sessionId });

	let callCount = 0;
	const MAX_LOOPS = 3;

	// ─── Sticky Fallback ────────────────────────────────────────────
	// If the primary LLM fails once during a request, skip it for all
	// subsequent loops. This prevents repeated 30s timeout penalties.
	let primaryFailed = false;

	while (callCount < MAX_LOOPS) {
		let aiMsg: any;
		let usedProvider = '';

		// ─── LLM Invocation with Sticky Fallback ────────────────────
		const activePrimary = primary && !primaryFailed ? primary : null;

		if (activePrimary) {
			const llmStart = agentLogger.llmStart(llmInfo.primaryProvider, llmInfo.primaryModel);
			try {
				aiMsg = await invokeWithTimeout(
					activePrimary,
					turnMessages,
					llmInfo.primaryProvider,
				);
				agentLogger.llmSuccess(
					llmStart,
					(aiMsg.tool_calls?.length ?? 0) > 0,
					aiMsg.tool_calls?.length ?? 0,
				);
				usedProvider = llmInfo.primaryProvider;
			} catch (primaryError: any) {
				agentLogger.llmError(llmStart, primaryError);
				primaryFailed = true; // ← Sticky: won't try primary again this request
				agentLogger.warn(
					'LLM',
					`🔒 Primary (${llmInfo.primaryProvider}) disabled for remainder of this request`,
				);

				// Try fallback
				if (fallback) {
					agentLogger.info(
						'LLM',
						`🔄 Switching to fallback (${llmInfo.fallbackProvider})`,
					);
					const fallbackStart = agentLogger.llmStart(
						llmInfo.fallbackProvider,
						llmInfo.fallbackModel,
					);
					try {
						aiMsg = await invokeWithTimeout(
							fallback,
							turnMessages,
							llmInfo.fallbackProvider,
						);
						agentLogger.llmSuccess(
							fallbackStart,
							(aiMsg.tool_calls?.length ?? 0) > 0,
							aiMsg.tool_calls?.length ?? 0,
						);
						usedProvider = llmInfo.fallbackProvider;
					} catch (fallbackError: any) {
						agentLogger.llmError(fallbackStart, fallbackError);
						agentLogger.error(
							'LLM',
							'💀 Both primary AND fallback LLMs failed',
							fallbackError,
							{
								primaryError: primaryError.message?.substring(0, 100),
							},
						);
						throw fallbackError;
					}
				} else {
					throw primaryError;
				}
			}
		} else if (fallback) {
			// Primary already failed (sticky) or not configured — go straight to fallback
			if (primaryFailed) {
				agentLogger.debug(
					'LLM',
					`⏩ Skipping ${llmInfo.primaryProvider} (failed earlier) — using ${llmInfo.fallbackProvider} directly`,
				);
			}
			const llmStart = agentLogger.llmStart(llmInfo.fallbackProvider, llmInfo.fallbackModel);
			try {
				aiMsg = await invokeWithTimeout(fallback, turnMessages, llmInfo.fallbackProvider);
				agentLogger.llmSuccess(
					llmStart,
					(aiMsg.tool_calls?.length ?? 0) > 0,
					aiMsg.tool_calls?.length ?? 0,
				);
				usedProvider = llmInfo.fallbackProvider;
			} catch (err: any) {
				agentLogger.llmError(llmStart, err);
				throw err;
			}
		} else {
			throw new Error('No LLM providers available');
		}

		// ─── Process Response ───────────────────────────────────────
		turnMessages.push(aiMsg);
		await memory.addMessage(aiMsg);

		const toolCalls = aiMsg.tool_calls ?? [];

		if (toolCalls.length > 0) {
			agentLogger.info(
				'TOOL',
				`Agent (${usedProvider}) requested ${toolCalls.length} tool(s)`,
				{
					tools: toolCalls.map((tc: any) => tc.name),
					loop: callCount + 1,
				},
			);

			for (const toolCall of toolCalls) {
				const selectedTool = agentTools.find(tool => tool.name === toolCall.name);
				if (!selectedTool) {
					agentLogger.warn('TOOL', `Tool "${toolCall.name}" not found in registry`, {
						available: agentTools.map(t => t.name),
					});
					const toolMsg = new ToolMessage({
						tool_call_id: toolCall.id!,
						content: `Tool ${toolCall.name} not found.`,
						name: toolCall.name,
					});
					turnMessages.push(toolMsg);
					await memory.addMessage(toolMsg);
					continue;
				}

				const toolStart = agentLogger.toolStart(toolCall.name, toolCall.args || {});
				try {
					const toolOutput = await (selectedTool as any).invoke(toolCall.args);
					const outputStr = String(toolOutput);
					agentLogger.toolSuccess(toolCall.name, toolStart, outputStr);

					const toolMsg = new ToolMessage({
						tool_call_id: toolCall.id!,
						content: outputStr,
						name: toolCall.name,
					});
					turnMessages.push(toolMsg);
					await memory.addMessage(toolMsg);
				} catch (e: any) {
					agentLogger.toolError(toolCall.name, toolStart, e);

					const errorMsg = new ToolMessage({
						tool_call_id: toolCall.id!,
						content: `Failed to execute tool: ${e.message}`,
						name: toolCall.name,
					});
					turnMessages.push(errorMsg);
					await memory.addMessage(errorMsg);
				}
			}
			callCount++;
		} else {
			// Finished — final reply
			const totalDuration = Date.now() - requestStartTime;
			agentLogger.info('SYSTEM', `━━━ Request Complete ━━━`, {
				sessionId,
				usedProvider,
				primarySkipped: primaryFailed,
				totalDurationMs: totalDuration,
				llmLoops: callCount + 1,
				replyPreview: String(aiMsg.content).substring(0, 100),
			});

			// Persist the human message + final AI reply
			await memory.addMessage(new HumanMessage(message));

			return {
				reply: String(aiMsg.content),
				sessionId,
			};
		}
	}

	const totalDuration = Date.now() - requestStartTime;
	agentLogger.warn('SYSTEM', `Agent hit MAX_LOOPS (${MAX_LOOPS}) — forced stop`, {
		sessionId,
		totalDurationMs: totalDuration,
	});

	return {
		reply: 'I had to think too long about that. Could you try asking in a different way?',
		sessionId,
	};
}
