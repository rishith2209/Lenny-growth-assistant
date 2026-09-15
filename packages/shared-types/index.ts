/**
 * Shared Type Definitions for Lenny Growth Assistant
 */

export interface ProvenanceCitation {
  chunk_id: string;
  episode_id: string;
  episode_title: string;
  guest: string | null;
  start_time_seconds: number | null;
  end_time_seconds: number | null;
  timestamp_formatted: string | null;
  youtube_url: string | null;
  source_commit: string;
  speaker: string | null;
}

export interface RetrievedChunk {
  chunk_id: string;
  episode_id: string;
  episode_title: string;
  guest: string | null;
  content: string;
  speaker: string | null;
  start_time_seconds: number | null;
  end_time_seconds: number | null;
  timestamp_formatted: string | null;
  provenance: ProvenanceCitation;
  semantic_score: number;
  lexical_score: number;
  rrf_score: number;
}

export interface KnowledgeSearchFilters {
  episode_id?: string;
  guest?: string;
  speaker?: string;
  date_from?: string;
  date_to?: string;
}

export interface KnowledgeSearchRequest {
  query: string;
  top_k?: number;
  filters?: KnowledgeSearchFilters;
}

export interface KnowledgeSearchResponse {
  query: string;
  total_results: number;
  confidence_score: number;
  confidence_tier: 'high' | 'medium' | 'low' | 'unsupported';
  results: RetrievedChunk[];
  execution_time_ms: number;
}

// ----------------------------------------------------------------------
// Pi Bridge Event Stream Contracts (SSE)
// ----------------------------------------------------------------------

export type AgentEventType =
  | 'agent_started'
  | 'text_delta'
  | 'tool_started'
  | 'tool_result'
  | 'agent_completed'
  | 'agent_error';

export interface BaseAgentEvent {
  event_id: string;
  session_id: string;
  timestamp: string;
  type: AgentEventType;
}

export interface AgentStartEvent extends BaseAgentEvent {
  type: 'agent_started';
  model: string;
  provider: string;
}

export interface TextDeltaEvent extends BaseAgentEvent {
  type: 'text_delta';
  delta: string;
}

export interface ToolStartedEvent extends BaseAgentEvent {
  type: 'tool_started';
  tool_call_id: string;
  tool_name: string;
  arguments: Record<string, any>;
}

export interface ToolResultEvent extends BaseAgentEvent {
  type: 'tool_result';
  tool_call_id: string;
  tool_name: string;
  result: Record<string, any>;
  is_error?: boolean;
}

export interface AgentCompletedEvent extends BaseAgentEvent {
  type: 'agent_completed';
  total_tokens?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
  latency_ms: number;
  cost_inr: number;
}

export interface AgentErrorEvent extends BaseAgentEvent {
  type: 'agent_error';
  error_code: string;
  message: string;
  recoverable: boolean;
}

export type AgentEvent =
  | AgentStartEvent
  | TextDeltaEvent
  | ToolStartedEvent
  | ToolResultEvent
  | AgentCompletedEvent
  | AgentErrorEvent;

// ----------------------------------------------------------------------
// Session & Message Contracts
// ----------------------------------------------------------------------

export interface SessionRecord {
  id: string;
  title: string | null;
  user_metadata: Record<string, any>;
  provider: string;
  model: string;
  status: 'active' | 'archived' | 'error';
  created_at: string;
  updated_at: string;
}

export interface MessageRecord {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  metadata: Record<string, any>;
  provider: string | null;
  model: string | null;
  latency_ms: number | null;
  token_count: number | null;
  cost_inr: number;
  created_at: string;
}
