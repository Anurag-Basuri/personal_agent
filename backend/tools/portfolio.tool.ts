import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { prisma } from "../lib/prisma";

export const portfolioTool = tool(
  async ({ query }) => {
    try {
      console.log(`[portfolio.tool] Searching projects/skills for: ${query}`);

      // Simple Prisma full-text search simulation using OR filters
      const projects = await prisma.project.findMany({
        where: {
          status: "published",
          OR: [
            { title: { contains: query, mode: "insensitive" } },
            { description: { contains: query, mode: "insensitive" } },
          ],
        },
        select: {
          title: true,
          description: true,
          techStack: true,
          liveUrl: true,
          githubUrl: true,
        },
      });

      const normalizedQuery = query.toLowerCase();
      const filtered = projects.filter((p) => {
        if (!p.techStack) return true;
        try {
          const stack = JSON.parse(p.techStack) as string[];
          return stack.some((item) =>
            String(item).toLowerCase().includes(normalizedQuery),
          );
        } catch {
          return p.techStack.toLowerCase().includes(normalizedQuery);
        }
      });

      const results = filtered.slice(0, 3);

      if (results.length === 0) {
        return `No specific projects found for "${query}". Anurag might have experience with it, but there are no dedicated published projects matching this query.`;
      }

      // Format the DB response into Markdown text for the LLM to read
      let result = `Found ${results.length} relevant projects for "${query}":\n\n`;

      results.forEach((p) => {
        result += `### ${p.title}\n`;
        let stack = p.techStack ? p.techStack : "";
        try {
          const parsed = JSON.parse(p.techStack ?? "") as string[];
          stack = parsed.join(", ");
        } catch {
          // Use raw string as-is
        }
        result += `Tech Stack: ${stack}\n`;
        result += `Description: ${p.description}\n`;
        if (p.liveUrl) result += `Live Demo: ${p.liveUrl}\n`;
        if (p.githubUrl) result += `GitHub Repo: ${p.githubUrl}\n`;
        result += `\n`;
      });

      return result;
    } catch (error) {
      console.error("[portfolio.tool] Error:", error);
      return `Database search failed: ${(error as Error).message}`;
    }
  },
  {
    name: "search_projects",
    description:
      "Search अनुराग's DB for portfolio projects by keyword or tech stack (e.g. React, Python, E-commerce).",
    schema: z.object({
      query: z.string().describe("The search query or technology name"),
    }),
  },
);
