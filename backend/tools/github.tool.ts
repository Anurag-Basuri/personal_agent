import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { env } from "../config/env";

/**
 * Native LangChain Tool to fetch Anurag's GitHub Activity.
 */
export const githubTool = tool(
  async ({ username }) => {
    try {
      const headers: Record<string, string> = {
        "User-Agent": "Portfolio-App",
      };
      if (env.GITHUB_TOKEN) {
        headers["Authorization"] = `token ${env.GITHUB_TOKEN}`;
      }

      // Fetch recent events
      const eventsRes = await fetch(
        `https://api.github.com/users/${username}/events/public?per_page=5`,
        { headers },
      );
      if (!eventsRes.ok) return `Failed to fetch GitHub events for ${username}`;
      const events = (await eventsRes.json()) as any[];

      // Fetch user info
      const userRes = await fetch(`https://api.github.com/users/${username}`, {
        headers,
      });
      const user = userRes.ok ? ((await userRes.json()) as any) : null;

      // Format human-readable output for the LLM
      let result = `GitHub Profile: ${username}\n`;
      if (user) {
        result += `Followers: ${user.followers} | Following: ${user.following} | Public Repos: ${user.public_repos}\n`;
        if (user.bio) result += `Bio: ${user.bio}\n`;
      }

      if (events.length === 0) {
        result += "\nNo recent public activity.";
        return result;
      }

      result += "\nRecent Activity (Last 5 events):\n";
      events.forEach((event) => {
        const repoName = event.repo?.name || "unknown repo";
        const date = new Date(event.created_at).toLocaleDateString();

        switch (event.type) {
          case "PushEvent":
            const commits = event.payload?.commits?.length || 0;
            result += `- [${date}] Pushed ${commits} commits to ${repoName}\n`;
            break;
          case "PullRequestEvent":
            const action = event.payload?.action;
            result += `- [${date}] ${action} a pull request in ${repoName}\n`;
            break;
          case "CreateEvent":
            result += `- [${date}] Created a new ${event.payload?.ref_type || "resource"} in ${repoName}\n`;
            break;
          case "WatchEvent":
            result += `- [${date}] Starred ${repoName}\n`;
            break;
          case "IssuesEvent":
            result += `- [${date}] ${event.payload?.action} an issue in ${repoName}\n`;
            break;
          default:
            result += `- [${date}] Performed ${event.type} in ${repoName}\n`;
        }
      });

      return result;
    } catch (error) {
      console.error("[github.tool] Error:", error);
      return `Error fetching GitHub data: ${(error as Error).message}`;
    }
  },
  {
    name: "get_github_activity",
    description:
      "Fetch Anurag's live GitHub profile stats and recent open-source activity.",
    schema: z.object({
      username: z
        .string()
        .default("anurag-basuri")
        .describe(
          "The GitHub username to fetch. Always defaults to anurag-basuri.",
        ),
    }),
  },
);
