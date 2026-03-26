import { tool } from '@langchain/core/tools';
import { z } from 'zod';
import { env } from '../../config/env';

export const githubRepoTool = tool(
	async ({ owner, repo }) => {
		try {
			console.log(`[github.repo.tool] Fetching README for ${owner}/${repo}`);
			
			const headers: Record<string, string> = {
				Accept: 'application/vnd.github.v3.raw', // Fetch raw markdown without Base64 decoding
				'User-Agent': 'Anurag-Dev-AI-Agent',
			};

			if (env.GITHUB_TOKEN) {
				headers.Authorization = `Bearer ${env.GITHUB_TOKEN}`;
			}

			const controller = new AbortController();
			const timeout = setTimeout(() => controller.abort(), 10000);

			const url = `https://api.github.com/repos/${owner}/${repo}/readme`;
			const response = await fetch(url, { headers, signal: controller.signal });
			clearTimeout(timeout);

			if (response.status === 404) {
				return `No README found for repository ${owner}/${repo}. The repository might be private or empty. Tell the user you cannot read its internal structure.`;
			}

			if (!response.ok) {
				return `Failed to fetch repo data. GitHub returned status: ${response.status}`;
			}

			const markdown = await response.text();
			
			// Token safety limit (roughly 3k tokens)
			if (markdown.length > 15000) {
				return markdown.substring(0, 15000) + '\n\n...[README TRUNCATED DUE TO EXTREME LENGTH]';
			}

			return `TECHNICAL ARCHITECTURE DOCUMENTATION FOR ${owner}/${repo}:\n\n${markdown}`;
		} catch (error) {
			console.error('[github.repo.tool] Error:', error);
			if ((error as Error).name === 'AbortError') {
				return 'GitHub API timed out. Tell the user the service is slow right now.';
			}
			return `Network error resolving GitHub repository: ${(error as Error).message}`;
		}
	},
	{
		name: 'read_github_readme',
		description: 'Reads the raw technical README and architecture documentation from any public GitHub repository. Crucial for answering deep technical questions like "How did you build X?" or "What features does project Y have?". Combine with search_projects to find the githubUrl first.',
		schema: z.object({
			owner: z.string().describe('The GitHub username or organization (e.g., Anurag-Basuri)'),
			repo: z.string().describe('The repository name (e.g., Streamify, Landform-V2)'),
		}),
	},
);
