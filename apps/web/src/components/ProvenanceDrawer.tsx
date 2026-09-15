import React from 'react';
import { Citation } from '../types';
import { Layers, X, Clock } from 'lucide-react';

interface ProvenanceDrawerProps {
  citations: Citation[];
  selectedCitation: Citation | null;
  onClose: () => void;
}

export const ProvenanceDrawer: React.FC<ProvenanceDrawerProps> = ({
  citations,
  selectedCitation,
  onClose,
}) => {
  return (
    <aside className="provenance-drawer">
      <div className="provenance-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={16} style={{ color: 'var(--accent-light)' }} />
          <span style={{ fontSize: '14px', fontWeight: 700, color: '#fff' }}>
            Transcript Evidence ({citations.length})
          </span>
        </div>
        <button
          className="session-delete-btn"
          style={{ opacity: 1 }}
          onClick={onClose}
          title="Close Drawer"
        >
          <X size={16} />
        </button>
      </div>

      <div className="provenance-list">
        {citations.map((cite, idx) => {
          const isSelected = selectedCitation?.chunk_id === cite.chunk_id;
          return (
            <div
              key={idx}
              className="provenance-card"
              style={{
                borderColor: isSelected ? 'var(--accent-primary)' : 'var(--border-subtle)',
                backgroundColor: isSelected ? 'var(--bg-surface-active)' : 'var(--bg-input)',
              }}
            >
              <div className="provenance-card-header">
                <span className="episode-pill">
                  {cite.guest || cite.episode_title}
                </span>
                {cite.timestamp_formatted && (
                  <span className="timestamp-pill">
                    <Clock size={10} style={{ display: 'inline', marginRight: '3px' }} />
                    {cite.timestamp_formatted}
                  </span>
                )}
              </div>

              <div className="quote-box">"{cite.content}"</div>

              <div className="scores-row">
                {cite.speaker && <span>Speaker: {cite.speaker}</span>}
                {cite.semantic_score !== undefined && (
                  <span>Cosine: {(cite.semantic_score * 100).toFixed(1)}%</span>
                )}
                {cite.rrf_score !== undefined && (
                  <span>RRF: {cite.rrf_score.toFixed(4)}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
};
