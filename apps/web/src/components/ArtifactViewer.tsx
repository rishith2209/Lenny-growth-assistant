import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Artifact } from '../types';
import {
  FileCode,
  Eye,
  Copy,
  Check,
  Download,
  X,
} from 'lucide-react';

interface ArtifactViewerProps {
  artifact: Artifact | null;
  onClose: () => void;
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({
  artifact,
  onClose,
}) => {
  const [viewMode, setViewMode] = useState<'preview' | 'markdown'>('preview');
  const [copied, setCopied] = useState(false);

  if (!artifact) return null;

  const handleCopyMarkdown = () => {
    navigator.clipboard.writeText(artifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadHtml = () => {
    const blob = new Blob([artifact.rendered_html || ''], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${artifact.title.replace(/\s+/g, '_').toLowerCase()}.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const isTargetWordCount =
    artifact.word_count >= 1000 && artifact.word_count <= 1500;

  return (
    <aside className="artifact-pane">
      <div className="artifact-header">
        <div className="artifact-title-group">
          <div className="artifact-title">{artifact.title}</div>
          <div className="artifact-subtitle">
            <span>{artifact.metadata?.framework || 'Ship 30 for 30'}</span>
            <span
              className="word-count-badge"
              style={{
                backgroundColor: isTargetWordCount
                  ? 'var(--emerald-subtle)'
                  : 'rgba(245, 158, 11, 0.15)',
                color: isTargetWordCount
                  ? 'var(--emerald-success)'
                  : 'var(--amber-warning)',
              }}
            >
              {artifact.word_count} words (~1,250 target)
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div className="view-mode-tabs">
            <button
              className={`tab-btn ${viewMode === 'preview' ? 'active' : ''}`}
              onClick={() => setViewMode('preview')}
              title="Isolated HTML/CSS Sandboxed Card"
            >
              <Eye size={12} style={{ marginRight: '4px' }} />
              Preview
            </button>
            <button
              className={`tab-btn ${viewMode === 'markdown' ? 'active' : ''}`}
              onClick={() => setViewMode('markdown')}
              title="Raw Markdown Content"
            >
              <FileCode size={12} style={{ marginRight: '4px' }} />
              Markdown
            </button>
          </div>

          <button
            className="action-pill-btn"
            onClick={handleCopyMarkdown}
            title="Copy Markdown to Clipboard"
          >
            {copied ? <Check size={13} style={{ color: 'var(--emerald-success)' }} /> : <Copy size={13} />}
          </button>

          <button
            className="action-pill-btn"
            onClick={handleDownloadHtml}
            title="Download Standalone HTML"
          >
            <Download size={13} />
          </button>

          <button
            className="session-delete-btn"
            style={{ opacity: 1 }}
            onClick={onClose}
            title="Close Artifact Viewer"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      <div className="artifact-content-container">
        {viewMode === 'preview' ? (
          <iframe
            title={artifact.title}
            src={`/api/v1/artifacts/${artifact.id}/raw`}
            className="artifact-iframe"
            sandbox="allow-scripts"
          />
        ) : (
          <div className="markdown-artifact-view markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {artifact.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </aside>
  );
};
