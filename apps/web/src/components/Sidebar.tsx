import React from 'react';
import { Session, HealthStatus } from '../types';
import { Plus, MessageSquare, Trash2, Database } from 'lucide-react';

interface SidebarProps {
  sessions: Session[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onDeleteSession: (id: string, e: React.MouseEvent) => void;
  selectedModel: string;
  onSelectModel: (model: string) => void;
  health: HealthStatus | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  selectedModel,
  onSelectModel,
  health,
}) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand-icon">
          <Database size={20} />
        </div>
        <div>
          <div className="brand-title">Lenny Assistant</div>
          <div className="brand-subtitle">Growth Knowledge Agent</div>
        </div>
      </div>

      <button className="new-chat-btn" onClick={onNewSession}>
        <Plus size={16} />
        <span>New Conversation</span>
      </button>

      <div className="sidebar-section-title">Conversations ({sessions.length})</div>

      <div className="session-list">
        {sessions.map((session) => (
          <button
            key={session.id}
            className={`session-item ${session.id === activeSessionId ? 'active' : ''}`}
            onClick={() => onSelectSession(session.id)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <MessageSquare size={14} style={{ flexShrink: 0, opacity: 0.7 }} />
              <span className="session-title-text">{session.title || 'Untitled Chat'}</span>
            </div>
            <button
              className="session-delete-btn"
              title="Delete session"
              onClick={(e) => onDeleteSession(session.id, e)}
            >
              <Trash2 size={13} />
            </button>
          </button>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="model-selector">
          <div className="selector-label">
            <span>LLM Model</span>
            <span style={{ color: 'var(--accent-light)', textTransform: 'none' }}>Ollama Local</span>
          </div>
          <select
            className="custom-select"
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
          >
            <option value="llama3.1:8b">llama3.1:8b (Primary)</option>
            <option value="qwen3:4b">qwen3:4b (Fast Lightweight)</option>
            <option value="qwen3:8b">qwen3:8b (Analytical)</option>
          </select>
        </div>

        <div className="status-badge-row">
          <div className="status-indicator">
            <div className="status-dot" />
            <span>{health?.database.connected ? 'pgvector Active' : 'Connecting...'}</span>
          </div>
          <div className="cost-free-pill">₹0 Spend</div>
        </div>
      </div>
    </aside>
  );
};
