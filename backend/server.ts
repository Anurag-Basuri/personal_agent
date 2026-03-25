import express, { Request, Response, NextFunction } from "express";
import cors from "cors";
import agentRoutes from "./agent.routes.js";
import { env } from "./config/env.js";
import { ApiError } from "./utils/ApiError.js";

const app = express();

app.use(
  cors({
    origin: env.CLIENT_URL || true,
    credentials: true,
  }),
);

app.use(express.json({ limit: "1mb" }));

app.get("/health", (_req: Request, res: Response) => {
  res.json({ status: "ok" });
});

app.use("/chat", agentRoutes);

app.use((err: unknown, _req: Request, res: Response, _next: NextFunction) => {
  const apiError =
    err instanceof ApiError
      ? err
      : new ApiError(500, "Unexpected server error");
  res.status(apiError.statusCode).json({
    success: false,
    message: apiError.message,
    errors: apiError.errors ?? [],
  });
});

const port = Number(env.PORT || 4000);
app.listen(port, () => {
  console.log(`[server] Backend running on http://localhost:${port}`);
});
