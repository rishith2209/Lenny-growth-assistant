import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Message, AgentEvent, Citation } from '../types';
import {
  Send,
  Sparkles,
  BookOpen,
  CheckCircle2,
  FileCode,
  Zap,
} from 'lucide-react';

interface ChatViewProps {
  messages: Message[];
  isStreaming: boolean;
  streamingText: string;
  activeEvents: AgentEvent[];
  onSendMessage: (text: string) => void;
  onSelectCitation: (citation: Citation) => void;
  onGenerateShip30: () => void;
}

const STARTER_PROMPTS = [
  {
    title: "Adam Fishman's Competency Model",
    subtitle: 'What are the 4 buckets of growth competencies?',
    prompt: 'What advice does Adam Fishman give regarding growth teams and competency models?',
  },
  {
    title: 'Figma Product-Led Growth',
    subtitle: 'How did Figma build viral designer loops?',
    prompt: 'How did Figma drive early bottom-up adoption and viral designer growth loops?',
  },
  {
    title: 'Hiring a Head of Growth',
    subtitle: 'What fatal mistakes do founders make when hiring?',
    prompt: 'What are the biggest mistakes founders make when evaluating and hiring a Head of Growth?',
  },
  {
    title: 'Ship 30 for 30 Essay',
    subtitle: 'Generate a 1,250-word atomic essay with citations',
    prompt: 'Turn Adam Fishman\'s growth leadership and competency framework into a masterclass Ship 30 for 30 Long-Form Atomic Essay (approx 1,250 words) with exact transcript citations, bold rules, and actionable pillars. Save it as an artifact.',
  },
];

export const ChatView: React.FC<ChatViewProps> = ({
  messages,
  isStreaming,
  streamingText,
  activeEvents,
  onSendMessage,
  onSelectCitation,
  onGenerateShip30,
}) => {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingText, activeEvents]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputText.trim() || isStreaming) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Find active tool running during streaming
  const activeTool = activeEvents.find((e) => e.type === 'tool_started');
  const activeToolResult = activeEvents.find((e) => e.type === 'tool_result');

  return (
    <div className="chat-pane">
      <div className="messages-container">
        {messages.length === 0 && !isStreaming ? (
          <div className="welcome-container">
            <div className="welcome-badge">
              <Sparkles size={13} />
              <span>Grounded Growth Intelligence</span>
            </div>
            <h1 className="welcome-title">
              What growth challenge are you <span>solving today?</span>
            </h1>
            <p className="welcome-desc">
              Ask any tactical question about product-led growth, retention loops, or hiring.
              Every insight is synthesized and verified directly from Lenny's Podcast transcripts.
            </p>

            <div className="starter-grid">
              {STARTER_PROMPTS.map((item, idx) => (
                <div
                  key={idx}
                  className="starter-card"
                  onClick={() => onSendMessage(item.prompt)}
                >
                  <div className="starter-card-title">
                    <Zap size={14} style={{ color: 'var(--accent-light)' }} />
                    <span>{item.title}</span>
                  </div>
                  <div className="starter-card-subtitle">{item.subtitle}</div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <div key={msg.id} className={`message-row ${msg.role}`}>
                <div className={`avatar ${msg.role}`}>
                  {msg.role === 'assistant' ? 'L' : 'U'}
                </div>
                <div className="message-body">
                  <div className="message-bubble">
                    <div className="markdown-body">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>

                    {/* Citations block */}
                    {msg.metadata?.citations && msg.metadata.citations.length > 0 && (
                      <div className="citation-chip-group">
                        {msg.metadata.citations.map((cite, i) => (
                          <div
                            key={i}
                            className="citation-chip"
                            onClick={() => onSelectCitation(cite)}
                            title="Click to view raw transcript quote in Evidence Drawer"
                          >
                            <BookOpen size={11} style={{ color: 'var(--accent-light)' }} />
                            <span>
                              {cite.speaker || cite.guest || cite.episode_title}
                              {cite.timestamp_formatted ? ` (${cite.timestamp_formatted})` : ''}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {msg.role === 'assistant' && (
                    <div className="message-action-bar">
                      <button
                        className="action-pill-btn ship30-btn"
                        onClick={onGenerateShip30}
                        title="Convert this synthesis into a ~1,250-word Cole & Bush Ship 30 for 30 atomic essay"
                      >
                        <FileCode size={12} />
                        <span>Turn into Ship 30 Essay</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Live Streaming State */}
            {isStreaming && (
              <div className="message-row assistant">
                <div className="avatar assistant">L</div>
                <div className="message-body">
                  {/* Tool execution badge */}
                  {activeTool && (
                    <div className="agent-step-badge">
                      <div className="step-spinner" />
                      <span>
                        Executing <code>{activeTool.tool_name}</code>
                        {activeTool.arguments?.guest
                          ? ` (Guest: ${activeTool.arguments.guest})`
                          : ''}
                      </span>
                    </div>
                  )}

                  {activeToolResult && (
                    <div className="agent-step-badge" style={{ borderColor: 'rgba(16, 185, 129, 0.4)', color: 'var(--emerald-success)' }}>
                      <CheckCircle2 size={13} />
                      <span>
                        Retrieved {activeToolResult.result?.total_results || 0} transcript chunks in {activeToolResult.result?.execution_time_ms || 0}ms
                      </span>
                    </div>
                  )}

                  {streamingText && (
                    <div className="message-bubble">
                      <div className="markdown-body">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {streamingText}
                        </ReactMarkdown>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-floating-bar">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          rows={1}
          placeholder="Ask a tactical growth question or request a Ship 30 for 30 essay..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isStreaming}
        />
        <div className="input-controls">
          <div className="input-hint">
            <span>Press Enter to send, Shift+Enter for new line</span>
          </div>
          <button
            className="send-btn"
            onClick={() => handleSubmit()}
            disabled={!inputText.trim() || isStreaming}
            title="Send Message"
          >
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  );
};
