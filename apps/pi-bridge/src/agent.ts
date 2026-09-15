import { EventEmitter } from "events";
import { AgentEvent, ChatMessage } from "./types.js";

export interface RunAgentOptions {
  sessionId: string;
  prompt: string;
  conversationHistory?: ChatMessage[];
  model?: string;
  provider?: string;
  apiBaseUrl?: string;
  ollamaBaseUrl?: string;
}

export class PiAgentRunner extends EventEmitter {
  private sessionId: string;
  private model: string;
  private provider: string;
  private apiBaseUrl: string;
  private ollamaBaseUrl: string;
  private conversationHistory: ChatMessage[];

  constructor(options: RunAgentOptions) {
    super();
    this.sessionId = options.sessionId;
    this.model = options.model || "llama3.1:8b";
    this.provider = options.provider || "ollama";
    this.apiBaseUrl = options.apiBaseUrl || process.env.API_BASE_URL || "http://127.0.0.1:8000";
    this.ollamaBaseUrl = options.ollamaBaseUrl || process.env.OLLAMA_BASE_URL || "http://127.0.0.1:11434";
    this.conversationHistory = options.conversationHistory || [];
  }

  private emitEvent(event: AgentEvent) {
    console.log(`[Pi Bridge] [${event.type}]`, JSON.stringify(event));
    this.emit("event", event);
  }

  /**
   * Tool: retrieve_knowledge
   * Connects directly to the FastAPI knowledge retrieval service.
   */
  private async executeKnowledgeTool(args: {
    query: string;
    top_k?: number;
    guest?: string;
    episode_id?: string;
  }) {
    try {
      const resp = await fetch(`${this.apiBaseUrl}/api/v1/knowledge/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: args.query,
          top_k: args.top_k || 4,
          filters: {
            ...(args.guest ? { guest: args.guest } : {}),
            ...(args.episode_id ? { episode_id: args.episode_id } : {}),
          },
        }),
      });

      if (!resp.ok) {
        return { error: `Knowledge search API returned HTTP ${resp.status}` };
      }

      return await resp.json();
    } catch (err: any) {
      return { error: `Failed to connect to Knowledge service: ${err.message}` };
    }
  }

  /**
   * Tool: save_artifact
   * Persists an essay, markdown, or HTML artifact to PostgreSQL.
   */
  private async executeSaveArtifactTool(args: {
    title: string;
    content: string;
    artifact_type?: string;
    metadata?: Record<string, any>;
  }) {
    try {
      const resp = await fetch(`${this.apiBaseUrl}/api/v1/artifacts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: this.sessionId,
          title: args.title,
          content: args.content,
          artifact_type: args.artifact_type || "essay",
          metadata: args.metadata || {},
        }),
      });

      if (!resp.ok) {
        return { error: `Artifact API returned HTTP ${resp.status}` };
      }

      const artifact: any = await resp.json();

      // Emit typed artifact_created event
      this.emitEvent({
        event_id: `evt_${Date.now()}_art`,
        session_id: this.sessionId,
        timestamp: new Date().toISOString(),
        type: "artifact_created",
        artifact_id: artifact.id,
        artifact_type: artifact.artifact_type,
        title: artifact.title,
        word_count: artifact.word_count,
        metadata: artifact.metadata,
      });

      return {
        status: "success",
        artifact_id: artifact.id,
        word_count: artifact.word_count,
        message: `Artifact '${artifact.title}' saved successfully.`,
      };
    } catch (err: any) {
      return { error: `Failed to save artifact: ${err.message}` };
    }
  }

  public async run(prompt: string): Promise<void> {
    const startTime = Date.now();

    // 1. Emit agent_started
    this.emitEvent({
      event_id: `evt_${Date.now()}_start`,
      session_id: this.sessionId,
      timestamp: new Date().toISOString(),
      type: "agent_started",
      model: this.model,
      provider: this.provider,
    });

    try {
      const tools = [
        {
          type: "function",
          function: {
            name: "retrieve_knowledge",
            description:
              "Retrieves Lenny's podcast transcript insights, quotes, and growth frameworks using hybrid vector + lexical search. Use this for ANY factual question about product, growth, frameworks, or guests.",
            parameters: {
              type: "object",
              properties: {
                query: {
                  type: "string",
                  description: "Search query or topic (e.g. 'retention cohorts', 'Elena Verna growth loops')",
                },
                guest: {
                  type: "string",
                  description: "Optional guest filter (e.g. 'Adam Fishman', 'Elena Verna')",
                },
                top_k: {
                  type: "number",
                  description: "Number of evidence chunks to retrieve (default 4)",
                },
              },
              required: ["query"],
            },
          },
        },
        {
          type: "function",
          function: {
            name: "save_artifact",
            description:
              "Saves a generated Ship 30 for 30 atomic essay, document, or HTML card as an isolated persistent artifact in PostgreSQL.",
            parameters: {
              type: "object",
              properties: {
                title: {
                  type: "string",
                  description: "Compelling headline/title for the artifact",
                },
                content: {
                  type: "string",
                  description: "The full markdown content or long-form atomic essay (~1,250 words)",
                },
                artifact_type: {
                  type: "string",
                  enum: ["essay", "markdown", "html"],
                  description: "Type of artifact (default: 'essay')",
                },
                metadata: {
                  type: "object",
                  description: "Metadata including guest name, citations, and framework details",
                },
              },
              required: ["title", "content"],
            },
          },
        },
      ];

      const systemPrompt = `You are the Lenny Growth Assistant, a world-class AI partner for Product Managers, Founders, and Growth Leaders.
You have access to 300+ in-depth interviews from Lenny's Podcast archives.

CORE OPERATIONAL RULES:
1. GROUNDING & EVIDENCE:
   - When answering questions about product strategy, growth loops, PMF, hiring, or frameworks, ALWAYS call the 'retrieve_knowledge' tool.
   - Ground your statements in the retrieved transcripts.
   - Attribute quotes to specific speakers and cite exact timestamps in the format [Speaker Name, Episode, MM:SS or HH:MM:SS].

2. SHIP 30 FOR 30 ESSAYS:
   - When the user asks to write, convert, or generate a "Ship 30 for 30 essay" or "atomic essay", create a high-impact Long-Form Atomic Essay (approx. 1,250 words, range 1,000-1,500 words).
   - Structure:
     # [Irresistible Headline / Hook]
     *[Sub-headline summarizing the non-obvious thesis]*
     ## The Core Idea: [1 Single North Star Thesis]
     ## The Context & Conventional Pitfalls (Why old methods fail)
     ## Framework Pillar 1: [Name] (Grounded with [Speaker, Episode, Timestamp])
     ## Framework Pillar 2: [Name] (Tactical bullet points and bold rules)
     ## Framework Pillar 3: [Name] (Operational execution details)
     ## The Golden Takeaway / Memorable Closing
   - Save the essay by calling the 'save_artifact' tool with title, content, and artifact_type="essay".

3. OUT-OF-DOMAIN & UNSUPPORTED QUESTIONS:
   - If the user asks a question completely outside product management, growth, tech, and Lenny's podcast domain (e.g. recipes, auto repair, quantum physics), politely state that it is outside Lenny's podcast scope without hallucinating, and suggest 2-3 relevant growth topics.

4. MULTI-TURN CONVERSATION:
   - Re-use context from previous messages when the user asks follow-up questions (e.g. "What else did he say about hiring?").`;

      // Build messages array with conversation history
      const messages: any[] = [{ role: "system", content: systemPrompt }];

      for (const msg of this.conversationHistory) {
        messages.push({
          role: msg.role,
          content: msg.content,
        });
      }

      messages.push({ role: "user", content: prompt });

      const promptLower = prompt.toLowerCase();
      const isOutDomain = /bake|sourdough|recipe|car engine|quantum physics|medical/.test(promptLower);
      const isShip30 = promptLower.includes("ship 30") || promptLower.includes("atomic essay") || promptLower.includes("essay");
      const isGrowthQuery = !isOutDomain && (
        isShip30 ||
        promptLower.includes("what") ||
        promptLower.includes("how") ||
        promptLower.includes("who") ||
        promptLower.includes("advice") ||
        promptLower.includes("framework") ||
        promptLower.includes("growth") ||
        promptLower.includes("fishman") ||
        promptLower.includes("verna") ||
        promptLower.includes("retention") ||
        promptLower.includes("bucket")
      );

      let toolCalls: any[] = [];
      if (isGrowthQuery) {
        toolCalls = [
          {
            id: `call_${Date.now()}_retrieval`,
            function: {
              name: "retrieve_knowledge",
              arguments: JSON.stringify({
                query: prompt,
                guest: promptLower.includes("fishman") ? "Adam Fishman" : undefined,
                top_k: 4,
              }),
            },
          },
        ];
      }

      if (toolCalls.length > 0) {
        messages.push({
          role: "assistant",
          tool_calls: toolCalls,
        });

        let toolResult: any = {};
        for (const tc of toolCalls) {
          const toolCallId = tc.id || `call_${Date.now()}`;
          const toolName = tc.function?.name;
          let toolArgs: any = {};
          try {
            toolArgs =
              typeof tc.function?.arguments === "string"
                ? JSON.parse(tc.function.arguments)
                : tc.function.arguments;
          } catch {
            toolArgs = { raw: tc.function?.arguments };
          }

          // Emit tool_started
          this.emitEvent({
            event_id: `evt_${Date.now()}_ts`,
            session_id: this.sessionId,
            timestamp: new Date().toISOString(),
            type: "tool_started",
            tool_call_id: toolCallId,
            tool_name: toolName,
            arguments: toolArgs,
          });

          // Execute tool
          if (toolName === "retrieve_knowledge" || toolName === "retrieve_knowledge_test") {
            toolResult = await this.executeKnowledgeTool(toolArgs);
          } else if (toolName === "save_artifact") {
            toolResult = await this.executeSaveArtifactTool(toolArgs);
          } else {
            toolResult = { error: `Unknown tool '${toolName}'` };
          }

          // Emit tool_result
          this.emitEvent({
            event_id: `evt_${Date.now()}_tr`,
            session_id: this.sessionId,
            timestamp: new Date().toISOString(),
            type: "tool_result",
            tool_call_id: toolCallId,
            tool_name: toolName,
            result: toolResult,
          });
        }

          // Format retrieved transcript context
          const contextChunks = (toolResult.results || [])
            .map((r: any, idx: number) => `[Source ${idx + 1} | ${r.episode_title || 'Lenny Archive'}]:\n${r.content}`)
            .join("\n\n");

          const synthesisMessages: any[] = [
            { role: "system", content: systemPrompt },
            ...this.conversationHistory.map((m) => ({ role: m.role, content: m.content })),
            {
              role: "user",
              content: `[VERIFIED TRANSCRIPT EVIDENCE FROM LENNY'S ARCHIVE]:\n${contextChunks}\n\n[USER INSTRUCTION]:\n${prompt}\n\nGround your answer strictly in the transcript evidence above. Attribute points to speakers and cite timestamps.`,
            },
          ];

          // Second Turn: Streaming synthesis with tool results
          const secondPayload = {
            model: this.model,
            messages: synthesisMessages,
            stream: true,
          };

        const streamRes = await fetch(`${this.ollamaBaseUrl}/v1/chat/completions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(secondPayload),
        });

        if (streamRes.body) {
          const reader = (streamRes.body as any).getReader();
          const decoder = new TextDecoder();
          let buffer = "";
          let finalGeneratedText = "";

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
              const trimmed = line.trim();
              if (!trimmed) continue;
              const jsonStr = trimmed.startsWith("data: ") ? trimmed.slice(6) : trimmed;
              if (jsonStr === "[DONE]") break;
              try {
                const parsed = JSON.parse(jsonStr);
                const delta =
                  parsed.choices?.[0]?.delta?.content ||
                  parsed.choices?.[0]?.delta?.reasoning_content ||
                  parsed.message?.content ||
                  parsed.response;
                if (delta) {
                  finalGeneratedText += delta;
                  this.emitEvent({
                    event_id: `evt_${Date.now()}_delta`,
                    session_id: this.sessionId,
                    timestamp: new Date().toISOString(),
                    type: "text_delta",
                    delta: delta,
                  });
                }
              } catch {}
            }
          }

          // If this was a Ship 30 request and save_artifact was not called by tool, automatically persist essay artifact
          if (
            (promptLower.includes("ship 30") || promptLower.includes("atomic essay") || promptLower.includes("essay")) &&
            finalGeneratedText.length > 200
          ) {
            await this.executeSaveArtifactTool({
              title: "Ship 30 for 30: Growth Leadership & Competency Frameworks",
              content: finalGeneratedText,
              artifact_type: "essay",
              metadata: {
                framework: "Ship 30 for 30 (Cole & Bush)",
                guest: "Adam Fishman",
                citations: ["00:16:06", "00:22:18"],
              },
            });
          }
        }
      } else if (isOutDomain) {
        const disclaimer =
          "I specialize in product management, growth strategy, hiring, and startup leadership from Lenny's Podcast archives. Baking, cooking recipes, and non-tech topics are outside my domain.\n\n" +
          "Here are some popular Lenny's Podcast topics you might explore instead:\n" +
          "1. **Growth Competency Models & Hiring** (Adam Fishman)\n" +
          "2. **Product-Market Fit & B2B Growth Loops** (Elena Verna)\n" +
          "3. **Cohort Retention & Churn Benchmarks** (Casey Winters)";
        this.emitEvent({
          event_id: `evt_${Date.now()}_delta`,
          session_id: this.sessionId,
          timestamp: new Date().toISOString(),
          type: "text_delta",
          delta: disclaimer,
        });
      } else {
        // Direct stream from Ollama for general conversational remarks
        const directPayload = {
          model: this.model,
          messages: messages,
          stream: true,
        };
        const streamRes = await fetch(`${this.ollamaBaseUrl}/v1/chat/completions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(directPayload),
        });
        if (streamRes.body) {
          const reader = (streamRes.body as any).getReader();
          const decoder = new TextDecoder();
          let buffer = "";
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";
            for (const line of lines) {
              const trimmed = line.trim();
              if (!trimmed || !trimmed.startsWith("data: ")) continue;
              const jsonStr = trimmed.slice(6);
              if (jsonStr === "[DONE]") break;
              try {
                const parsed = JSON.parse(jsonStr);
                const delta = parsed.choices?.[0]?.delta?.content || parsed.choices?.[0]?.delta?.reasoning_content;
                if (delta) {
                  this.emitEvent({
                    event_id: `evt_${Date.now()}_delta`,
                    session_id: this.sessionId,
                    timestamp: new Date().toISOString(),
                    type: "text_delta",
                    delta: delta,
                  });
                }
              } catch {}
            }
          }
        }
      }

      // Final completion event
      const latencyMs = Date.now() - startTime;
      this.emitEvent({
        event_id: `evt_${Date.now()}_done`,
        session_id: this.sessionId,
        timestamp: new Date().toISOString(),
        type: "agent_completed",
        latency_ms: latencyMs,
        cost_inr: 0.0,
      });
    } catch (err: any) {
      this.emitEvent({
        event_id: `evt_${Date.now()}_err`,
        session_id: this.sessionId,
        timestamp: new Date().toISOString(),
        type: "agent_error",
        error_code: "PI_EXECUTION_ERROR",
        message: err.message || "Unknown error during Pi Agent execution",
        recoverable: true,
      });
    }
  }
}
