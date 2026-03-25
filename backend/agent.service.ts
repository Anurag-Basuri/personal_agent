import { getLLM } from './core/llm.factory';
import { agentTools } from './tools';
import { SYSTEM_PERSONA } from './core/prompts';
import { getMessageHistory } from './core/memory.service';
import { HumanMessage, SystemMessage, ToolMessage } from '@langchain/core/messages';
import { getBasePortfolioContext } from './rag/context.builder';

export interface AgentResponse {
	reply: string;
	sessionId: string;
}

export async function processUserMessage(message: string, sessionId: string): Promise<AgentResponse> {
	console.log(`[agent.service] Processing message for session: ${sessionId}`);
	
	const llm = getLLM();
	const llmWithTools = llm.bindTools(agentTools);

	const memory = getMessageHistory(sessionId);
	const history = await memory.getMessages();

	const portfolioContext = await getBasePortfolioContext();
	const systemPrompt = new SystemMessage(`${SYSTEM_PERSONA}\n\n[PORTFOLIO CONTEXT]\n${portfolioContext}\n[END CONTEXT]`);
	
	// Prepare messages array for the current turn
	const turnMessages = [
		systemPrompt,
		...history,
		new HumanMessage(message)
	];

	// Ensure user message is saved to memory first
	await memory.addMessage(new HumanMessage(message));

	let callCount = 0;
	const MAX_LOOPS = 4;

	while (callCount < MAX_LOOPS) {
		const aiMsg = await llmWithTools.invoke(turnMessages);
		turnMessages.push(aiMsg);
		
		// Wait, we only add the final generated standard text to history, not intermediate tool steps?
		// Actually, adding tool calls to memory is standard so long-term memory tracks agent operations.
		await memory.addMessage(aiMsg);

		if (aiMsg.tool_calls && aiMsg.tool_calls.length > 0) {
			console.log(`[agent.service] Agent requested ${aiMsg.tool_calls.length} tools`);
			for (const toolCall of aiMsg.tool_calls) {
				const selectedTool = agentTools.find(tool => tool.name === toolCall.name);
				if (!selectedTool) {
					const toolMsg = new ToolMessage({
						tool_call_id: toolCall.id!,
						content: `Tool ${toolCall.name} not found.`,
						name: toolCall.name
					});
					turnMessages.push(toolMsg);
					await memory.addMessage(toolMsg);
					continue;
				}

				try {
					const toolOutput = await (selectedTool as any).invoke(toolCall.args);
					const toolMsg = new ToolMessage({
						tool_call_id: toolCall.id!,
						content: String(toolOutput),
						name: toolCall.name
					});
					turnMessages.push(toolMsg);
					await memory.addMessage(toolMsg);
				} catch (e: any) {
					console.error(`[agent.service] Tool execution error for ${toolCall.name}:`, e.message);
					const errorMsg = new ToolMessage({
						tool_call_id: toolCall.id!,
						content: `Failed to execute tool: ${e.message}`,
						name: toolCall.name
					});
					turnMessages.push(errorMsg);
					await memory.addMessage(errorMsg);
				}
			}
			callCount++;
		} else {
			// Finished execution
			return {
				reply: String(aiMsg.content),
				sessionId,
			};
		}
	}

	return {
		reply: 'I had to think too long about that. Could you try asking in a different way?',
		sessionId,
	};
}
