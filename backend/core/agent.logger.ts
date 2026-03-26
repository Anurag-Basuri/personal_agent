/**
 * Centralized Agent Logger
 * Provides structured, timestamped, categorized logging for the entire Agent pipeline.
 * Categories: LLM, TOOL, MEMORY, CTRL (Controller), SYSTEM
 */

type LogCategory = 'LLM' | 'TOOL' | 'MEMORY' | 'CTRL' | 'SYSTEM';
type LogLevel = 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';

function timestamp(): string {
	return new Date().toISOString().replace('T', ' ').substring(0, 19);
}

function formatLog(level: LogLevel, category: LogCategory, message: string, meta?: Record<string, any>): string {
	const metaStr = meta ? ` | ${JSON.stringify(meta)}` : '';
	return `[${timestamp()}] [${level}] [Agent:${category}] ${message}${metaStr}`;
}

export const agentLogger = {
	// ─── Info ───────────────────────────────────────────────────────
	info(category: LogCategory, message: string, meta?: Record<string, any>) {
		console.log(formatLog('INFO', category, message, meta));
	},

	// ─── Warn ───────────────────────────────────────────────────────
	warn(category: LogCategory, message: string, meta?: Record<string, any>) {
		console.warn(formatLog('WARN', category, message, meta));
	},

	// ─── Error ──────────────────────────────────────────────────────
	error(category: LogCategory, message: string, error?: any, meta?: Record<string, any>) {
		const errMeta = {
			...meta,
			errorName: error?.name || 'Unknown',
			errorMessage: error?.message || String(error),
			...(error?.status && { httpStatus: error.status }),
		};
		console.error(formatLog('ERROR', category, message, errMeta));
	},

	// ─── Debug (verbose, only in dev) ───────────────────────────────
	debug(category: LogCategory, message: string, meta?: Record<string, any>) {
		if (process.env.NODE_ENV === 'development' || process.env.DEBUG_AGENT === 'true') {
			console.log(formatLog('DEBUG', category, message, meta));
		}
	},

	// ─── Tool Execution (special structured format) ─────────────────
	toolStart(toolName: string, args: Record<string, any>) {
		console.log(formatLog('INFO', 'TOOL', `⚡ Executing: ${toolName}`, { args }));
		return Date.now(); // Return start time for duration tracking
	},

	toolSuccess(toolName: string, startTime: number, outputPreview?: string) {
		const durationMs = Date.now() - startTime;
		console.log(formatLog('INFO', 'TOOL', `✅ ${toolName} completed`, {
			durationMs,
			outputLength: outputPreview?.length ?? 0,
			preview: outputPreview?.substring(0, 120),
		}));
	},

	toolError(toolName: string, startTime: number, error: any) {
		const durationMs = Date.now() - startTime;
		console.error(formatLog('ERROR', 'TOOL', `❌ ${toolName} FAILED`, {
			durationMs,
			errorName: error?.name || 'Unknown',
			errorMessage: error?.message || String(error),
		}));
	},

	// ─── LLM Invocation (special structured format) ─────────────────
	llmStart(provider: string, model: string) {
		console.log(formatLog('INFO', 'LLM', `🧠 Invoking ${provider} (${model})`));
		return Date.now();
	},

	llmSuccess(startTime: number, hasToolCalls: boolean, toolCount: number) {
		const durationMs = Date.now() - startTime;
		console.log(formatLog('INFO', 'LLM', `✅ LLM responded`, {
			durationMs,
			hasToolCalls,
			toolCallCount: toolCount,
		}));
	},

	llmError(startTime: number, error: any) {
		const durationMs = Date.now() - startTime;
		console.error(formatLog('ERROR', 'LLM', `❌ LLM invocation FAILED`, {
			durationMs,
			errorName: error?.name || 'Unknown',
			errorMessage: error?.message || String(error),
			isRateLimit: error?.message?.includes('429') || error?.message?.includes('Quota'),
		}));
	},
};
