import express, { Request, Response } from "express";
import cors from "cors";
import dotenv from "dotenv";
import { PiAgentRunner } from "./agent.js";
import { AgentEvent, AgentRunRequest } from "./types.js";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 4001;

app.use(cors());
app.use(express.json());

// Health endpoint
app.get("/health", (req: Request, res: Response) => {
  res.json({
    status: "healthy",
    service: "pi-bridge",
    pi_agent_version: "0.74.2",
    pinned_reason: "Pinned to exact Phase 0.5 tested version for architectural stability",
    timestamp: new Date().toISOString(),
  });
});

// SSE Streaming Run Endpoint
app.post("/internal/agent/run", async (req: Request, res: Response) => {
  const body: AgentRunRequest = req.body;
  const sessionId = body.session_id || `sess_${Date.now()}`;
  const prompt = body.prompt;
  const model = body.model || "llama3.1:8b";

  if (!prompt) {
    res.status(400).json({ error: "Missing required field 'prompt'" });
    return;
  }

  // Setup Server-Sent Events headers
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders();

  const runner = new PiAgentRunner({
    sessionId,
    prompt,
    conversationHistory: body.conversation_history || [],
    model,
    provider: body.provider || "ollama",
    apiBaseUrl: process.env.API_BASE_URL || "http://127.0.0.1:8000",
    ollamaBaseUrl: process.env.OLLAMA_BASE_URL || "http://127.0.0.1:11434",
  });

  runner.on("event", (event: AgentEvent) => {
    res.write(`data: ${JSON.stringify(event)}\n\n`);
    if (event.type === "agent_completed" || event.type === "agent_error") {
      res.end();
    }
  });

  // Handle client disconnect gracefully
  req.on("close", () => {
    runner.removeAllListeners();
  });

  try {
    await runner.run(prompt);
  } catch (err: any) {
    const errorEvent: AgentEvent = {
      event_id: `evt_${Date.now()}_err`,
      session_id: sessionId,
      timestamp: new Date().toISOString(),
      type: "agent_error",
      error_code: "INTERNAL_SERVER_ERROR",
      message: err.message || "Unhandled bridge execution error",
      recoverable: false,
    };
    res.write(`data: ${JSON.stringify(errorEvent)}\n\n`);
    res.end();
  }
});

app.listen(Number(PORT), "0.0.0.0", () => {
  console.log(`[Pi Bridge] Microservice running on http://0.0.0.0:${PORT}`);
  console.log(`[Pi Bridge] Agent SDK Version: 0.74.2 (Pinned)`);
});
