import { prisma } from "../lib/prisma";

export async function getBasePortfolioContext(): Promise<string> {
  try {
    const profile = await prisma.profile.findFirst({
      include: { socialLinks: true },
    });

    if (!profile) return "No profile found.";

    let context = `[Anurag's Core Profile Data]\n`;
    context += `Name: ${profile.name}\n`;
    if (profile.header) context += `Headline: ${profile.header}\n`;
    if (profile.bio) context += `Bio: ${profile.bio}\n`;
    if (profile.skills) {
      try {
        const skills = JSON.parse(profile.skills) as Record<string, string[]>;
        context += `Skills:\n`;
        Object.entries(skills).forEach(([category, list]) => {
          context += `- ${category}: ${list.join(", ")}\n`;
        });
      } catch {
        context += `Skills: ${profile.skills}\n`;
      }
    }

    const availability = profile.openToWork
      ? `Open to Work (Available ${profile.availableFrom || "immediately"}, Notice Period: ${profile.noticePeriod || "N/A"})`
      : "Currently employed / Not looking";
    context += `Current Status: ${availability}\n`;
    context += `[End Profile Data]\n`;

    return context;
  } catch (error) {
    console.error("[context.builder] Error fetching base profile:", error);
    return "";
  }
}
