import { Request, Response, NextFunction } from "express";
import { z } from "zod";
import { processUserMessage } from "./agent.service";
import { clearSessionMemory } from "./core/memory.service";
import { ApiError } from "./utils/ApiError";
import { ApiResponse } from "./utils/ApiResponse";

// ─── Validation ─────────────────────────────────────────────────

const ChatMessageSchema = z.object({
  message: z
    .string()
    .min(1, "Message cannot be empty")
    .max(1000, "Message too long"),
  sessionId: z.string().min(1, "Session ID is required"),
});

const ClearSessionSchema = z.object({
  sessionId: z.string().min(1, "Session ID is required"),
});

// ─── Controllers ───────────────────────────────────────────────

export async function sendMessage(
  req: Request,
  res: Response,
  next: NextFunction,
): Promise<void> {
  try {
    const data = ChatMessageSchema.parse(req.body);

    const response = await processUserMessage(data.message, data.sessionId);

    ApiResponse.ok(
      res,
      {
        reply: response.reply,
        intents: [], // Legacy compatibility
        sessionId: response.sessionId,
      },
      "Message processed successfully by Agent",
    );
  } catch (error: any) {
    console.error("[agent.controller] Global Error:", error.message || error);

    // Map specific LangChain or API rate limit errors securely
    if (
      error instanceof Error &&
      (error.message.includes("Quota") || error.message.includes("429"))
    ) {
      return next(
        ApiError.ServiceUnavailable(
          "AI service is currently rate limited. Falling back failed. Please try again later.",
        ),
      );
    }

    return next(
      new ApiError(500, "Failed to process message due to Agent failure"),
    );
  }
}

export async function resetSession(
  req: Request,
  res: Response,
  next: NextFunction,
): Promise<void> {
  try {
    const data = ClearSessionSchema.parse(req.body);
    clearSessionMemory(data.sessionId);
    ApiResponse.ok(res, { cleared: true }, "Agent session memory cleared");
  } catch (error) {
    next(error);
  }
}
