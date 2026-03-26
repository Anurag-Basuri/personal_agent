import { ChatGoogleGenerativeAI } from '@langchain/google-genai';
import { ChatOpenAI } from '@langchain/openai';
import { env } from '../config/env.js';
import { agentLogger } from './agent.logger.js';

import { DynamicStructuredTool } from '@langchain/core/tools';

// ─── Singleton State ─────────────────────────────────────────────

let _primaryLlm: ChatOpenAI | null = null; // HuggingFace is now primary
let _fallbackLlm: ChatGoogleGenerativeAI | null = null; // Gemini is now fallback
let _initialized = false;

export const llmInfo = {
	primaryProvider: '',
	primaryModel: '',
	fallbackProvider: '',
	fallbackModel: '',
	mode: 'NONE' as 'dual' | 'primary-only' | 'fallback-only' | 'NONE',
};

function initLLMs() {
	if (_initialized) return;
	_initialized = true;

	// 1. Configure Primary Model (HuggingFace — fast, no rate limit issues)
	if (env.HF_TOKEN) {
		_primaryLlm = new ChatOpenAI({
			model: 'Qwen/Qwen2.5-72B-Instruct',
			apiKey: env.HF_TOKEN,
			configuration: { baseURL: 'https://router.huggingface.co/v1' },
			temperature: 0.3,
			timeout: 30000,
			maxTokens: 1000,
		});
		llmInfo.primaryProvider = 'HuggingFace';
		llmInfo.primaryModel = 'Qwen2.5-72B-Instruct';
		agentLogger.info('LLM', '🟢 Primary LLM configured', {
			provider: 'HuggingFace',
			model: 'Qwen2.5-72B-Instruct',
		});
	} else {
		agentLogger.warn('LLM', '⚠️ HF_TOKEN not set — HuggingFace primary skipped');
	}

	// 2. Configure Fallback Model (Gemini)
	if (env.GEMINI_API_KEY || env.AI_PROVIDER === 'gemini') {
		const apiKey = env.GEMINI_API_KEY || process.env.AI_API_KEY;
		if (apiKey) {
			_fallbackLlm = new ChatGoogleGenerativeAI({
				model: 'gemini-2.5-flash',
				apiKey: apiKey,
				temperature: 0.3,
				maxOutputTokens: 1000,
			});
			llmInfo.fallbackProvider = 'Gemini';
			llmInfo.fallbackModel = 'gemini-2.5-flash-preview-05-20';
			agentLogger.info('LLM', '🟡 Fallback LLM configured', {
				provider: 'Google Gemini',
				model: 'gemini-2.5-flash-preview-05-20',
			});
		}
	}

	// Determine mode
	if (_primaryLlm && _fallbackLlm) {
		llmInfo.mode = 'dual';
		agentLogger.info('LLM', '🚀 Dual-LLM ready: HuggingFace (primary) → Gemini (fallback)');
	} else if (_primaryLlm) {
		llmInfo.mode = 'primary-only';
		agentLogger.info('LLM', '🚀 Single-LLM ready: HuggingFace (no fallback configured)');
	} else if (_fallbackLlm) {
		llmInfo.mode = 'fallback-only';
		agentLogger.warn('LLM', '⚠️ Running on Gemini only (no primary HuggingFace configured)');
	} else {
		llmInfo.mode = 'NONE';
		agentLogger.error('SYSTEM', 'FATAL: No AI Providers configured', null, {
			hint: 'Set HF_TOKEN or GEMINI_API_KEY',
		});
	}
}

// Initialize immediately on module load
initLLMs();

/**
 * Returns the bound primary + fallback LLM instances.
 */
export function getBoundLLMs(tools: DynamicStructuredTool[]) {
	if (llmInfo.mode === 'NONE') {
		throw new Error('No AI Providers configured. Please set HF_TOKEN or GEMINI_API_KEY.');
	}

	return {
		primary: _primaryLlm ? _primaryLlm.bindTools(tools) : null,
		fallback: _fallbackLlm ? _fallbackLlm.bindTools(tools) : null,
		info: llmInfo,
	};
}
