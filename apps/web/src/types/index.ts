export interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
  messages?: Message[];
}

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  created_at: string;
  provider?: string;
  model?: string;
  latency_ms?: number;
  metadata?: {
    status?: string;
    events?: AgentEvent[];
    citations?: Citation[];
    artifacts?: string[];
    guardrail_triggered?: boolean;
    reason?: string;
  };
}

export interface Citation {
  chunk_id: string;
  episode_id: string;
  episode_title: string;
  guest?: string | null;
  speaker?: string;
  timestamp_formatted?: string | null;
  start_time_seconds?: number | null;
  end_time_seconds?: number | null;
  youtube_url?: string | null;
  content: string;
  semantic_score?: number;
  lexical_score?: number;
  rrf_score?: number;
}

export interface Artifact {
  id: string;
  session_id: string;
  message_id?: string | null;
  artifact_type: 'essay' | 'framework' | 'memo' | 'table';
  title: string;
  content: string;
  rendered_html?: string | null;
  word_count: number;
  metadata: {
    framework?: string;
    guest?: string;
    citations?: string[];
    validation?: {
      is_valid: boolean;
      has_hook: boolean;
      has_core_idea: boolean;
      has_subheadings: boolean;
      citation_count: number;
      warnings: string[];
    };
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
}

export interface AgentEvent {
  event_id: string;
  session_id: string;
  timestamp?: string;
  type:
    | 'agent_started'
    | 'tool_started'
    | 'tool_result'
    | 'text_delta'
    | 'artifact_created'
    | 'agent_completed'
    | 'agent_error';
  model?: string;
  provider?: string;
  delta?: string;
  tool_call_id?: string;
  tool_name?: string;
  arguments?: Record<string, any>;
  result?: {
    query: string;
    total_results: number;
    confidence_score: number;
    confidence_tier: string;
    results: Citation[];
    execution_time_ms: number;
  };
  artifact_id?: string;
  artifact_type?: string;
  title?: string;
  word_count?: number;
  latency_ms?: number;
  cost_inr?: number;
  error?: string;
}

export interface HealthStatus {
  status: string;
  environment: string;
  database: {
    status: string;
    connected: boolean;
    pgvector_installed: boolean;
  };
  providers: {
    primary_provider: string;
    providers: Record<
      string,
      {
        provider: string;
        status: string;
        models_available: string[];
        embedding_model_available: boolean;
        details?: Record<string, any>;
      }
    >;
  };
  cost_profile: string;
}
