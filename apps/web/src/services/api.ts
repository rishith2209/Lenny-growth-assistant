import { Session, Artifact, HealthStatus, AgentEvent } from '../types';

const API_BASE = '';

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchSessions(): Promise<Session[]> {
  const res = await fetch(`${API_BASE}/api/v1/sessions`);
  if (!res.ok) throw new Error('Failed to fetch sessions');
  const data = await res.json();
  return data.sessions || [];
}

export async function createSession(title?: string): Promise<Session> {
  const res = await fetch(`${API_BASE}/api/v1/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: title || 'New Growth Strategy' }),
  });
  if (!res.ok) throw new Error('Failed to create session');
  return res.json();
}

export async function fetchSession(sessionId: string): Promise<Session> {
  const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}`);
  if (!res.ok) throw new Error(`Failed to fetch session ${sessionId}`);
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error(`Failed to delete session ${sessionId}`);
}

export async function fetchArtifacts(sessionId?: string): Promise<Artifact[]> {
  const url = sessionId
    ? `${API_BASE}/api/v1/artifacts/session/${sessionId}`
    : `${API_BASE}/api/v1/artifacts`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch artifacts');
  const data = await res.json();
  return data.artifacts || [];
}

export async function fetchArtifact(artifactId: string): Promise<Artifact> {
  const res = await fetch(`${API_BASE}/api/v1/artifacts/${artifactId}`);
  if (!res.ok) throw new Error('Failed to fetch artifact');
  return res.json();
}

export interface StreamChatParams {
  sessionId: string;
  message: string;
  model: string;
  provider: string;
  onEvent: (event: AgentEvent) => void;
  onDelta: (delta: string) => void;
  onError: (error: Error) => void;
  onComplete: (accumulatedText: string) => void;
}

export async function streamChat({
  sessionId,
  message,
  model,
  provider,
  onEvent,
  onDelta,
  onError,
  onComplete,
}: StreamChatParams): Promise<() => void> {
  const controller = new AbortController();
  let accumulatedText = '';

  try {
    const response = await fetch(`${API_BASE}/api/v1/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message,
        model,
        provider,
      }),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('ReadableStream not supported by browser');
    }

    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    const readLoop = async () => {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('data: ')) {
              try {
                const event: AgentEvent = JSON.parse(trimmed.slice(6));
                onEvent(event);

                if (event.type === 'text_delta' && event.delta) {
                  accumulatedText += event.delta;
                  onDelta(event.delta);
                } else if (event.type === 'agent_completed') {
                  onComplete(accumulatedText);
                } else if (event.type === 'agent_error') {
                  onError(new Error(event.error || 'Agent execution error'));
                }
              } catch (e) {
                console.warn('Failed to parse SSE line:', trimmed, e);
              }
            }
          }
        }
        onComplete(accumulatedText);
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          onError(err);
        }
      }
    };

    readLoop();
  } catch (err: any) {
    if (err.name !== 'AbortError') {
      onError(err);
    }
  }

  return () => {
    controller.abort();
  };
}
