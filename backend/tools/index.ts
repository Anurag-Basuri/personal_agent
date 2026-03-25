import { githubTool } from './github.tool';
import { leetcodeTool } from './leetcode.tool';
import { submitContactTool } from './contact.tool';
import { portfolioTool } from './portfolio.tool';

/**
 * All Model Context Protocol (MCP) tools available to the LangChain Agent.
 */
export const agentTools = [
    githubTool,
    leetcodeTool,
    submitContactTool,
    portfolioTool
];
