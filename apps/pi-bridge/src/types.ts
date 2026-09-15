export type AgentEventType =
  | "agent_started"
  | "text_delta"
  | "tool_started"
  | "tool_result"
  | "artifact_created"
  | "agent_completed"
  | "agent_error";

export interface BaseAgentEvent {
  event_id: string;
  session_id: string;
  timestamp: string;
  type: AgentEventType;
}

export interface AgentStartEvent extends BaseAgentEvent {
  type: "agent_started";
  model: string;
  provider: string;
}

export interface TextDeltaEvent extends BaseAgentEvent {
  type: "text_delta";
  delta: string;
}

export interface ToolStartedEvent extends BaseAgentEvent {
  type: "tool_started";
  tool_call_id: string;
  tool_name: string;
  arguments: Record<string, any>;
}

export interface ToolResultEvent extends BaseAgentEvent {
  type: "tool_result";
  tool_call_id: string;
  tool_name: string;
  result: Record<string, any>;
  is_error?: boolean;
}

export interface ArtifactCreatedEvent extends BaseAgentEvent {
  type: "artifact_created";
  artifact_id: string;
  artifact_type: string;
  title: string;
  word_count: number;
  metadata: Record<string, any>;
}

export interface AgentCompletedEvent extends BaseAgentEvent {
  type: "agent_completed";
  total_tokens?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
  latency_ms: number;
  cost_inr: number;
}

export interface AgentErrorEvent extends BaseAgentEvent {
  type: "agent_error";
  error_code: string;
  message: string;
  recoverable: boolean;
}

export type AgentEvent =
  | AgentStartEvent
  | TextDeltaEvent
  | ToolStartedEvent
  | ToolResultEvent
  | ArtifactCreatedEvent
  | AgentCompletedEvent
  | AgentErrorEvent;

export interface ChatMessage {
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  name?: string;
  metadata?: Record<string, any>;
}

export interface AgentRunRequest {
  session_id: string;
  prompt: string;
  conversation_history?: ChatMessage[];
  model?: string;
  provider?: string;
  temperature?: number;
}
