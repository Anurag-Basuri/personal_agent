import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { ChatOpenAI } from "@langchain/openai";
import { env } from "../config/env";

/**
 * Returns a configured LangChain LLM with fallback capabilities.
 * Primary: Google Gemini 2.0 Flash
 * Fallback: Hugging Face Qwen 2.5 72B Instruct (Triggered on API errors or Rate Limits)
 */
export function getLLM() {
  let primaryLlm = null;
  let fallbackLlm = null;

  // 1. Configure Primary Model (Gemini)
  if (env.GEMINI_API_KEY || env.AI_PROVIDER === "gemini") {
    const apiKey = env.GEMINI_API_KEY || process.env.AI_API_KEY; // backwards compatibility
    if (apiKey) {
      primaryLlm = new ChatGoogleGenerativeAI({
        model: "gemini-2.0-flash",
        apiKey: apiKey,
        temperature: 0.3,
        maxOutputTokens: 1000,
      });
    }
  }

  // 2. Configure Fallback Model (Hugging Face Serverless via OpenAI SDK)
  if (env.HF_TOKEN) {
    fallbackLlm = new ChatOpenAI({
      model: "Qwen/Qwen2.5-72B-Instruct",
      apiKey: env.HF_TOKEN,
      configuration: {
        baseURL: "https://api-inference.huggingface.co/models/",
      },
      temperature: 0.3,
      maxTokens: 1000,
    });
  }

  // 3. Orchestrate
  if (primaryLlm && fallbackLlm) {
    console.log(
      "[Agent] Dual-LLM initialized: Gemini (Primary) -> Hugging Face (Fallback)",
    );
    return primaryLlm.withFallbacks({
      fallbacks: [fallbackLlm],
    });
  } else if (primaryLlm) {
    console.log("[Agent] LLM initialized: Gemini (Standalone)");
    return primaryLlm;
  } else if (fallbackLlm) {
    console.log("[Agent] LLM initialized: Hugging Face (Standalone)");
    return fallbackLlm;
  } else {
    throw new Error(
      "No AI Providers configured. Please set GEMINI_API_KEY or HF_TOKEN.",
    );
  }
}
