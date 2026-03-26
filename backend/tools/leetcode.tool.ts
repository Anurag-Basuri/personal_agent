import { tool } from '@langchain/core/tools';
import { z } from 'zod';

/**
 * LeetCode GraphQL query — same approach as coding-stats.service.ts (which works reliably).
 * Uses the official LeetCode GraphQL API instead of third-party proxies that get rate-limited.
 */
const LEETCODE_QUERY = `
query getUserProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      ranking
    }
    submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
      }
    }
  }
  userContestRanking(username: $username) {
    rating
    globalRanking
  }
}`;

export const leetcodeTool = tool(
	async ({ username }) => {
		try {
			const controller = new AbortController();
			const timeout = setTimeout(() => controller.abort(), 10000);

			const res = await fetch('https://leetcode.com/graphql/', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Referer: 'https://leetcode.com/',
					Origin: 'https://leetcode.com',
					'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
				},
				body: JSON.stringify({
					query: LEETCODE_QUERY,
					variables: { username },
				}),
				signal: controller.signal,
			});
			clearTimeout(timeout);

			if (!res.ok) {
				return `The LeetCode API returned status ${res.status}. Tell the user you can't fetch live LeetCode stats right now but they can check the coding profiles section.`;
			}

			const text = await res.text();
			let json: any;
			try {
				json = JSON.parse(text);
			} catch {
				return `The LeetCode API returned an invalid response. Tell the user the service is temporarily down.`;
			}

			const user = json.data?.matchedUser;
			if (!user) {
				return `LeetCode account "${username}" not found or the API returned no data.`;
			}

			// Parse submission stats
			const submissions = user.submitStatsGlobal?.acSubmissionNum || [];
			const findCount = (difficulty: string) =>
				submissions.find(
					(s: { difficulty: string; count: number }) => s.difficulty === difficulty,
				)?.count || 0;

			const contestRanking = json.data?.userContestRanking;

			// Format for the LLM
			let result = `LeetCode Profile: ${username}\n`;
			result += `Total Solved: ${findCount('All')}`;
			if (user.profile?.ranking) result += ` (Global Ranking: #${user.profile.ranking})`;
			result += '\n';
			result += `Difficulty Breakdown:\n`;
			result += `- Easy: ${findCount('Easy')}\n`;
			result += `- Medium: ${findCount('Medium')}\n`;
			result += `- Hard: ${findCount('Hard')}\n`;

			if (contestRanking?.rating) {
				result += `Contest Rating: ${Math.round(contestRanking.rating)}\n`;
			}
			if (contestRanking?.globalRanking) {
				result += `Contest Global Rank: #${contestRanking.globalRanking}\n`;
			}

			return result;
		} catch (error: any) {
			console.error('[leetcode.tool] Error:', error);
			if (error?.name === 'AbortError') {
				return 'LeetCode API timed out. Tell the user the service is slow right now, but they can check the coding profiles section on the portfolio.';
			}
			return `Error fetching LeetCode data: ${error.message}. Tell the user to check the coding profiles section instead.`;
		}
	},
	{
		name: 'get_leetcode_stats',
		description:
			"Fetch Anurag's live LeetCode competitive programming stats (problems solved, ranking, etc).",
		schema: z.object({
			username: z
				.string()
				.default('Anurag_Basuri')
				.describe('The LeetCode username to fetch. Always defaults to "Anurag_Basuri".'),
		}),
	},
);
