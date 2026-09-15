import React from 'react';
import { Session, Artifact } from '../types';
import { FileText, Layers, ShieldCheck, Sparkles } from 'lucide-react';

interface HeaderProps {
  activeSession: Session | null;
  selectedModel: string;
  artifacts: Artifact[];
  showArtifactViewer: boolean;
  onToggleArtifactViewer: () => void;
  showProvenance: boolean;
  onToggleProvenance: () => void;
  provenanceCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  activeSession,
  selectedModel,
  artifacts,
  showArtifactViewer,
  onToggleArtifactViewer,
  showProvenance,
  onToggleProvenance,
  provenanceCount,
}) => {
  return (
    <header className="top-header">
      <div className="header-left">
        <div className="header-session-title">
          {activeSession?.title || 'Lenny Growth Assistant'}
        </div>
        <div className="header-meta-chip">
          <Sparkles size={12} style={{ color: 'var(--accent-light)' }} />
          <span>{selectedModel}</span>
        </div>
        <div className="header-meta-chip">
          <ShieldCheck size={12} style={{ color: 'var(--emerald-success)' }} />
          <span>Grounded RAG</span>
        </div>
      </div>

      <div className="header-actions">
        {artifacts.length > 0 && (
          <button
            className={`toggle-btn ${showArtifactViewer ? 'active' : ''}`}
            onClick={onToggleArtifactViewer}
          >
            <FileText size={14} />
            <span>Artifacts ({artifacts.length})</span>
          </button>
        )}

        {provenanceCount > 0 && (
          <button
            className={`toggle-btn ${showProvenance ? 'active' : ''}`}
            onClick={onToggleProvenance}
          >
            <Layers size={14} />
            <span>Evidence ({provenanceCount})</span>
          </button>
        )}
      </div>
    </header>
  );
};
