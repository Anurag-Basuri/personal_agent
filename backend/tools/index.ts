import { githubTool } from './github.tool';
import { githubRepoTool } from './github.repo.tool';
import { leetcodeTool } from './leetcode.tool';
import { portfolioTool } from './portfolio.tool';
import { submitContactTool } from './contact.tool';

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
