import dotenv from "dotenv";
import { z } from "zod";

dotenv.config();

const EnvSchema = z.object({
  NODE_ENV: z.string().optional(),
  PORT: z.string().optional(),
  CLIENT_URL: z.string().optional(),
  DATABASE_URL: z.string().optional(),
  GEMINI_API_KEY: z.string().optional(),
  AI_PROVIDER: z.string().optional(),
  HF_TOKEN: z.string().optional(),
  GITHUB_TOKEN: z.string().optional(),
});

export const env = EnvSchema.parse(process.env);
