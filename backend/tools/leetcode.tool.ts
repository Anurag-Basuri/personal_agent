import { tool } from '@langchain/core/tools';
import { z } from 'zod';

export const leetcodeTool = tool(
	async ({ username }) => {
		try {
			// Using a popular public proxy for LeetCode stats since they only have GraphQL
			const res = await fetch(`https://leetcode-stats-api.herokuapp.com/${username}`);
			const data = (await res.json()) as any;

			if (data.status === 'error') {
				return `LeetCode account "${username}" not found or private.`;
			}

			// Format for the LLM
			let result = `LeetCode Profile: ${username}\n`;
			result += `Total Solved: ${data.totalSolved} / ${data.totalQuestions} (Global Ranking: ${data.ranking})\n`;
			result += `Difficulty Breakdown:\n`;
			result += `- Easy: ${data.easySolved}\n`;
			result += `- Medium: ${data.mediumSolved}\n`;
			result += `- Hard: ${data.hardSolved}\n`;

			if (data.acceptanceRate) {
				result += `Acceptance Rate: ${data.acceptanceRate}%\n`;
			}
			if (data.contributionPoints) {
				result += `Contribution Points: ${data.contributionPoints}\n`;
			}

			return result;
		} catch (error) {
			console.error('[leetcode.tool] Error:', error);
			return `Error fetching LeetCode data: ${(error as Error).message}`;
		}
	},
	{
		name: 'get_leetcode_stats',
		description: 'Fetch Anurag\'s live LeetCode competitive programming stats (problems solved, ranking, etc).',
		schema: z.object({
			username: z.string().default('avijit-basuri').describe('The LeetCode username to fetch. Always defaults to "avijit-basuri".'),
		}),
	},
);
