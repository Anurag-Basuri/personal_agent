import { githubTool } from './github.tool.js';
import { githubRepoTool } from './github.repo.tool.js';
import { leetcodeTool } from './leetcode.tool.js';
import { portfolioTool } from './portfolio.tool.js';
import { submitContactTool } from './contact.tool.js';

/**
 * All Model Context Protocol (MCP) tools available to the LangChain Agent.
 */
export const agentTools = [
	githubTool,
	githubRepoTool,
	leetcodeTool,
	portfolioTool,
	submitContactTool,
];
